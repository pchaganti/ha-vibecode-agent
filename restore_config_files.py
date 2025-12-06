#!/usr/bin/env python3
"""Script to restore Home Assistant configuration files from Git"""
import os
import sys
import subprocess
from pathlib import Path

# Configuration
CONFIG_PATH = os.getenv('CONFIG_PATH', '/config')
RESTORE_PATTERNS = [
    'configuration.yaml',
    'automations.yaml',
    'scripts.yaml',
    '*.yaml',
    '*.yml'
]

def restore_files_from_git(commit_hash=None, file_patterns=None):
    """Restore files from Git commit"""
    config_path = Path(CONFIG_PATH)
    git_dir = config_path / '.git'
    
    if not git_dir.exists():
        print(f"ERROR: Git repository not found at {CONFIG_PATH}")
        return False
    
    try:
        # Get HEAD commit if not specified
        if not commit_hash:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=str(config_path),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                print(f"ERROR: Cannot get HEAD commit: {result.stderr}")
                return False
            commit_hash = result.stdout.strip()
        
        print(f"Restoring files from commit {commit_hash}...")
        
        # Restore files
        if file_patterns:
            restored = []
            for pattern in file_patterns:
                # Get list of files matching pattern in commit
                result = subprocess.run(
                    ['git', 'ls-tree', '-r', '--name-only', commit_hash, pattern],
                    cwd=str(config_path),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
                    for file_path in files:
                        # Restore individual file
                        restore_result = subprocess.run(
                            ['git', 'checkout', commit_hash, '--', file_path],
                            cwd=str(config_path),
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        if restore_result.returncode == 0:
                            restored.append(file_path)
                            print(f"✅ Restored: {file_path}")
                        else:
                            print(f"❌ Failed to restore {file_path}: {restore_result.stderr}")
                else:
                    print(f"⚠️  No files found matching pattern: {pattern}")
            
            print(f"\n✅ Restored {len(restored)} files")
            return len(restored) > 0
        else:
            # Restore all tracked files
            result = subprocess.run(
                ['git', 'checkout', commit_hash, '--', '.'],
                cwd=str(config_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"ERROR: Failed to restore files: {result.stderr}")
                return False
            
            # Get list of restored files
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=str(config_path),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            restored_files = []
            if status_result.returncode == 0:
                for line in status_result.stdout.split('\n'):
                    if line.strip() and not line.startswith('??'):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            restored_files.append(parts[-1])
            
            print(f"\n✅ Restored {len(restored_files)} files from commit {commit_hash}")
            if restored_files:
                print("\nRestored files:")
                for f in restored_files[:20]:  # Show first 20
                    print(f"  - {f}")
                if len(restored_files) > 20:
                    print(f"  ... and {len(restored_files) - 20} more")
            
            return True
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Home Assistant Configuration Files Restore")
    print("=" * 60)
    print(f"Config path: {CONFIG_PATH}")
    print()
    
    # Try to restore YAML files
    success = restore_files_from_git(file_patterns=RESTORE_PATTERNS)
    
    if success:
        print("\n✅ Restore completed successfully!")
        print("\n⚠️  Note: You may need to restart Home Assistant for changes to take effect.")
    else:
        print("\n❌ Restore failed!")
        sys.exit(1)

