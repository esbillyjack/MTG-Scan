import os
from sqlalchemy import create_engine, text

def reset_sequences():
    postgres_url = os.getenv("DATABASE_URL")
    if not postgres_url:
        print("❌ DATABASE_URL not set")
        return
    
    engine = create_engine(postgres_url)
    with engine.connect() as conn:
        tables = ['cards', 'scans', 'scan_images', 'scan_results']
        for table in tables:
            seq_name = f'{table}_id_seq'
            query = text(f"SELECT setval('{seq_name}', coalesce((SELECT MAX(id)+1 FROM {table}), 1), false)")
            conn.execute(query)
            print(f"✅ Reset sequence for {table}")
        conn.commit()

if __name__ == "__main__":
    reset_sequences() 