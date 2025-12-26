#!/bin/bash

# Deployment Pipeline with Integrated Testing
# This script ensures all tests pass before deploying to AWS Elastic Beanstalk

set -e  # Exit on any error

echo "🚀 Starting Deployment Pipeline with Integrated Testing"
echo "======================================================"

# Configuration
BACKEND_DIR="backend"
TEST_TIMEOUT=120
DEPLOYMENT_VERSION=$(date +"%y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Pre-deployment checks
print_status "Step 1: Pre-deployment checks"
echo "-------------------------------"

# Check if we're in the right directory
if [ ! -d "$BACKEND_DIR" ]; then
    print_error "Backend directory not found. Please run from project root."
    exit 1
fi

# Check if EB CLI is available
if ! command -v eb &> /dev/null; then
    print_error "EB CLI not found. Please install AWS EB CLI first."
    exit 1
fi

# Check if we're in a git repository (optional but recommended)
if [ -d ".git" ]; then
    print_status "Git repository detected. Checking for uncommitted changes..."
    if ! git diff-index --quiet HEAD --; then
        print_warning "You have uncommitted changes. Consider committing before deployment."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Deployment cancelled by user."
            exit 1
        fi
    fi
fi

print_success "Pre-deployment checks passed"

# Step 2: Comprehensive test suite execution
print_status "Step 2: Comprehensive test suite execution"
echo "--------------------------------------------"

print_status "Running all registered tests via test manager..."
if python test_manager.py > test_manager_results.log 2>&1; then
    # Check if all required tests passed
    if grep -q "🎉 ALL REQUIRED TESTS PASSED!" test_manager_results.log; then
        print_success "✅ All required tests passed"
        
        # Show test summary
        echo "Test Summary:"
        grep -E "Total Tests:|Passed:|Failed:|Required Tests:|Required Passed:|Required Failed:" test_manager_results.log
        
        # Show any optional test warnings
        if grep -q "⚠️ Failed Optional Tests:" test_manager_results.log; then
            print_warning "Some optional tests failed (deployment will continue)"
            grep -A 10 "⚠️ Failed Optional Tests:" test_manager_results.log
        fi
        
    else
        print_error "❌ Required tests FAILED"
        echo "Test manager output:"
        cat test_manager_results.log
        exit 1
    fi
else
    print_error "❌ Test manager execution FAILED"
    echo "Test manager output:"
    cat test_manager_results.log
    exit 1
fi

# Step 3: Start local test server
print_status "Step 3: Starting local test server"
echo "-----------------------------------"

cd $BACKEND_DIR

# Kill any existing server processes
pkill -f "python application.py" || true
sleep 2

# Start server in background
print_status "Starting Flask application..."
python application.py &
SERVER_PID=$!

# Wait for server to start
print_status "Waiting for server to start..."
sleep 8

# Check if server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    print_error "Failed to start Flask application"
    exit 1
fi

# Test server health
print_status "Testing server health..."
if curl -s http://127.0.0.1:5000/api/health > /dev/null; then
    print_success "Server is healthy and responding"
else
    print_error "Server health check failed"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Step 4: Legacy individual tests (for backward compatibility)
print_status "Step 4: Legacy individual tests (for backward compatibility)"
echo "------------------------------------------------------------"

cd ..  # Back to project root

# Note: These individual tests are now managed by test_manager.py
# but kept here for backward compatibility during transition

print_success "Individual tests now managed by test_manager.py"

# Clean up test server
print_status "Stopping test server..."
kill $SERVER_PID 2>/dev/null || true
sleep 2

print_success "All tests passed successfully!"

# Step 5: Create deployment backup
print_status "Step 5: Creating deployment backup"
echo "-----------------------------------"

BACKUP_DIR="deployment_backup_${DEPLOYMENT_VERSION}"
print_status "Creating backup: $BACKUP_DIR"

cp -r $BACKEND_DIR $BACKUP_DIR
print_success "Backup created: $BACKUP_DIR"

# Step 6: Deploy to Elastic Beanstalk
print_status "Step 6: Deploying to AWS Elastic Beanstalk"
echo "--------------------------------------------"

cd $BACKEND_DIR

# Check EB environment status
print_status "Checking current EB environment status..."
eb status

print_status "Deploying version: app-$DEPLOYMENT_VERSION"

# Deploy with version label
if eb deploy --label "app-$DEPLOYMENT_VERSION" --timeout 20; then
    print_success "✅ Deployment to Elastic Beanstalk SUCCESSFUL"
else
    print_error "❌ Deployment to Elastic Beanstalk FAILED"
    cd ..
    print_status "Backup available at: $BACKUP_DIR"
    exit 1
fi

# Step 7: Post-deployment validation
print_status "Step 7: Post-deployment validation"
echo "-----------------------------------"

# Get the EB environment URL
EB_URL=$(eb status | grep "CNAME:" | awk '{print $2}')

if [ -z "$EB_URL" ]; then
    print_error "Could not determine EB environment URL"
    exit 1
fi

print_status "Testing deployed application at: https://$EB_URL"

# Wait for deployment to be ready
print_status "Waiting for deployment to be ready..."
sleep 30

# Test deployed health endpoint
for i in {1..5}; do
    print_status "Health check attempt $i/5..."
    if curl -s "https://$EB_URL/api/health" | grep -q '"status":"healthy"'; then
        print_success "✅ Deployed application is healthy"
        break
    else
        if [ $i -eq 5 ]; then
            print_error "❌ Deployed application health check failed after 5 attempts"
            print_status "Consider rolling back deployment"
            exit 1
        fi
        sleep 10
    fi
done

# Test deployed pipeline config
if curl -s "https://$EB_URL/api/pipeline-config" | grep -q '"intelligent_cropping":true'; then
    print_success "✅ Deployed pipeline configuration is correct"
else
    print_error "❌ Deployed pipeline configuration test failed"
    exit 1
fi

# Step 8: Cleanup
print_status "Step 8: Cleanup"
echo "---------------"

cd ..

# Clean up test output files
rm -f test_results_*.log dependency_test_results.log region_check_results.log test_manager_results.log

print_success "Cleanup completed"

# Final success message
echo ""
echo "🎉 DEPLOYMENT PIPELINE COMPLETED SUCCESSFULLY! 🎉"
echo "=================================================="
echo ""
print_success "✅ All tests passed"
print_success "✅ Backup created: $BACKUP_DIR"
print_success "✅ Deployed version: app-$DEPLOYMENT_VERSION"
print_success "✅ Application URL: https://$EB_URL"
print_success "✅ Post-deployment validation passed"
echo ""
print_status "Your government-compliant passport photo application is now live!"
echo ""

exit 0