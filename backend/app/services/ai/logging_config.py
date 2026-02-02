"""
Production-Grade Logging Configuration

Implements industry-standard logging with:
- Separate console and file handlers with different log levels
- Rotating file handlers to prevent unbounded log growth
- Structured logging for metrics and performance tracking
- Configurable thresholds for performance monitoring
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Log directory
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs" / "ai_services"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log file paths
MAIN_LOG_FILE = LOG_DIR / "ai_services.log"
PERFORMANCE_LOG_FILE = LOG_DIR / "ai_services_performance.log"
ERROR_LOG_FILE = LOG_DIR / "ai_services_errors.log"

# Logging levels
CONSOLE_LOG_LEVEL = logging.INFO  # Console only shows INFO and above (no DEBUG timing spam)
FILE_LOG_LEVEL = logging.DEBUG  # File captures everything including DEBUG
ERROR_LOG_LEVEL = logging.WARNING  # Error file captures warnings and errors

# Log format
CONSOLE_FORMAT = "%(name)s - %(levelname)s - %(message)s"
FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s"
PERFORMANCE_FORMAT = "%(asctime)s - %(name)s - %(message)s"

# Performance tuning threshold (in seconds) for logging slow operations
SLOW_OPERATION_THRESHOLD = 0.05


def setup_logging() -> logging.Logger:
    """
    Configure production-grade logging with multiple handlers.
    
    Returns:
        Configured root logger for AI services
    """
    root_logger = logging.getLogger("ai_services")
    root_logger.setLevel(logging.DEBUG)  # Capture all levels at root
    
    # Prevent duplicate handlers if called multiple times
    if root_logger.handlers:
        return root_logger
    
    # ========================================================================
    # Console Handler (INFO and above - clean output for terminals)
    # ========================================================================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(CONSOLE_LOG_LEVEL)
    console_formatter = logging.Formatter(CONSOLE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # ========================================================================
    # Main Log File Handler (DEBUG and above - all details)
    # Rotating handler: max 10MB per file, keep 5 backup files
    # ========================================================================
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            MAIN_LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,  # Keep 5 old files
            encoding='utf-8'
        )
        file_handler.setLevel(FILE_LOG_LEVEL)
        file_formatter = logging.Formatter(FILE_FORMAT)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create main log file handler: {e}")
    
    # ========================================================================
    # Performance Log Handler (dedicated performance metrics file)
    # Rotating handler: max 5MB per file, keep 3 backup files
    # ========================================================================
    try:
        perf_handler = logging.handlers.RotatingFileHandler(
            PERFORMANCE_LOG_FILE,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.DEBUG)
        perf_formatter = logging.Formatter(PERFORMANCE_FORMAT)
        perf_handler.setFormatter(perf_formatter)
        
        # Performance logger - only captures TIMING messages
        perf_logger = logging.getLogger("ai_services.performance")
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.DEBUG)
        perf_logger.propagate = False
    except Exception as e:
        print(f"Warning: Could not create performance log handler: {e}")
    
    # ========================================================================
    # Error Log Handler (warnings and errors only)
    # Rotating handler: max 5MB per file, keep 10 backup files
    # ========================================================================
    try:
        error_handler = logging.handlers.RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(ERROR_LOG_LEVEL)
        error_formatter = logging.Formatter(FILE_FORMAT)
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)
    except Exception as e:
        print(f"Warning: Could not create error log handler: {e}")
    
    return root_logger


# ============================================================================
# METRICS COLLECTION CLASS
# ============================================================================

class PerformanceMetrics:
    """
    Collects and aggregates performance metrics for AI operations.
    Useful for end-of-run summaries and performance monitoring.
    """
    
    def __init__(self):
        self.metrics = {}
        self.operation_times = {}
    
    def record_operation(self, operation_name: str, duration_ms: float):
        """
        Record the execution time for an operation.
        
        Args:
            operation_name: Name of the operation (e.g., "model.encode")
            duration_ms: Execution time in milliseconds
        """
        if operation_name not in self.operation_times:
            self.operation_times[operation_name] = []
        self.operation_times[operation_name].append(duration_ms)
    
    def get_summary(self) -> dict:
        """
        Get statistical summary of all recorded operations.
        
        Returns:
            Dictionary with min, max, avg, count for each operation
        """
        summary = {}
        for op_name, times in self.operation_times.items():
            if times:
                summary[op_name] = {
                    "count": len(times),
                    "total_ms": sum(times),
                    "avg_ms": sum(times) / len(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                }
        return summary
    
    def log_summary(self, logger: logging.Logger):
        """
        Log performance summary to logger.
        
        Args:
            logger: Logger instance to write summary to
        """
        summary = self.get_summary()
        if not summary:
            return
        
        logger.info("=" * 80)
        logger.info("PERFORMANCE SUMMARY")
        logger.info("=" * 80)
        for op_name, stats in summary.items():
            logger.info(
                f"{op_name}: "
                f"count={stats['count']}, "
                f"total={stats['total_ms']:.2f}ms, "
                f"avg={stats['avg_ms']:.2f}ms, "
                f"min={stats['min_ms']:.2f}ms, "
                f"max={stats['max_ms']:.2f}ms"
            )
        logger.info("=" * 80)
    
    def clear(self):
        """Reset all metrics."""
        self.operation_times.clear()


# ============================================================================
# INITIALIZATION
# ============================================================================

# Initialize logging when module is imported
logger = setup_logging()
perf_logger = logging.getLogger("ai_services.performance")
metrics = PerformanceMetrics()

logger.info("AI Services logging initialized")
logger.info(f"Main log file: {MAIN_LOG_FILE}")
logger.info(f"Performance log file: {PERFORMANCE_LOG_FILE}")
logger.info(f"Error log file: {ERROR_LOG_FILE}")
