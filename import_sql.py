"""
SQL File Import Script for Mandiri Statement Bot
This script imports database structure and data from a .sql file.
"""

import argparse
import os
import sys

from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DATABASE_URL


def read_sql_file(file_path):
    """Read and return SQL content from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"❌ SQL file not found: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading SQL file: {str(e)}")
        return None


def execute_sql_statements(engine, sql_content):
    """Execute SQL statements from the content."""
    print("🔄 Executing SQL statements...")

    try:
        # Split SQL content into individual statements
        # Handle different statement separators
        statements = []

        # Split by semicolon and filter out empty statements
        raw_statements = sql_content.split(';')

        for statement in raw_statements:
            # Clean up the statement
            cleaned = statement.strip()
            if cleaned and not cleaned.startswith('--') and cleaned.upper() != 'COMMIT':
                statements.append(cleaned)

        executed_count = 0

        with engine.connect() as connection:
            # Start a transaction
            trans = connection.begin()

            try:
                for i, statement in enumerate(statements):
                    if statement.strip():
                        try:
                            # Execute the statement
                            connection.execute(text(statement))
                            executed_count += 1

                            # Print progress for long imports
                            if (i + 1) % 10 == 0:
                                print(f"   ✅ Executed {i + 1}/{len(statements)} statements...")

                        except Exception as stmt_error:
                            print(f"⚠️  Warning - Failed to execute statement {i + 1}: {str(stmt_error)}")
                            print(f"   Statement: {statement[:100]}...")
                            # Continue with other statements
                            continue

                # Commit the transaction
                trans.commit()
                print(f"✅ Successfully executed {executed_count}/{len(statements)} SQL statements!")

            except Exception as e:
                trans.rollback()
                print(f"❌ Transaction failed, rolling back: {str(e)}")
                return False

        return True

    except Exception as e:
        print(f"❌ Error executing SQL statements: {str(e)}")
        return False


def import_sql_with_mysql_dump(engine, sql_file):
    """Import SQL file that contains MySQL dump format."""
    print("🔄 Importing MySQL dump format...")

    try:
        sql_content = read_sql_file(sql_file)
        if not sql_content:
            return False

        # Pre-process MySQL dump content
        # Remove MySQL-specific comments and commands
        lines = sql_content.split('\n')
        processed_lines = []

        skip_patterns = [
            '/*!',
            'SET @',
            'SET SQL_MODE',
            'SET time_zone',
            'SET NAMES',
            'SET character_set',
            'LOCK TABLES',
            'UNLOCK TABLES',
            'DISABLE KEYS',
            'ENABLE KEYS'
        ]

        for line in lines:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('--') or line.startswith('#'):
                continue

            # Skip MySQL-specific commands
            if any(pattern in line for pattern in skip_patterns):
                continue

            # Replace MySQL-specific syntax if needed
            line = line.replace('`', '"')  # Replace backticks with quotes
            line = line.replace('ENGINE=InnoDB', '')  # Remove engine specification
            line = line.replace('AUTO_INCREMENT=', '')  # Remove auto increment values

            processed_lines.append(line)

        processed_content = '\n'.join(processed_lines)

        return execute_sql_statements(engine, processed_content)

    except Exception as e:
        print(f"❌ Error importing MySQL dump: {str(e)}")
        return False


def import_sql_file(sql_file, chunk_size=1000):
    """Main function to import SQL file."""
    print(f"🚀 Starting SQL Import from: {sql_file}")
    print("=" * 50)

    # Check if file exists
    if not os.path.exists(sql_file):
        print(f"❌ File not found: {sql_file}")
        return False

    # Create database engine
    try:
        engine = create_engine(DATABASE_URL)
        print(f"✅ Connected to database: {DATABASE_URL}")
    except Exception as e:
        print(f"❌ Failed to connect to database: {str(e)}")
        return False

    # Read SQL file
    sql_content = read_sql_file(sql_file)
    if not sql_content:
        return False

    print(f"📄 SQL file size: {len(sql_content)} characters")

    # Detect file type and import accordingly
    if 'mysqldump' in sql_content.lower() or 'MySQL dump' in sql_content:
        print("🔍 Detected MySQL dump format")
        return import_sql_with_mysql_dump(engine, sql_file)
    else:
        print("🔍 Detected standard SQL format")
        return execute_sql_statements(engine, sql_content)


def verify_import(engine):
    """Verify the import by checking table counts."""
    print("\n🔍 Verifying import...")

    try:
        with engine.connect() as connection:
            # Check if main tables exist and have data
            tables_to_check = [
                'bank_accounts',
                'bank_transactions',
                'categories',
                'subcategories',
                'budget_limits',
                'financial_goals'
            ]

            print("📊 Table verification:")
            total_records = 0

            for table in tables_to_check:
                try:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    total_records += count
                    print(f"   • {table}: {count} records")
                except Exception as e:
                    print(f"   • {table}: ❌ Error ({str(e)})")

            print(f"\n✅ Total records imported: {total_records}")

            if total_records > 0:
                print("🎉 Import verification successful!")
                return True
            else:
                print("⚠️  No data found in tables")
                return False

    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description='Import SQL file into Mandiri Statement Bot database')
    parser.add_argument('sql_file', help='Path to the SQL file to import')
    parser.add_argument('--verify', action='store_true', help='Verify import after completion')
    parser.add_argument('--chunk-size', type=int, default=1000, help='Number of statements to execute per batch')

    args = parser.parse_args()

    # Import the SQL file
    success = import_sql_file(args.sql_file, args.chunk_size)

    if success:
        print("\n✅ SQL import completed successfully!")

        # Verify import if requested
        if args.verify:
            engine = create_engine(DATABASE_URL)
            verify_import(engine)

        print("\n🤖 Your bot database is ready!")
        print("   Use /start in your Telegram bot to begin!")

    else:
        print("\n❌ SQL import failed!")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())