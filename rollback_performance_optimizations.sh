#!/bin/bash
# Quick rollback script for performance optimizations

echo "🔄 Performance Optimization Rollback"
echo "====================================="

echo "Choose rollback option:"
echo "1. Rollback via git (recommended)"
echo "2. Disable optimizations via feature flags"
echo "3. Show current performance status"
echo "4. Cancel"

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "🔄 Rolling back via git..."
        echo "Current branch: $(git branch --show-current)"
        echo "Recent commits:"
        git log --oneline -5
        echo ""
        read -p "Rollback to main branch? (y/N): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            git checkout main
            echo "✅ Rolled back to main branch"
            echo "Performance optimizations disabled"
        else
            echo "Rollback cancelled"
        fi
        ;;
    2)
        echo "🏗️ Disabling optimizations via feature flags..."
        if [ -f "app/config/performance_config.py" ]; then
            sed -i.bak 's/PERFORMANCE_OPTIMIZATIONS_ENABLED = True/PERFORMANCE_OPTIMIZATIONS_ENABLED = False/' app/config/performance_config.py
            echo "✅ Performance optimizations disabled in config"
            echo "Restart the app for changes to take effect"
        else
            echo "❌ Performance config not found"
        fi
        ;;
    3)
        echo "📊 Current performance status:"
        if [ -f "performance_test_sms.py" ]; then
            python performance_test_sms.py | grep -E "(Router creation|Services reused|EXCELLENT|GOOD|OK|SLOW)"
        else
            echo "Performance test not available"
        fi
        echo ""
        echo "Current branch: $(git branch --show-current)"
        ;;
    4)
        echo "Rollback cancelled"
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
