# -*- coding: utf-8 -*-
import psycopg2

try:
    print("Attempting to connect to the database...")
    conn = psycopg2.connect(
        host="localhost",
        database="Kanban",
        user="postgres",
        password="#Gabriel19",
        port="5432"
    )
    cursor = conn.cursor()
    print("✓ Connection successful!")
    
    # Test the cursor
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✓ Database version: {version[0]}")
    
    # Test a simple query
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    print(f"✓ Query test successful: {result[0]}")
    
    cursor.close()
    conn.close()
    print("\n✓ All tests passed! Database connection is working correctly.")
    
except Exception as e:
    print(f"\n✗ Connection failed with error:")
    print(f"  {type(e).__name__}: {str(e)}")
