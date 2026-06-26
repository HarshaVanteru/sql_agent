"""Debug script to print MongoDB credentials."""
import os
from sqlalchemy import create_engine, text

# Use synchronous MySQL driver instead of async
db_url = "mysql+pymysql://root:root@localhost:3306/ecom_analytics"

# Create engine
engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        # Query all database credentials
        result = conn.execute(text("SELECT * FROM database_credentials"))

        print("\n" + "="*80)
        print("DATABASE CREDENTIALS")
        print("="*80 + "\n")

        rows = result.fetchall()
        if not rows:
            print("[NO DATA] No database credentials found!")
        else:
            for row in rows:
                print(f"ID:             {row[0]}")
                print(f"Database ID:    {row[1]}")
                print(f"Host:           {row[2]}")
                print(f"Port:           {row[3]}")
                print(f"Username:       {row[4]}")
                print(f"Password:       {row[5]}")
                print(f"Database Name:  {row[6]}")
                print("-"*80)

        # Also show all databases for reference
        print("\n" + "="*80)
        print("ALL CONFIGURED DATABASES")
        print("="*80 + "\n")

        result2 = conn.execute(text("SELECT id, name, db_type FROM `databases`"))

        for row in result2.fetchall():
            print(f"  {row[1]:30} (ID: {row[0]}, Type: {row[2]})")

except Exception as e:
    print(f"[ERROR] {e}")
finally:
    engine.dispose()
