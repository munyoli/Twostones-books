import psycopg2
import sys
import os

# Your connection string
# Be sure to replace [YOUR-PASSWORD] with your actual Supabase database password
DB_URL = "postgresql://postgres.shhmyyamptradvrootme:[YOUR-PASSWORD]@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

def run_sql():
    if "[YOUR-PASSWORD]" in DB_URL:
        print("❌ Error: Please open run_schema.py and replace [YOUR-PASSWORD] with your actual database password.")
        sys.exit(1)
        
    print("Connecting to Supabase...")
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Reading schema.sql...")
        with open("schema.sql", "r", encoding="utf-8") as f:
            sql = f.read()
            
        print("Running SQL schema...")
        cursor.execute(sql)
        
        print("✅ Schema executed successfully! The tables and policies have been created.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Failed to execute schema. Error details:\n{e}")

if __name__ == "__main__":
    run_sql()
