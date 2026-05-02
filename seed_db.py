from sqlalchemy import text
from database import engine

def setup_db():
    with engine.connect() as conn:
        # 1. Purani table delete karo agar hai toh
        conn.execute(text("DROP TABLE IF EXISTS pricing_master"))
        
        # 2. PostgreSQL specific syntax (SERIAL use karna hai)
        conn.execute(text("""
            CREATE TABLE pricing_master (
                id SERIAL PRIMARY KEY,
                service_name TEXT NOT NULL,
                instance_type TEXT,
                hourly_rate REAL NOT NULL
            )
        """))
        
        # 3. Data Insert karo
        conn.execute(text("INSERT INTO pricing_master (service_name, instance_type, hourly_rate) VALUES ('EC2', 't3.medium', 0.0416)"))
        conn.execute(text("INSERT INTO pricing_master (service_name, instance_type, hourly_rate) VALUES ('S3', '100GB Standard', 0.0031)"))
        conn.execute(text("INSERT INTO pricing_master (service_name, instance_type, hourly_rate) VALUES ('RDS', 'db.t3.micro', 0.017)"))
        
        # PostgreSQL mein commit karna zaroori hai
        conn.commit()
        print("Postgres Table Created and Seeded")

if __name__ == "__main__":
    setup_db()