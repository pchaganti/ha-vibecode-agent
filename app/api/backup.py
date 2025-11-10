"""Backup/Restore API endpoints"""
from fastapi import APIRouter, HTTPException
import logging

from app.models.schemas import BackupRequest, RollbackRequest, Response
from app.services.git_manager import git_manager

router = APIRouter()
logger = logging.getLogger('ha_cursor_agent')

@router.post("/commit", response_model=Response)
async def create_backup(backup: BackupRequest):
    """
    Create backup (Git commit) of current state
    
    **Example:**
    ```json
    {
      "message": "Before installing climate control system"
    }
    ```
    """
    try:
        if not git_manager.enabled:
            raise HTTPException(status_code=400, detail="Git versioning is not enabled")
        
        commit_hash = await git_manager.commit_changes(backup.message)
        
        if not commit_hash:
            return Response(
                success=True,
                message="No changes to commit",
                data=None
            )
        
        logger.info(f"Created backup: {commit_hash}")
        
        return Response(
            success=True,
            message=f"Backup created: {commit_hash}",
            data={"commit_hash": commit_hash}
        )
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_history(limit: int = 20):
    """
    Get backup history (Git commits)
    
    Returns list of commits with details
    """
    try:
        if not git_manager.enabled:
            raise HTTPException(status_code=400, detail="Git versioning is not enabled")
        
        history = await git_manager.get_history(limit)
        
        return {
            "success": True,
            "count": len(history),
            "commits": history
        }
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rollback/{commit_hash}", response_model=Response)
async def rollback_to_commit_path(commit_hash: str):
    """
    Rollback configuration to specific commit (path parameter version)
    
    **⚠️ WARNING: This will overwrite current configuration!**
    
    **Example:**
    - POST `/api/backup/rollback/a1b2c3d4`
    """
    try:
        if not git_manager.enabled:
            raise HTTPException(status_code=400, detail="Git versioning is not enabled")
        
        result = await git_manager.rollback(commit_hash)
        
        logger.warning(f"Rolled back to: {commit_hash}")
        
        return Response(
            success=True,
            message=f"Rolled back to commit: {commit_hash}",
            data=result
        )
    except Exception as e:
        logger.error(f"Failed to rollback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rollback", response_model=Response)
async def rollback_to_commit_body(rollback: RollbackRequest):
    """
    Rollback configuration to specific commit (body parameter version)
    
    **⚠️ WARNING: This will overwrite current configuration!**
    
    **Example:**
    ```json
    {
      "commit_hash": "a1b2c3d4"
    }
    ```
    """
    # Delegate to path parameter version
    return await rollback_to_commit_path(rollback.commit_hash)

@router.get("/diff")
async def get_diff(
    commit1: str = None,
    commit2: str = None
):
    """
    Get diff between commits or current changes
    
    **Examples:**
    - `/api/backup/diff` - Current uncommitted changes
    - `/api/backup/diff?commit1=a1b2c3d4` - Changes since commit
    - `/api/backup/diff?commit1=a1b2c3d4&commit2=e5f6g7h8` - Between two commits
    """
    try:
        if not git_manager.enabled:
            raise HTTPException(status_code=400, detail="Git versioning is not enabled")
        
        diff = await git_manager.get_diff(commit1, commit2)
        
        return {
            "success": True,
            "diff": diff
        }
    except Exception as e:
        logger.error(f"Failed to get diff: {e}")
        raise HTTPException(status_code=500, detail=str(e))

