#!/usr/bin/env python3
"""
Persona Manager Command Line Tool

This CLI tool provides commands to operate on the CURRENT DATABASE:
1. Add skeleton personas to the current database
2. Enrich existing personas without descriptions in the current database
3. Show status of the current database
4. Switch current database

The tool operates on whatever database is currently set as the "current database".
You can switch databases using the --database option or set-db command.

Usage:
    python persona_cli.py status
    python persona_cli.py set-db --path data/db/mydb.db
    python persona_cli.py add-skeletons --count 10
    python persona_cli.py enrich-empty
"""

import argparse
import sys
import time
import os
from typing import Optional
from asociety.generator.persona_manager import PersonaManagerFactory
from asociety.repository.database import set_currentdb, get_currentdb_path


class CLIProgressBar:
    """Simple CLI progress bar"""
    
    def __init__(self, total: int, width: int = 50):
        self.total = total
        self.width = width
        self.current = 0
        
    def update(self, current: int, message: str = ""):
        self.current = current
        percentage = (current / self.total) * 100 if self.total > 0 else 0
        filled = int(self.width * current / self.total) if self.total > 0 else 0
        bar = '█' * filled + '░' * (self.width - filled)
        
        # Clear line and print progress
        print(f'\r[{bar}] {percentage:6.1f}% ({current}/{self.total}) {message}', end='', flush=True)
        
        if current >= self.total:
            print()  # New line when complete


class PersonaCLI:
    """Command Line Interface for Persona Manager - operates on current database"""

    def __init__(self):
        self.manager = PersonaManagerFactory.create()

    def set_database(self, db_path: str) -> None:
        """Set the current database"""
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return

        try:
            set_currentdb(db_path)
            print(f"✅ Current database set to: {db_path}")
            self.show_status()
        except Exception as e:
            print(f"❌ Error setting database: {e}")

    def get_current_database_info(self) -> dict:
        """Get information about current database"""
        return self.manager.get_current_database_info()
        
    def add_skeletons(self, count: int, verbose: bool = False) -> int:
        """Add skeleton personas to the database"""
        print(f"🚀 Adding {count} skeleton personas to the database...")
        
        if verbose:
            progress_bar = CLIProgressBar(count)
            
            def progress_callback(current, total, message):
                progress_bar.update(current, message)
            
            start_time = time.time()
            added_count = self.manager.add_skeleton_personas(count, progress_callback)
            end_time = time.time()
            
            print(f"✅ Successfully added {added_count} skeleton personas")
            print(f"⏱️  Time taken: {end_time - start_time:.2f} seconds")
        else:
            added_count = self.manager.add_skeleton_personas(count)
            print(f"✅ Successfully added {added_count} skeleton personas")
            
        return added_count
    
    def enrich_empty(self, verbose: bool = False) -> int:
        """Enrich personas without descriptions"""
        print("🔍 Scanning database for personas without descriptions...")
        
        # First, check how many need enrichment
        empty_personas = self.manager._get_personas_without_desc()
        if not empty_personas:
            print("ℹ️  No personas found that need enrichment")
            return 0
            
        count = len(empty_personas)
        print(f"📝 Found {count} personas that need enrichment")
        
        # Ask for confirmation if many personas
        if count > 10:
            response = input(f"⚠️  This will enrich {count} personas using LLM. Continue? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("❌ Operation cancelled")
                return 0
        
        if verbose:
            progress_bar = CLIProgressBar(count)
            
            def progress_callback(current, total, message):
                progress_bar.update(current, message)
            
            start_time = time.time()
            enriched_count = self.manager.enrich_empty_personas(progress_callback)
            end_time = time.time()
            
            print(f"✅ Successfully enriched {enriched_count} personas")
            print(f"⏱️  Time taken: {end_time - start_time:.2f} seconds")
        else:
            enriched_count = self.manager.enrich_empty_personas()
            print(f"✅ Successfully enriched {enriched_count} personas")
            
        return enriched_count
    
    def show_status(self) -> None:
        """Show database status"""
        print("📊 Database Status")
        print("=" * 50)
        
        try:
            # Get total personas
            from asociety.repository.database import get_current_db_path
            import sqlite3
            
            db_path = get_current_db_path()
            conn = sqlite3.connect(db_path)
            
            # Total personas
            cursor = conn.execute("SELECT COUNT(*) FROM persona")
            total_personas = cursor.fetchone()[0]
            
            # Personas with descriptions
            cursor = conn.execute("""
                SELECT COUNT(*) FROM persona 
                WHERE persona_desc IS NOT NULL 
                AND persona_desc != '' 
                AND TRIM(persona_desc) != ''
            """)
            with_desc = cursor.fetchone()[0]
            
            # Personas without descriptions
            without_desc = total_personas - with_desc
            
            conn.close()
            
            print(f"📁 Database: {db_path}")
            print(f"👥 Total personas: {total_personas}")
            print(f"📝 With descriptions: {with_desc}")
            print(f"📄 Without descriptions: {without_desc}")
            
            if total_personas > 0:
                completion_rate = (with_desc / total_personas) * 100
                print(f"📈 Completion rate: {completion_rate:.1f}%")
            
        except Exception as e:
            print(f"❌ Error getting status: {e}")
    
    def batch_operation(self, skeleton_count: int, enrich: bool = True, verbose: bool = False) -> None:
        """Perform batch operation: add skeletons then optionally enrich"""
        print(f"🔄 Starting batch operation...")
        print(f"   - Adding {skeleton_count} skeleton personas")
        if enrich:
            print(f"   - Enriching all empty personas")
        
        # Step 1: Add skeletons
        print("\n📝 Step 1: Adding skeleton personas")
        added_count = self.add_skeletons(skeleton_count, verbose)
        
        if enrich:
            # Step 2: Enrich empty personas
            print("\n🎨 Step 2: Enriching personas")
            enriched_count = self.enrich_empty(verbose)
            
            print(f"\n🎉 Batch operation completed!")
            print(f"   ✅ Added: {added_count} skeleton personas")
            print(f"   ✅ Enriched: {enriched_count} personas")
        else:
            print(f"\n🎉 Skeleton addition completed!")
            print(f"   ✅ Added: {added_count} skeleton personas")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Persona Manager CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add-skeletons --count 10 --verbose
  %(prog)s enrich-empty --verbose
  %(prog)s batch --skeletons 20 --no-enrich
  %(prog)s status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add skeletons command
    add_parser = subparsers.add_parser('add-skeletons', help='Add skeleton personas')
    add_parser.add_argument('--count', '-c', type=int, required=True,
                           help='Number of skeleton personas to add')
    add_parser.add_argument('--verbose', '-v', action='store_true',
                           help='Show detailed progress')
    
    # Enrich empty command
    enrich_parser = subparsers.add_parser('enrich-empty', help='Enrich personas without descriptions')
    enrich_parser.add_argument('--verbose', '-v', action='store_true',
                              help='Show detailed progress')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show database status')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch operation: add skeletons and enrich')
    batch_parser.add_argument('--skeletons', '-s', type=int, required=True,
                             help='Number of skeleton personas to add')
    batch_parser.add_argument('--no-enrich', action='store_true',
                             help='Skip enrichment step')
    batch_parser.add_argument('--verbose', '-v', action='store_true',
                             help='Show detailed progress')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = PersonaCLI()
    
    try:
        if args.command == 'add-skeletons':
            cli.add_skeletons(args.count, args.verbose)
            
        elif args.command == 'enrich-empty':
            cli.enrich_empty(args.verbose)
            
        elif args.command == 'status':
            cli.show_status()
            
        elif args.command == 'batch':
            cli.batch_operation(
                skeleton_count=args.skeletons,
                enrich=not args.no_enrich,
                verbose=args.verbose
            )
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
