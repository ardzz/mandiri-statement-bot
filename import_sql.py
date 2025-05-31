"""
Import SQL dump into Docker Compose MySQL container
"""

import os
import subprocess
import sys
import time
from datetime import datetime


class DockerComposeImporter:
    def __init__(self):
        self.compose_file = "docker-compose.yml"
        self.env_file = ".env"
        self.mysql_container = "finance_mysql"
        self.env_vars = self.load_env_vars()
        
    def load_env_vars(self):
        """Load environment variables from .env file."""
        env_vars = {}
        
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        
        # Set defaults if not found
        defaults = {
            'MYSQL_ROOT_PASSWORD': 'root_password',
            'MYSQL_DATABASE': 'finance_db',
            'MYSQL_USER': 'finance_user',
            'MYSQL_PASSWORD': 'finance_password',
            'MYSQL_PORT_FORWARD': '3306'
        }
        
        for key, default_value in defaults.items():
            if key not in env_vars:
                env_vars[key] = default_value
                print(f"⚠️  Using default for {key}: {default_value}")
        
        return env_vars
    
    def run_command(self, command, description="", capture_output=True):
        """Run shell command and return result."""
        if description:
            print(f"🔄 {description}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                check=True
            )
            return True, result.stdout if capture_output else ""
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if capture_output else str(e)
            return False, error_msg
    
    def check_prerequisites(self):
        """Check if Docker and docker compose are available."""
        print("🔍 Checking prerequisites...")
        
        # Check Docker
        success, _ = self.run_command("docker --version")
        if not success:
            print("❌ Docker is not installed or running")
            return False
        
        # Check docker compose
        success, _ = self.run_command("docker compose --version")
        if not success:
            print("❌ docker compose is not installed")
            return False
        
        # Check if docker compose.yml exists
        if not os.path.exists(self.compose_file):
            print(f"❌ {self.compose_file} not found")
            return False
        
        print("✅ All prerequisites met")
        return True
    
    def start_mysql_container(self):
        """Start MySQL container using docker compose."""
        print("🚀 Starting MySQL container...")
        
        # Start only the mysql service
        success, output = self.run_command(
            "docker compose up -d mysql",
            "Starting MySQL service..."
        )
        
        if not success:
            print(f"❌ Failed to start MySQL container: {output}")
            return False
        
        print("✅ MySQL container started")
        return True
    
    def wait_for_mysql(self, max_attempts=60):
        """Wait for MySQL to be ready."""
        print("⏳ Waiting for MySQL to be ready...")
        
        for attempt in range(max_attempts):
            success, _ = self.run_command(
                f"docker exec {self.mysql_container} mysqladmin ping -h localhost --silent",
                ""
            )
            
            if success:
                print("✅ MySQL is ready!")
                return True
            
            time.sleep(2)
            if (attempt + 1) % 10 == 0:
                print(f"   Still waiting... ({attempt + 1}/{max_attempts})")
        
        print("❌ MySQL failed to start within timeout")
        return False
    
    def copy_sql_file(self, sql_file):
        """Copy SQL file to MySQL container."""
        print("📋 Copying SQL file to container...")
        
        # Ensure the file exists
        if not os.path.exists(sql_file):
            print(f"❌ SQL file not found: {sql_file}")
            return False
        
        # Copy file to container
        success, output = self.run_command(
            f"docker cp '{sql_file}' {self.mysql_container}:/tmp/import.sql",
            f"Copying {os.path.basename(sql_file)}..."
        )
        
        if not success:
            print(f"❌ Failed to copy SQL file: {output}")
            return False
        
        print("✅ SQL file copied to container")
        return True
    
    def import_sql(self):
        """Import the SQL file into MySQL."""
        print("🔄 Importing SQL file...")
        
        # Prepare import command
        mysql_cmd = f"""
        docker exec -i {self.mysql_container} mysql \\
            -u root \\
            -p{self.env_vars['MYSQL_ROOT_PASSWORD']} \\
            {self.env_vars['MYSQL_DATABASE']} \\
            -e "
                SET FOREIGN_KEY_CHECKS = 0;
                SET AUTOCOMMIT = 0;
                SET UNIQUE_CHECKS = 0;
                SOURCE /tmp/import.sql;
                COMMIT;
                SET FOREIGN_KEY_CHECKS = 1;
                SET UNIQUE_CHECKS = 1;
            "
        """
        
        success, output = self.run_command(mysql_cmd, "Executing SQL import...")
        
        if not success:
            print(f"❌ SQL import failed: {output}")
            return False
        
        print("✅ SQL import completed!")
        return True
    
    def verify_import(self):
        """Verify the import by checking tables and record counts."""
        print("🔍 Verifying import...")
        
        verify_cmd = f"""
        docker exec {self.mysql_container} mysql \\
            -u root \\
            -p{self.env_vars['MYSQL_ROOT_PASSWORD']} \\
            {self.env_vars['MYSQL_DATABASE']} \\
            -e "
                SELECT 
                    TABLE_NAME as 'Table',
                    TABLE_ROWS as 'Rows'
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = '{self.env_vars['MYSQL_DATABASE']}' 
                ORDER BY TABLE_NAME;
            "
        """
        
        success, output = self.run_command(verify_cmd)
        
        if success:
            print("📊 Database tables:")
            print(output)
            
            # Count total records
            lines = output.strip().split('\n')[1:]  # Skip header
            total_records = 0
            table_count = 0
            
            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        try:
                            records = int(parts[1]) if parts[1] != 'NULL' else 0
                            total_records += records
                            table_count += 1
                        except:
                            pass
            
            print(f"\n📈 Summary:")
            print(f"   • Tables: {table_count}")
            print(f"   • Total records: {total_records:,}")
            
            return table_count > 0
        else:
            print(f"❌ Verification failed: {output}")
            return False
    
    def show_connection_info(self):
        """Show database connection information."""
        print("\n🎉 Import completed successfully!")
        print("=" * 50)
        print("📊 Database Connection Information:")
        print(f"   Host: localhost")
        print(f"   Port: {self.env_vars['MYSQL_PORT_FORWARD']}")
        print(f"   Database: {self.env_vars['MYSQL_DATABASE']}")
        print(f"   Username: {self.env_vars['MYSQL_USER']}")
        print(f"   Password: {self.env_vars['MYSQL_PASSWORD']}")
        print(f"\n🔗 DATABASE_URL:")
        print(f"   mysql+pymysql://{self.env_vars['MYSQL_USER']}:{self.env_vars['MYSQL_PASSWORD']}@localhost:{self.env_vars['MYSQL_PORT_FORWARD']}/{self.env_vars['MYSQL_DATABASE']}")
        print(f"\n🤖 To start your bot:")
        print(f"   docker compose up bot")
    
    def import_sql_file(self, sql_file):
        """Main import process."""
        print("🗃️  Docker Compose MySQL Import")
        print(f"👤 User: ardzz")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # Show file info
        if os.path.exists(sql_file):
            file_size = os.path.getsize(sql_file)
            print(f"📄 SQL File: {sql_file}")
            print(f"📏 Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
        else:
            print(f"❌ SQL file not found: {sql_file}")
            return False
        
        # Show environment
        print(f"🐳 MySQL Container: {self.mysql_container}")
        print(f"🗄️  Database: {self.env_vars['MYSQL_DATABASE']}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Start MySQL container
        if not self.start_mysql_container():
            return False
        
        # Wait for MySQL to be ready
        if not self.wait_for_mysql():
            return False
        
        # Copy SQL file
        if not self.copy_sql_file(sql_file):
            return False
        
        # Import SQL
        if not self.import_sql():
            return False
        
        # Verify import
        if not self.verify_import():
            print("⚠️  Import completed but verification had issues")
        
        # Show connection info
        self.show_connection_info()
        
        return True

def main():
    """Main function."""
    # Default SQL file name based on your file
    default_sql_file = "finance_db_localhost-2025_05_31_06_00_28-dump.sql"
    
    if len(sys.argv) > 1:
        sql_file = sys.argv[1]
    else:
        sql_file = input(f"📁 Enter SQL file path (default: {default_sql_file}): ").strip()
        if not sql_file:
            sql_file = default_sql_file
    
    # Create importer and run
    importer = DockerComposeImporter()
    
    # Confirm import
    confirm = input(f"\n🚀 Import {sql_file} into Docker MySQL? (Y/n): ").strip().lower()
    if confirm == 'n':
        print("❌ Import cancelled")
        return 0
    
    success = importer.import_sql_file(sql_file)
    
    if success:
        print("\n🎉 All done! Your bot database is ready.")
    else:
        print("\n❌ Import failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())