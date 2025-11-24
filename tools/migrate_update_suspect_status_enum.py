import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def update_suspect_status_enum():
    print("Starting migration: Update suspect_status enum")

    database_url = settings.DATABASE_URL
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            check_query = text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (
                    SELECT oid 
                    FROM pg_type 
                    WHERE typname = 'suspect_status'
                )
                ORDER BY enumsortorder
            """)
            result = conn.execute(check_query)
            current_values = [row[0] for row in result.fetchall()]
            
            print(f"Current enum values: {current_values}")
            
            required_values = ["Witness", "Reported", "Suspected", "Suspect", "Defendant"]
            missing_values = [v for v in required_values if v not in current_values]
            
            if not missing_values:
                print("All required enum values already exist. Migration not needed.")
                return
            
            print(f"Missing enum values: {missing_values}")
            print("Adding missing enum values...")
            
            for value in missing_values:
                try:
                    if value not in current_values:
                        alter_query = text(f"""
                            ALTER TYPE suspect_status 
                            ADD VALUE IF NOT EXISTS '{value}'
                        """)
                        conn.execute(alter_query)
                        conn.commit()
                        print(f"Successfully added enum value: '{value}'")
                        current_values.append(value)
                except Exception as e:
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print(f"Enum value '{value}' already exists, skipping...")
                        continue
                    else:
                        raise
            
            result = conn.execute(check_query)
            final_values = [row[0] for row in result.fetchall()]
            print(f"Final enum values: {final_values}")
            
            print("Migration completed successfully!")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        if "if not exists" in str(e).lower():
            print("Trying alternative approach...")
            try:
                with engine.connect() as conn:
                    for value in missing_values:
                        try:
                            alter_query = text(f"""
                                DO $$ 
                                BEGIN
                                    IF NOT EXISTS (
                                        SELECT 1 FROM pg_enum 
                                        WHERE enumlabel = '{value}' 
                                        AND enumtypid = (
                                            SELECT oid FROM pg_type WHERE typname = 'suspect_status'
                                        )
                                    ) THEN
                                        ALTER TYPE suspect_status ADD VALUE '{value}';
                                    END IF;
                                END $$;
                            """)
                            conn.execute(alter_query)
                            conn.commit()
                            print(f"Successfully added enum value: '{value}'")
                        except Exception as e2:
                            if "already exists" in str(e2).lower() or "duplicate" in str(e2).lower():
                                print(f"Enum value '{value}' already exists, skipping...")
                                continue
                            else:
                                print(f"Error adding '{value}': {e2}")
                print("Migration completed successfully with alternative approach!")
            except Exception as e3:
                print(f"Error with alternative approach: {e3}")
                raise
        else:
            raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    update_suspect_status_enum()

