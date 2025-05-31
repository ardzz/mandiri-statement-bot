"""
Robust SQL Import Script that handles malformed SQL and data cleanup.
"""

import sys
import os
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DATABASE_URL

def clean_and_fix_sql_content(content):
    """Clean and fix malformed SQL content."""
    print("🧹 Cleaning and fixing SQL content...")

    lines = content.split('\n')
    cleaned_lines = []
    current_statement = ""
    in_insert = False

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('--') or line.startswith('#'):
            continue

        # Fix escaped newlines in data
        line = line.replace('\\n', ' ')

        # Remove problematic characters that might cause issues
        line = re.sub(r'[^\x20-\x7E\x09\x0A\x0D]', '', line)  # Keep only printable ASCII

        # Handle incomplete INSERT statements
        if line.startswith('INSERT INTO') or line.startswith('insert into'):
            if current_statement:
                # Finish previous statement
                if not current_statement.rstrip().endswith(';'):
                    current_statement += ';'
                cleaned_lines.append(current_statement)
            current_statement = line
            in_insert = True

        # Handle lines that look like orphaned data (like your error case)
        elif re.match(r"^[A-Z\s]+\\n\d+',\d+,\d+,\d+,\d+,\d+", line):
            print(f"⚠️  Skipping orphaned data line {line_num}: {line[:100]}...")
            continue

        # Handle regular lines
        elif current_statement:
            current_statement += " " + line
        else:
            # Standalone statement
            cleaned_lines.append(line)

        # Check if statement is complete
        if current_statement and line.endswith(';'):
            cleaned_lines.append(current_statement)
            current_statement = ""
            in_insert = False

    # Add final statement if exists
    if current_statement:
        if not current_statement.rstrip().endswith(';'):
            current_statement += ';'
        cleaned_lines.append(current_statement)

    return '\n'.join(cleaned_lines)

def extract_and_fix_insert_statements(content):
    """Extract and fix INSERT statements from malformed SQL."""
    print("🔧 Extracting and fixing INSERT statements...")

    # Find all complete INSERT statements
    insert_pattern = r'INSERT INTO\s+`?(\w+)`?\s*\([^)]+\)\s*VALUES\s*\([^;]+\);'
    matches = re.findall(insert_pattern, content, re.IGNORECASE | re.DOTALL)

    fixed_statements = []

    # Extract complete statements
    for match in re.finditer(insert_pattern, content, re.IGNORECASE | re.DOTALL):
        statement = match.group(0)

        # Clean the statement
        statement = statement.replace('\\n', ' ')
        statement = re.sub(r'\s+', ' ', statement)  # Normalize whitespace

        fixed_statements.append(statement)

    return fixed_statements

def import_sql_with_recovery(sql_file):
    """Import SQL with error recovery and data validation."""
    print(f"🚀 Starting robust SQL import from: {sql_file}")
    print("=" * 60)

    # Read the file
    try:
        with open(sql_file, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    print(f"📄 Original file size: {len(content):,} characters")

    # Clean and fix the content
    cleaned_content = clean_and_fix_sql_content(content)

    print(f"📄 Cleaned content size: {len(cleaned_content):,} characters")

    # Connect to database
    try:
        engine = create_engine(DATABASE_URL)
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

    # Split into statements
    statements = [s.strip() for s in cleaned_content.split(';') if s.strip()]

    print(f"📝 Found {len(statements)} statements to execute")

    # Execute statements with recovery
    executed = 0
    failed = 0

    with engine.connect() as connection:
        # Disable foreign key checks for MySQL
        try:
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            connection.execute(text("SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO'"))
        except:
            pass

        for i, statement in enumerate(statements, 1):
            try:
                # Skip very short statements
                if len(statement) < 10:
                    continue

                # Validate statement before execution
                if not is_valid_sql_statement(statement):
                    print(f"⚠️  Skipping invalid statement {i}: {statement[:50]}...")
                    continue

                # Execute statement
                connection.execute(text(statement))
                executed += 1

                if i % 10 == 0:
                    print(f"   ✅ Executed {i}/{len(statements)} statements...")

            except Exception as e:
                failed += 1
                error_msg = str(e)

                # Log specific error types
                if "syntax error" in error_msg.lower():
                    print(f"❌ Syntax error in statement {i}: {statement[:100]}...")
                elif "duplicate" in error_msg.lower():
                    print(f"⚠️  Duplicate entry in statement {i} (skipping)")
                else:
                    print(f"⚠️  Error in statement {i}: {error_msg}")

                continue

        # Commit all changes
        try:
            connection.commit()
            print(f"✅ Committed all changes")
        except Exception as e:
            print(f"⚠️  Commit warning: {e}")

        # Re-enable foreign key checks
        try:
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        except:
            pass

    print(f"\n📊 Import Summary:")
    print(f"   • Executed: {executed} statements")
    print(f"   • Failed: {failed} statements")
    print(f"   • Success rate: {(executed/(executed+failed)*100):.1f}%")

    return executed > 0

def is_valid_sql_statement(statement):
    """Basic validation for SQL statements."""
    statement = statement.strip().upper()

    # Check if it starts with valid SQL keywords
    valid_starts = ['CREATE', 'INSERT', 'UPDATE', 'DELETE', 'ALTER', 'DROP', 'SELECT']

    if not any(statement.startswith(keyword) for keyword in valid_starts):
        return False

    # Check for basic SQL structure
    if statement.startswith('INSERT') and 'VALUES' not in statement:
        return False

    # Check for malformed data (like your error case)
    if re.match(r'^[A-Z\s]+\\n\d+', statement):
        return False

    return True

def create_recovery_sql(original_file):
    """Create a cleaned version of the SQL file for manual review."""
    print("💾 Creating recovery SQL file...")

    try:
        with open(original_file, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()

        # Clean content
        cleaned_content = clean_and_fix_sql_content(content)

        # Save cleaned version
        recovery_file = original_file.replace('.sql', '_cleaned.sql')
        with open(recovery_file, 'w', encoding='utf-8') as file:
            file.write(cleaned_content)

        print(f"✅ Cleaned SQL saved to: {recovery_file}")
        return recovery_file

    except Exception as e:
        print(f"❌ Error creating recovery file: {e}")
        return None

def verify_import():
    """Verify the import results."""
    print("\n🔍 Verifying import...")

    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:

            tables = [
                'bank_accounts', 'bank_transactions', 'categories',
                'subcategories', 'budget_limits', 'financial_goals'
            ]

            total_records = 0

            for table in tables:
                try:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM `{table}`"))
                    count = result.scalar()
                    total_records += count
                    print(f"   • {table}: {count:,} records")
                except Exception as e:
                    print(f"   • {table}: ❌ ({str(e)})")

            print(f"\n✅ Total records: {total_records:,}")
            return total_records > 0

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) > 1:
        sql_file = sys.argv[1]
    else:
        sql_file = input("📁 Enter path to your SQL file: ").strip()

    if not os.path.exists(sql_file):
        print(f"❌ File not found: {sql_file}")
        return 1

    # Ask user what to do
    print("\nOptions:")
    print("1. Import with robust error handling")
    print("2. Create cleaned SQL file only")
    print("3. Both import and create cleaned file")

    choice = input("\nChoose option (1-3): ").strip()

    if choice in ['2', '3']:
        recovery_file = create_recovery_sql(sql_file)
        if choice == '2':
            return 0

    if choice in ['1', '3']:
        success = import_sql_with_recovery(sql_file)

        if success:
            print("\n✅ Import completed!")

            if input("\n🔍 Verify import? (Y/n): ").strip().lower() != 'n':
                verify_import()

            print("\n🤖 Your database is ready!")
        else:
            print("\n❌ Import failed!")
            return 1

    return 0

if __name__ == "__main__":
    exit(main())