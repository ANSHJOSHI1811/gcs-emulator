"""Fix instances table memory column"""
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="gcs_emulator",
    user="gcs_user",
    password="gcs_password"
)

try:
    cur = conn.cursor()
    
    # Check if memory column exists
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'instances' AND column_name IN ('memory', 'memory_mb')
    """)
    columns = [row[0] for row in cur.fetchall()]
    print(f"Current columns: {columns}")
    
    if 'memory' in columns and 'memory_mb' not in columns:
        print("Renaming memory to memory_mb...")
        cur.execute("ALTER TABLE instances RENAME COLUMN memory TO memory_mb")
        conn.commit()
        print("✓ Column renamed successfully")
    elif 'memory_mb' in columns:
        print("✓ Column memory_mb already exists")
    else:
        print("Neither column exists, creating memory_mb...")
        cur.execute("ALTER TABLE instances ADD COLUMN memory_mb INTEGER DEFAULT 512")
        conn.commit()
        print("✓ Column memory_mb created")
        
    cur.close()
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
