from sqlalchemy import text
from database import engine

def setup_db():
    with engine.connect() as conn:
        # 1. Purani table delete karo agar hai toh
        conn.execute(text("DROP TABLE IF EXISTS pricing_master"))
        
        # 2. Asli SQL Syntax se Table banao
        conn.execute(text("""
            CREATE TABLE pricing_master (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                instance_type TEXT,
                hourly_rate REAL NOT NULL
            )
        """))
        
        # 3. Data Insert karo (SQL Insert Query)
        conn.execute(text("INSERT INTO pricing_master (service_name, instance_type, hourly_rate) VALUES ('EC2', 't3.medium', 0.0416)"))
        conn.execute(text("INSERT INTO pricing_master (service_name, instance_type, hourly_rate) VALUES ('S3', '100GB Standard', 0.0031)"))
        conn.execute(text("INSERT INTO pricing_master (service_name, instance_type, hourly_rate) VALUES ('RDS', 'db.t3.micro', 0.017)"))
        
        conn.commit()
        print("SQL Table Created and Seeded, Bhai!")

if __name__ == "__main__":
    setup_db()