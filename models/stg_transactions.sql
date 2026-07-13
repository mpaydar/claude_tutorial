SELECT DISTINCT
    transaction_id,
    COALESCE(user_id, 'UNKNOWN') as user_id,
    ABS(amount) as amount
FROM raw_transactions;
