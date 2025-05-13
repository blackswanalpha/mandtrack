"""
Management command to clean up old log files and temporary files.
"""
import os
import time
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up old log files and temporary files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete files older than this many days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        self.stdout.write(f"Cleaning up files older than {days} days...")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No files will be deleted"))
        
        # Calculate cutoff time
        cutoff_time = time.time() - (days * 86400)  # 86400 seconds = 1 day
        
        # Clean up log files
        self._cleanup_logs(cutoff_time, dry_run)
        
        # Clean up temporary files
        self._cleanup_temp_files(cutoff_time, dry_run)
        
        # Clean up old media files (if configured)
        self._cleanup_old_media(cutoff_time, dry_run)
        
        self.stdout.write(self.style.SUCCESS("Cleanup completed successfully"))
    
    def _cleanup_logs(self, cutoff_time, dry_run):
        """Clean up old log files."""
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        if not os.path.exists(log_dir):
            self.stdout.write(f"Log directory {log_dir} does not exist, skipping")
            return
        
        self.stdout.write(f"Checking log files in {log_dir}")
        deleted_count = 0
        total_size = 0
        
        for filename in os.listdir(log_dir):
            file_path = os.path.join(log_dir, filename)
            
            # Skip if not a file
            if not os.path.isfile(file_path):
                continue
            
            # Check if file is old enough to delete
            file_time = os.path.getmtime(file_path)
            if file_time < cutoff_time:
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                if dry_run:
                    self.stdout.write(f"Would delete: {file_path} ({self._format_size(file_size)})")
                else:
                    try:
                        os.remove(file_path)
                        self.stdout.write(f"Deleted: {file_path} ({self._format_size(file_size)})")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error deleting {file_path}: {e}"))
                        continue
                
                deleted_count += 1
        
        action = "Would delete" if dry_run else "Deleted"
        self.stdout.write(f"{action} {deleted_count} log files ({self._format_size(total_size)})")
    
    def _cleanup_temp_files(self, cutoff_time, dry_run):
        """Clean up temporary files."""
        temp_dirs = [
            os.path.join(settings.BASE_DIR, 'tmp'),
            os.path.join(settings.BASE_DIR, 'temp'),
            os.path.join(settings.MEDIA_ROOT, 'temp'),
            os.path.join(settings.MEDIA_ROOT, 'tmp'),
        ]
        
        deleted_count = 0
        total_size = 0
        
        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue
            
            self.stdout.write(f"Checking temporary files in {temp_dir}")
            
            for root, dirs, files in os.walk(temp_dir):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    
                    # Check if file is old enough to delete
                    file_time = os.path.getmtime(file_path)
                    if file_time < cutoff_time:
                        file_size = os.path.getsize(file_path)
                        total_size += file_size
                        
                        if dry_run:
                            self.stdout.write(f"Would delete: {file_path} ({self._format_size(file_size)})")
                        else:
                            try:
                                os.remove(file_path)
                                self.stdout.write(f"Deleted: {file_path} ({self._format_size(file_size)})")
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"Error deleting {file_path}: {e}"))
                                continue
                        
                        deleted_count += 1
        
        action = "Would delete" if dry_run else "Deleted"
        self.stdout.write(f"{action} {deleted_count} temporary files ({self._format_size(total_size)})")
    
    def _cleanup_old_media(self, cutoff_time, dry_run):
        """Clean up old media files that are no longer referenced."""
        # This is a placeholder for a more sophisticated media cleanup
        # In a real implementation, you would check the database to see if files are still referenced
        pass
    
    def _format_size(self, size_bytes):
        """Format file size in a human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
