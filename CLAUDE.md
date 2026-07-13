# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

This directory holds two unrelated exercises:

- **`uigen/`** — a Next.js app: an AI-powered React component generator with live preview. This is the primary codebase; almost all work happens here.
- **`models/`, `setup_docker_db.py`, `.claude/commands/run_pipeline.md`** — a small standalone data-pipeline exercise (Dockerized Postgres + a SQL transformation model), unrelated to `uigen`. `setup_docker_db.py` loads mock rows into a `raw_transactions` table in a local Postgres instance (`postgresql://postgres:mysecretpassword@localhost:5432/simulation_db`); `models/stg_transactions.sql` is a dedup/cleanup transform over that table. The `/run_pipeline` custom command (`.claude/commands/run_pipeline.md`) orchestrates running a SQL model file against that DB and asserting data-quality invariants (no dupes, no negative amounts, no null `user_id`).

Everything below describes `uigen/`. Run all `uigen` commands from inside `uigen/`, not the repo root.

## Commands (run from `uigen/`)

```bash
npm run setup       # install deps + prisma generate + prisma migrate dev (first-time setup)
npm run dev          # start dev server (Next.js + Turbopack) on :3000
npm run dev:daemon   # start dev server in background, logs to logs.txt (prefer this for Claude Code so the shell isn't blocked)
npm run build        # production build
npm run lint         # next lint
npm test             # run vitest test suite
npm run db:reset      # reset the local SQLite db (prisma migrate reset --force)
```

Run a single test file: `npx vitest run <path>` (e.g. `npx vitest run src/lib/transform/__tests__/jsx-transformer.test.ts`). Tests use `vitest` with `jsdom` environment and React Testing Library; test files live in `__tests__/` directories next to the code they cover.

**Never run `npm audit fix`** — dependency versions are intentionally pinned to a known-compatible set; `audit fix` can bump packages past compatible versions and break the app. If a security scanner flags something, update the specific pinned version deliberately instead.

No `ANTHROPIC_API_KEY` is required to run the app: without one (or with the placeholder value left in `.env`), `src/lib/provider.ts` falls back to a `MockLanguageModel` that returns canned tool calls/components instead of calling Claude, so the full generation flow is testable without live API access.

## Architecture

**Stack**: Next.js 15 (App Router), React 19, TypeScript, Tailwind v4, Prisma + SQLite, Vercel AI SDK (`ai` package) + `@ai-sdk/anthropic`.

### Virtual file system, not disk I/O

Generated components are never written to disk. `src/lib/file-system.ts` defines `VirtualFileSystem`, an in-memory tree of `FileNode`s (files/directories keyed by normalized path) that the AI model edits via tool calls. It supports create/view/rename/delete/str-replace and serializes to/from a plain object for persistence (stored as a JSON string in `Project.data` in the DB) and for passing across the client/server boundary in chat requests.

### AI tool-calling loop

`src/app/api/chat/route.ts` is the only LLM-facing endpoint. Per request it:
1. Rebuilds a `VirtualFileSystem` from the `files` payload the client sends (client owns file state; server is stateless per-request).
2. Calls `streamText` (Vercel AI SDK) with two tools bound to that filesystem instance: `str_replace_editor` (`src/lib/tools/str-replace.ts` — create/view/str_replace/insert/undo_edit, mirrors Anthropic's text-editor tool) and `file_manager` (`src/lib/tools/file-manager.ts` — rename/delete).
3. On finish, if a `projectId` was supplied and the request is authenticated, persists the updated message history and serialized filesystem to the `Project` row.

`maxSteps` is capped lower for the mock provider (4) than for real Claude (40) to avoid the mock repeating itself.

### Live preview

`src/lib/transform/jsx-transformer.ts` + `@babel/standalone` transpile the virtual filesystem's JSX/TSX in-browser so `src/components/preview/PreviewFrame.tsx` can render generated components live without a build step, driven by whatever is currently in the `VirtualFileSystem`.

### State: contexts over prop drilling

`src/lib/contexts/chat-context.tsx` and `src/lib/contexts/file-system-context.tsx` hold chat messages and the virtual filesystem respectively, and are the source of truth `ChatInterface`, `FileTree`, `CodeEditor`, and `PreviewFrame` all read from/write to.

### Auth & persistence

- `src/lib/auth.ts`: JWT-based sessions (via `jose`) in an httpOnly cookie, `JWT_SECRET` env-configurable (defaults to a dev-only secret — must be set in production).
- `src/lib/prisma.ts` + `prisma/schema.prisma`: SQLite via Prisma. `User` has many `Project`s; `Project.userId` is optional, `Project.messages` and `Project.data` are JSON-serialized strings (not relational), letting anonymous users use the tool with in-memory-only state.
- `src/lib/anon-work-tracker.ts`: tracks anonymous (unauthenticated) work client-side so it can be attributed/claimed if the user later signs up.
- Auth is enforced per-action (e.g. inside the `onFinish` save path in `api/chat/route.ts`, and in `src/actions/*`), not via Next.js middleware — there is no `middleware.ts`.

### Directory map

- `src/app/` — routes: `/` (home), `/[projectId]` (a saved project's chat+editor+preview), `/api/chat` (the streaming generation endpoint).
- `src/actions/` — server actions for project CRUD (`create-project.ts`, `get-project(s).ts`), re-exported from `index.ts`.
- `src/components/chat/`, `src/components/editor/`, `src/components/preview/`, `src/components/auth/` — feature UI; `src/components/ui/` — shared Radix-based primitives (shadcn-style).
- `src/lib/prompts/generation.tsx` — the system prompt sent to the model.
- `src/generated/prisma/` — Prisma client output (generated, not hand-edited).
