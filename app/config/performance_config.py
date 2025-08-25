# Performance Optimization Configuration

# Set to False to disable performance optimizations and use legacy code paths
# This allows instant rollback if any optimization causes issues

# Background integrity checks (moved out of SMS processing)
ENABLE_BACKGROUND_INTEGRITY = True

# Singleton services (reuse service instances instead of creating new ones)
ENABLE_SINGLETON_SERVICES = True

# Reduced AI timeouts (8s instead of 30s)
ENABLE_FAST_AI_TIMEOUT = True

# Performance monitoring (log SMS processing times)
ENABLE_PERFORMANCE_MONITORING = True

# Quick rollback: Set to False to disable all optimizations
PERFORMANCE_OPTIMIZATIONS_ENABLED = True
