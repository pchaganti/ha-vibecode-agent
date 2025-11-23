"""Git versioning manager"""
import os
import git
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger('ha_cursor_agent')

class GitManager:
    """Manages Git versioning for config files"""
    
    def __init__(self):
        self.config_path = Path(os.getenv('CONFIG_PATH', '/config'))
        self.enabled = os.getenv('ENABLE_GIT', 'false').lower() == 'true'
        self.auto_backup = os.getenv('AUTO_BACKUP', 'true').lower() == 'true'
        self.max_backups = int(os.getenv('MAX_BACKUPS', '50'))
        self.repo = None
        self.processing_request = False  # Flag to disable auto-commits during request processing
        
        if self.enabled:
            self._init_repo()
    
    def _init_repo(self):
        """Initialize Git repository"""
        try:
            if (self.config_path / '.git').exists():
                self.repo = git.Repo(self.config_path)
                logger.info("Git repository loaded")
            else:
                self.repo = git.Repo.init(self.config_path)
                self.repo.config_writer().set_value("user", "name", "HA Cursor Agent").release()
                self.repo.config_writer().set_value("user", "email", "agent@homeassistant.local").release()
                logger.info("Git repository initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Git: {e}")
            self.enabled = False
    
    async def commit_changes(self, message: str = None, skip_if_processing: bool = False) -> Optional[str]:
        """Commit current changes"""
        if not self.enabled or not self.repo:
            return None
        
        # Skip auto-commits if processing a request (unless explicitly requested)
        if skip_if_processing and self.processing_request:
            logger.debug("Skipping auto-commit - request processing in progress")
            return None
        
        try:
            # Check if there are changes
            if not self.repo.is_dirty(untracked_files=True):
                logger.debug("No changes to commit")
                return None
            
            # Add all changes
            self.repo.git.add(A=True)
            
            # Create commit message
            if not message:
                message = f"Auto-commit by HA Cursor Agent at {datetime.now().isoformat()}"
            
            # Commit
            commit = self.repo.index.commit(message)
            commit_hash = commit.hexsha[:8]
            
            logger.info(f"Committed changes: {commit_hash} - {message}")
            
            # Cleanup old commits if needed
            await self._cleanup_old_commits()
            
            return commit_hash
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            return None
    
    async def create_checkpoint(self, user_request: str) -> Dict:
        """Create checkpoint with tag at the start of user request processing"""
        if not self.enabled or not self.repo:
            return {
                "success": False,
                "message": "Git versioning not enabled",
                "commit_hash": None,
                "tag": None
            }
        
        try:
            # Commit current state first (if there are changes)
            commit_hash = await self.commit_changes(
                f"Checkpoint before: {user_request}",
                skip_if_processing=False
            )
            
            # If no changes, get current HEAD
            if not commit_hash:
                try:
                    commit_hash = self.repo.head.commit.hexsha[:8]
                except:
                    commit_hash = None
            
            # Create tag with timestamp and description
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tag_name = f"checkpoint_{timestamp}"
            tag_message = f"Checkpoint before: {user_request}"
            
            # Create tag
            if commit_hash:
                try:
                    # Use HEAD for tag creation (commit_hash is already committed)
                    tag = self.repo.create_tag(
                        tag_name,
                        ref="HEAD",
                        message=tag_message
                    )
                    logger.info(f"Created checkpoint tag: {tag_name} - {tag_message}")
                except Exception as e:
                    logger.warning(f"Failed to create tag (may already exist): {e}")
                    tag = None
            else:
                try:
                    # Try to create tag on HEAD even if no new commit
                    tag = self.repo.create_tag(
                        tag_name,
                        ref="HEAD",
                        message=tag_message
                    )
                    logger.info(f"Created checkpoint tag: {tag_name} - {tag_message}")
                except Exception as e:
                    logger.warning(f"Failed to create tag: {e}")
                    tag = None
            
            # Set flag to disable auto-commits during request processing
            self.processing_request = True
            
            return {
                "success": True,
                "message": f"Checkpoint created: {tag_name}",
                "commit_hash": commit_hash,
                "tag": tag_name,
                "timestamp": timestamp
            }
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            return {
                "success": False,
                "message": f"Failed to create checkpoint: {e}",
                "commit_hash": None,
                "tag": None
            }
    
    def end_request_processing(self):
        """End request processing - re-enable auto-commits"""
        self.processing_request = False
        logger.debug("Request processing ended - auto-commits re-enabled")
    
    async def _cleanup_old_commits(self):
        """Remove old commits to save space"""
        try:
            commits = list(self.repo.iter_commits())
            if len(commits) > self.max_backups:
                # Keep only recent commits (Git will handle cleanup)
                logger.info(f"Repository has {len(commits)} commits, max is {self.max_backups}")
        except Exception as e:
            logger.error(f"Failed to cleanup commits: {e}")
    
    async def get_history(self, limit: int = 20) -> List[Dict]:
        """Get commit history"""
        if not self.enabled or not self.repo:
            return []
        
        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=limit):
                commits.append({
                    "hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": datetime.fromtimestamp(commit.committed_date).isoformat(),
                    "files_changed": len(commit.stats.files)
                })
            return commits
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []
    
    async def rollback(self, commit_hash: str) -> Dict:
        """Rollback to specific commit"""
        if not self.enabled or not self.repo:
            raise Exception("Git versioning not enabled")
        
        try:
            # Commit current state before rollback
            await self.commit_changes(f"Before rollback to {commit_hash}")
            
            # Reset to commit
            self.repo.git.reset('--hard', commit_hash)
            
            logger.info(f"Rolled back to commit: {commit_hash}")
            
            return {
                "success": True,
                "commit": commit_hash,
                "message": f"Rolled back to {commit_hash}"
            }
        except Exception as e:
            logger.error(f"Failed to rollback: {e}")
            raise Exception(f"Rollback failed: {e}")
    
    async def get_diff(self, commit1: str = None, commit2: str = None) -> str:
        """Get diff between commits or current changes"""
        if not self.enabled or not self.repo:
            return ""
        
        try:
            if commit1 and commit2:
                diff = self.repo.git.diff(commit1, commit2)
            elif commit1:
                diff = self.repo.git.diff(commit1, 'HEAD')
            else:
                diff = self.repo.git.diff('HEAD')
            
            return diff
        except Exception as e:
            logger.error(f"Failed to get diff: {e}")
            return ""

# Global instance
git_manager = GitManager()

