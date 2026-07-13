import psycopg2

DB_URI = "postgresql://postgres:mysecretpassword@localhost:5432/simulation_db"

try: 
	conn=psycopg2.connect(DB_URI)
	cursor=conn.cursor()
	cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_transactions (
            transaction_id VARCHAR(50),
            user_id VARCHAR(50),
            amount NUMERIC,
            created_at TIMESTAMP,
            status VARCHAR(50)
        )
    ''')

	cursor.execute('TRUNCATE TABLE raw_transactions')

	mock_data = [
        ('TXN_001', 'USR_99', 150.50, '2026-07-13 10:00:00', 'completed'),
        ('TXN_002', 'USR_88', -20.00, '2026-07-13 10:05:00', 'failed'),
        ('TXN_003', None, 45.00, '2026-07-13 10:10:00', 'completed'),
        ('TXN_001', 'USR_99', 150.50, '2026-07-13 10:00:00', 'completed')
    ]

	insert_query = "INSERT INTO raw_transactions VALUES (%s, %s, %s, %s, %s)"
	cursor.executemany(insert_query, mock_data)
	conn.commit()
	print("🐳 Successfully loaded the data artifact into your local Docker Postgres DB!")
except Exception as e:
	print(f" Conncection failed: {e}")

finally:
    if 'conn' in locals():
        cursor.close()
        conn.close()

