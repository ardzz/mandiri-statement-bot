"""
SQL File Import Script for Mandiri Statement Bot
This script imports database structure and data from a .sql file with MySQL compatibility.
"""

import sys
import os
import argparse
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to sys.path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DATABASE_URL

def detect_database_type():
    """Detect database type from DATABASE_URL."""
    url_lower = DATABASE_URL.lower()
    if 'mysql' in url_lower:
        return 'mysql'
    elif 'postgresql' in url_lower:
        return 'postgresql'
    elif 'sqlite' in url_lower:
        return 'sqlite'
    else:
        return 'unknown'

def convert_sql_for_mysql(sql_content):
    """Convert SQL syntax to be MySQL compatible."""
    print("🔄 Converting SQL syntax for MySQL...")

    # Replace double quotes with backticks for table/column names
    # But preserve double quotes in string literals
    def replace_quotes(match):
        content = match.group(1)
        # If it looks like a table/column name (no spaces, alphanumeric + underscore)
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', content):
            return f'`{content}`'
        else:
            # Keep as double quotes for string literals
            return f'"{content}"'

    # Replace "table_name" with `table_name` but preserve string literals
    sql_content = re.sub(r'"([^"]*)"', replace_quotes, sql_content)

    # Fix specific MySQL syntax issues
    replacements = [
        # Remove IF EXISTS from CREATE TABLE (MySQL handles this differently)
        (r'CREATE TABLE IF NOT EXISTS `([^`]+)`', r'CREATE TABLE `\1`'),

        # Replace SERIAL with AUTO_INCREMENT
        (r'\bSERIAL\b', 'INT AUTO_INCREMENT'),

        # Replace BOOLEAN with TINYINT(1)
        (r'\bBOOLEAN\b', 'TINYINT(1)'),

        # Replace TEXT with appropriate MySQL text types
        (r'\bTEXT\b', 'TEXT'),

        # Handle datetime defaults
        (r"DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
        (r"DEFAULT NOW\(\)", "DEFAULT CURRENT_TIMESTAMP"),

        # Remove ON UPDATE CASCADE if not supported
        (r'\bON UPDATE CASCADE\b', ''),

        # Fix constraint syntax
        (r'CONSTRAINT `([^`]+)` ', r'CONSTRAINT \1 '),
    ]

    for pattern, replacement in replacements:
        sql_content = re.sub(pattern, replacement, sql_content, flags=re.IGNORECASE)

    return sql_content

def convert_sql_for_postgresql(sql_content):
    """Convert SQL syntax to be PostgreSQL compatible."""
    print("🔄 Converting SQL syntax for PostgreSQL...")

    # Replace backticks with double quotes
    sql_content = re.sub(r'`([^`]*)`', r'"\1"', sql_content)

    # Other PostgreSQL-specific conversions
    replacements = [
        (r'\bAUTO_INCREMENT\b', 'SERIAL'),
        (r'\bTINYINT\(1\)\b', 'BOOLEAN'),
        (r'\bDATETIME\b', 'TIMESTAMP'),
    ]

    for pattern, replacement in replacements:
        sql_content = re.sub(pattern, replacement, sql_content, flags=re.IGNORECASE)

    return sql_content

def clean_sql_content(sql_content, db_type):
    """Clean and prepare SQL content based on database type."""
    print(f"🧹 Cleaning SQL content for {db_type}...")

    # Remove comments and empty lines
    lines = sql_content.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('--') or line.startswith('#'):
            continue

        # Remove inline comments
        if '--' in line:
            line = line.split('--')[0].strip()

        if line:
            cleaned_lines.append(line)

    cleaned_content = '\n'.join(cleaned_lines)

    # Convert syntax based on database type
    if db_type == 'mysql':
        cleaned_content = convert_sql_for_mysql(cleaned_content)
    elif db_type == 'postgresql':
        cleaned_content = convert_sql_for_postgresql(cleaned_content)

    return cleaned_content

def execute_sql_statements(engine, sql_content, db_type):
    """Execute SQL statements from the content."""
    print("🔄 Executing SQL statements...")

    try:
        # Clean the SQL content
        cleaned_sql = clean_sql_content(sql_content, db_type)

        # Split SQL content into individual statements
        statements = []

        # Split by semicolon and filter out empty statements
        raw_statements = cleaned_sql.split(';')

        for statement in raw_statements:
            cleaned = statement.strip()
            if cleaned and len(cleaned) > 5:  # Ignore very short statements
                statements.append(cleaned)

        print(f"📝 Found {len(statements)} SQL statements to execute")
        executed_count = 0
        failed_count = 0

        with engine.connect() as connection:
            # Disable foreign key checks for MySQL
            if db_type == 'mysql':
                try:
                    connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                except:
                    pass

            for i, statement in enumerate(statements):
                try:
                    # Execute the statement
                    connection.execute(text(statement))
                    executed_count += 1

                    # Print progress for long imports
                    if (i + 1) % 5 == 0:
                        print(f"   ✅ Executed {i + 1}/{len(statements)} statements...")

                except Exception as stmt_error:
                    failed_count += 1
                    print(f"⚠️  Statement {i + 1} failed: {str(stmt_error)}")
                    print(f"   Statement: {statement[:100]}...")

                    # For critical errors, stop execution
                    if "syntax error" in str(stmt_error).lower():
                        print("❌ Critical syntax error detected. Stopping execution.")
                        break

                    # Continue with other statements for non-critical errors
                    continue

            # Re-enable foreign key checks for MySQL
            if db_type == 'mysql':
                try:
                    connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                except:
                    pass

            # Commit all changes
            connection.commit()

        print(f"✅ Successfully executed {executed_count} statements")
        if failed_count > 0:
            print(f"⚠️  {failed_count} statements failed")

        return executed_count > 0

    except Exception as e:
        print(f"❌ Error executing SQL statements: {str(e)}")
        return False

def read_sql_file(file_path):
    """Read and return SQL content from file."""
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                print(f"✅ Successfully read SQL file with {encoding} encoding")
                return content
            except UnicodeDecodeError:
                continue

        print("❌ Could not read file with any supported encoding")
        return None

    except FileNotFoundError:
        print(f"❌ SQL file not found: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading SQL file: {str(e)}")
        return None

def import_sql_file(sql_file):
    """Main function to import SQL file."""
    print(f"🚀 Starting SQL Import from: {sql_file}")
    print("=" * 60)

    # Check if file exists
    if not os.path.exists(sql_file):
        print(f"❌ File not found: {sql_file}")
        return False

    # Detect database type
    db_type = detect_database_type()
    print(f"🔍 Detected database type: {db_type}")

    # Create database engine
    try:
        engine = create_engine(DATABASE_URL)
        print(f"✅ Connected to database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {str(e)}")
        return False

    # Read SQL file
    sql_content = read_sql_file(sql_file)
    if not sql_content:
        return False

    print(f"📄 SQL file size: {len(sql_content):,} characters")

    # Execute SQL statements
    return execute_sql_statements(engine, sql_content, db_type)

def verify_import():
    """Verify the import by checking table counts."""
    print("\n🔍 Verifying import...")

    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            # Check if main tables exist and have data
            tables_to_check = [
                'bank_accounts',
                'bank_transactions',
                'categories',
                'subcategories',
                'budget_limits',
                'financial_goals',
                'spending_alerts'
            ]

            print("📊 Table verification:")
            total_records = 0

            for table in tables_to_check:
                try:
                    # Use backticks for MySQL, quotes for others
                    db_type = detect_database_type()
                    if db_type == 'mysql':
                        query = f"SELECT COUNT(*) FROM `{table}`"
                    else:
                        query = f'SELECT COUNT(*) FROM "{table}"'

                    result = connection.execute(text(query))
                    count = result.scalar()
                    total_records += count
                    print(f"   • {table}: {count:,} records")
                except Exception as e:
                    print(f"   • {table}: ❌ Error ({str(e)})")

            print(f"\n✅ Total records imported: {total_records:,}")
            return total_records > 0

    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description='Import SQL file into Mandiri Statement Bot database')
    parser.add_argument('sql_file', nargs='?', help='Path to the SQL file to import')
    parser.add_argument('--verify', action='store_true', help='Verify import after completion')

    args = parser.parse_args()

    # Get SQL file path
    sql_file = args.sql_file
    if not sql_file:
        sql_file = input("📁 Enter path to your SQL file: ").strip()

    # Import the SQL file
    success = import_sql_file(sql_file)

    if success:
        print("\n✅ SQL import completed!")

        # Verify import if requested or ask user
        if args.verify or input("\n🔍 Verify import? (Y/n): ").strip().lower() != 'n':
            if verify_import():
                print("🎉 Import verification successful!")
            else:
                print("⚠️  Import verification found issues")

        print("\n🤖 Your bot database is ready!")
        print("   Use /start in your Telegram bot to begin!")

    else:
        print("\n❌ SQL import failed!")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())