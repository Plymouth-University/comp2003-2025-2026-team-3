"""
Quick diagnostic script to verify logging system imports
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    print("Testing logging_config imports...")
    from app.services.ai.logging_config import (
        setup_logging, 
        logger, 
        perf_logger, 
        metrics,
        SLOW_OPERATION_THRESHOLD,
        LOG_DIR
    )
    print("✓ logging_config imports successful")
    print(f"  - setup_logging: {setup_logging}")
    print(f"  - logger: {logger}")
    print(f"  - perf_logger: {perf_logger}")
    print(f"  - metrics: {metrics}")
    print(f"  - SLOW_OPERATION_THRESHOLD: {SLOW_OPERATION_THRESHOLD}")
    print(f"  - LOG_DIR: {LOG_DIR}")
    
    print("\nTesting config imports...")
    from app.services.ai.config import (
        CATEGORY_DEFINITIONS,
        CATEGORY_KEYWORDS,
        CATEGORY_LABELS,
        SLOW_OPERATION_THRESHOLD as CONFIG_THRESHOLD,
        MIN_KEYWORD_MATCHES
    )
    print("✓ config imports successful")
    print(f"  - CATEGORY_DEFINITIONS: {len(CATEGORY_DEFINITIONS)} configured")
    print(f"  - CATEGORY_LABELS: {list(CATEGORY_LABELS.values())}")
    print(f"  - CONFIG_THRESHOLD: {CONFIG_THRESHOLD}")
    print(f"  - MIN_KEYWORD_MATCHES: {MIN_KEYWORD_MATCHES}")
    
    print("\n✓ ALL IMPORTS SUCCESSFUL - Logging system is ready!")
    
except ImportError as e:
    print(f"✗ Import Error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
