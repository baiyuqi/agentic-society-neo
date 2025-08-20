import sys
import os
import argparse
from sqlalchemy import create_engine, text, inspect

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def get_cols_to_drop_from_persona():
    """Columns in the original table that are NOT in the final Persona entity design."""
    return [
        "education_num", "relationship", "capital_gain",
        "capital_loss", "hours_per_week", "income"
    ]

def get_cols_to_drop_from_skeleton():
    """The skeleton should not contain the enriched persona description."""
    return ["persona_desc", "elicited"]

def migrate_schema(db_path):
    """
    Migrates the persona schema by:
    1. Copying 'persona' to 'skeleton_persona'.
    2. Cleaning 'skeleton_persona' by dropping enriched data columns.
    3. Modifying 'persona' to match the entity design:
       a. Adds and populates 'sourcePersonaId'.
       b. Drops columns not present in the final 'Persona' entity.
    """
    # 拼接为绝对路径（基于当前工作目录）
    abs_db_path = os.path.abspath(db_path)

    if not os.path.exists(abs_db_path):
        print(f"Error: Database file not found at {abs_db_path}")
        return


    print(f"Starting schema migration for database: {db_path}")
    engine = create_engine(f'sqlite:///{db_path}')
    
    with engine.connect() as connection:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if "skeleton_persona" in tables:
            print("Migration appears to have already been completed. Skipping.")
            return
        if "persona" not in tables:
            print("No 'persona' table found. Nothing to migrate.")
            return

        try:
            persona_columns = [col['name'] for col in inspector.get_columns('persona')]
        except Exception as e:
            print(f"Could not inspect columns of 'persona' table. Error: {e}")
            return

        cols_to_drop_from_persona = [c for c in get_cols_to_drop_from_persona() if c in persona_columns]
        cols_to_drop_from_skeleton = [c for c in get_cols_to_drop_from_skeleton() if c in persona_columns]

        with connection.begin() as transaction:
            try:
                print("Step 1: Creating 'skeleton_persona' table with primary key...")

                # 构造列定义（保持原 persona 表中已有列）
                column_defs = []
                for col in inspector.get_columns('persona'):
                    col_name = col['name']
                    col_type = str(col['type'])
                    if col_name == 'id':
                        column_defs.append(f"{col_name} INTEGER PRIMARY KEY")
                    else:
                        column_defs.append(f"{col_name} {col_type}")

                create_sql = f"CREATE TABLE skeleton_persona ({', '.join(column_defs)});"
                connection.execute(text(create_sql))

                print("Step 2: Copying data to 'skeleton_persona'...")
                col_names = ", ".join(persona_columns)
                connection.execute(text(f"INSERT INTO skeleton_persona ({col_names}) SELECT {col_names} FROM persona;"))


                print("Step 2: Cleaning up 'skeleton_persona' table...")
                for col in cols_to_drop_from_skeleton:
                    connection.execute(text(f'ALTER TABLE skeleton_persona DROP COLUMN {col}'))

                print("Step 3: Modifying 'persona' table...")
                print("  - Adding 'sourcePersonaId' column...")
                connection.execute(text('ALTER TABLE persona ADD COLUMN sourcePersonaId VARCHAR(30)'))
                
                print("  - Populating 'sourcePersonaId' column...")
                connection.execute(text('UPDATE persona SET sourcePersonaId = CAST(id AS VARCHAR(30))'))

                print("  - Dropping columns to match final design...")
                for col in cols_to_drop_from_persona:
                    connection.execute(text(f'ALTER TABLE persona DROP COLUMN {col}'))
                
                transaction.commit()
                print("\nMigration finished successfully!")

            except Exception as e:
                print(f"\nAn error occurred during migration: {e}")
                print("The transaction has been rolled back.")
                transaction.rollback()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate persona data schema.")
    parser.add_argument("db_file", help="The absolute path to the SQLite database file.")
    args = parser.parse_args()
    migrate_schema(args.db_file)
