#!/bin/bash

# Emergency Rollback Script
# Quickly rollback to the last known working deployment

set -e

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

echo "🚨 EMERGENCY ROLLBACK SCRIPT"
echo "============================="

# Check if we're in the backend directory
if [ ! -f "application.py" ]; then
    if [ -d "backend" ]; then
        cd backend
    else
        print_error "Cannot find backend directory or application.py"
        exit 1
    fi
fi

# Check EB CLI availability
if ! command -v eb &> /dev/null; then
    print_error "EB CLI not found. Please install AWS EB CLI first."
    exit 1
fi

print_status "Current EB environment status:"
eb status

# Get list of recent deployments
print_status "Recent deployments:"
eb logs --all | grep "Deployed" | tail -5 || true

# Ask user which version to rollback to
echo ""
print_warning "This will rollback your current deployment!"
read -p "Do you want to see available versions? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Available application versions:"
    aws elasticbeanstalk describe-application-versions \
        --application-name passport-photo-budget \
        --query 'ApplicationVersions[*].[VersionLabel,DateCreated]' \
        --output table | head -20
fi

echo ""
read -p "Enter version label to rollback to (or press Enter to rollback to previous): " VERSION_LABEL

if [ -z "$VERSION_LABEL" ]; then
    print_status "Rolling back to previous version..."
    eb deploy --version-label $(aws elasticbeanstalk describe-environments \
        --environment-names passport-photo-free \
        --query 'Environments[0].VersionLabel' \
        --output text)
else
    print_status "Rolling back to version: $VERSION_LABEL"
    eb deploy --version-label "$VERSION_LABEL"
fi

if [ $? -eq 0 ]; then
    print_success "✅ Rollback completed successfully"
    
    # Test the rolled back deployment
    print_status "Testing rolled back deployment..."
    sleep 30
    
    EB_URL=$(eb status | grep "CNAME:" | awk '{print $2}')
    
    if curl -s "https://$EB_URL/api/health" | grep -q '"status":"healthy"'; then
        print_success "✅ Rolled back application is healthy"
    else
        print_error "❌ Rolled back application health check failed"
        print_warning "You may need to investigate further or rollback to an earlier version"
    fi
else
    print_error "❌ Rollback failed"
    exit 1
fi

echo ""
print_success "🎉 Rollback process completed!"
print_status "Application URL: https://$EB_URL"