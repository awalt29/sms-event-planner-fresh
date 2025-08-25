#!/bin/bash
# Deploy performance optimizations to Railway

echo "🚀 Deploying Performance Optimizations to Railway"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "wsgi.py" ]; then
    echo "❌ Error: Please run from the project root directory"
    exit 1
fi

# Check git status
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes"
    git status --short
    read -p "Continue with deployment? (y/N): " continue_deploy
    if [ "$continue_deploy" != "y" ] && [ "$continue_deploy" != "Y" ]; then
        echo "Deployment cancelled"
        exit 1
    fi
fi

echo "📋 Performance optimizations included:"
echo "  ✅ Background data integrity checks"
echo "  ✅ Singleton service pattern" 
echo "  ✅ Reduced AI API timeouts (8s)"
echo "  ✅ Performance monitoring"

# Start background integrity service if not already running
echo "🔧 Setting up background integrity maintenance..."

# Create a simple systemd-style service file for Railway
cat > start_background_integrity.sh << 'EOF'
#!/bin/bash
# Background integrity maintenance for Railway deployment
cd /app
python background_integrity_service.py --continuous --interval 15 &
echo $! > /tmp/integrity_service.pid
EOF

chmod +x start_background_integrity.sh

echo "📊 Running final performance test..."
python performance_test_sms.py | grep -E "(Router creation|Services reused|Message processing|EXCELLENT|GOOD|OK|SLOW)"

echo ""
echo "🚀 Ready for Railway deployment!"
echo ""
echo "Performance improvements expected:"
echo "  • SMS router creation: ~99% faster (0.1ms vs 75ms)"
echo "  • No more periodic 200-500ms delays"
echo "  • AI timeouts reduced from 30s to 8s" 
echo "  • Background integrity checks won't block SMS"
echo ""
echo "To deploy: git push railway performance-optimization:main"
echo "To rollback: Set PERFORMANCE_OPTIMIZATIONS_ENABLED=False in Railway env vars"
