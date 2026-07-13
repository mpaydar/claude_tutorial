You are acting as an automated Data Engineering CI/CD Orchestrator for a Dockerized PostgreSQL environment.

Analyze the SQL transformation rules written in: $ARGUMENTS

1. Write and run a temporary Python script that connects to the Dockerized Postgres database using the connection string from the `DATABASE_URL` environment variable (`os.environ["DATABASE_URL"]`) — never hardcode credentials in the script. In CI this is injected from the `DATABASE_URL` GitHub Actions secret; locally it comes from your `.env`/shell environment.
2. Run the SQL data cleaning transformation query found inside the target file ($ARGUMENTS).
3. Run programmatic assertions on the resulting dataset to audit:
	* ZERO duplicate rows.
    	* ZERO negative numbers in the amount column.
    	* NO true NULL values in the user_id field.
4. Output a summary markdown table to the terminal displaying row profiles and Pass/Fail statuses.
	

