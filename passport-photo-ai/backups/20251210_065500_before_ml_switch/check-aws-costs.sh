#!/bin/bash

echo "💰 AWS Free Tier Usage Check"
echo "=============================="

# Check current month costs
CURRENT_MONTH=$(date +%Y-%m)
START_DATE="${CURRENT_MONTH}-01"
END_DATE=$(date +%Y-%m-%d)

echo "📅 Checking costs from $START_DATE to $END_DATE"
echo ""

# Get cost breakdown by service
aws ce get-cost-and-usage \
    --time-period Start=$START_DATE,End=$END_DATE \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE \
    --query 'ResultsByTime[0].Groups[?Metrics.BlendedCost.Amount>`0`].[Keys[0],Metrics.BlendedCost.Amount]' \
    --output table

echo ""
echo "🎯 Free Tier Limits:"
echo "   • EC2 t3.micro: 750 hours/month"
echo "   • S3 Storage: 5 GB"
echo "   • CloudFront: 1 TB data transfer"
echo "   • Application Load Balancer: 750 hours/month"
echo ""
echo "💡 Tip: Set up billing alerts in AWS Console to monitor usage"