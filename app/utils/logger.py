"""Logging utilities"""
import logging
import sys
from datetime import datetime
from pathlib import Path

# Store logs in memory for API access
LOG_BUFFER = []
MAX_LOG_SIZE = 1000

class BufferHandler(logging.Handler):
    """Custom handler to store logs in memory"""
    def emit(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": self.format(record),
            "module": record.module
        }
        LOG_BUFFER.append(log_entry)
        
        # Keep only last MAX_LOG_SIZE entries
        if len(LOG_BUFFER) > MAX_LOG_SIZE:
            LOG_BUFFER.pop(0)

def setup_logger(name: str, level: str = 'INFO'):
    """Setup logger with console and buffer handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level))
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Buffer handler
    buffer_handler = BufferHandler()
    buffer_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(buffer_handler)
    
    return logger

def get_logs(limit: int = 100, level: str = None):
    """Get logs from buffer"""
    logs = LOG_BUFFER[-limit:]
    
    if level:
        logs = [log for log in logs if log['level'] == level.upper()]
    
    return logs

