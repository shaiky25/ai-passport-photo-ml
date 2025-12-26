#!/bin/bash

echo "🔧 Fixing Amplify App Deletion Issue"
echo "===================================="
echo "App: app3848"
echo "Issue: Domain in PENDING_VERIFICATION status"
echo ""

# Get the app ID
APP_ID="app3848"

echo "🔍 Checking current app status..."
aws amplify get-app --app-id $APP_ID --query 'app.[name,appId,defaultDomain]' --output table 2>/dev/null || echo "App not found or access issue"

echo ""
echo "🌐 Listing domains for the app..."
aws amplify list-domain-associations --app-id $APP_ID --query 'domainAssociations[*].[domainName,domainStatus]' --output table 2>/dev/null || echo "No domains or access issue"

echo ""
echo "🗑️  Step 1: Remove domain associations first..."

# List and remove domain associations
DOMAINS=$(aws amplify list-domain-associations --app-id $APP_ID --query 'domainAssociations[*].domainName' --output text 2>/dev/null)

if [ ! -z "$DOMAINS" ]; then
    for domain in $DOMAINS; do
        echo "Removing domain: $domain"
        aws amplify delete-domain-association --app-id $APP_ID --domain-name $domain
        if [ $? -eq 0 ]; then
            echo "✅ Domain $domain removed successfully"
        else
            echo "❌ Failed to remove domain $domain"
        fi
    done
else
    echo "No domains found to remove"
fi

echo ""
echo "⏳ Waiting 30 seconds for domain removal to propagate..."
sleep 30

echo ""
echo "🗑️  Step 2: Delete the app..."
aws amplify delete-app --app-id $APP_ID

if [ $? -eq 0 ]; then
    echo "✅ App $APP_ID deleted successfully!"
else
    echo "❌ Failed to delete app. Try manual deletion in console."
fi

echo ""
echo "🎯 Alternative: Manual Deletion Steps"
echo "1. Go to: https://console.aws.amazon.com/amplify/"
echo "2. Select app: $APP_ID"
echo "3. Go to 'Domain management'"
echo "4. Delete all domains first"
echo "5. Wait 5-10 minutes"
echo "6. Go back to app overview"
echo "7. Click 'Actions' → 'Delete app'"