#!/usr/bin/env python3
"""
AWS Cost Monitoring Script
Checks current month's spending to ensure we stay under $10
"""

import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal

def check_current_costs():
    """Check current month's AWS costs"""
    try:
        # Create Cost Explorer client
        ce_client = boto3.client('ce', region_name='us-east-1')
        
        # Get current month dates
        today = datetime.now()
        start_of_month = today.replace(day=1).strftime('%Y-%m-%d')
        end_of_month = today.strftime('%Y-%m-%d')
        
        # Get cost and usage
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_of_month,
                'End': end_of_month
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        print("💰 AWS COST REPORT")
        print("=" * 40)
        print(f"📅 Period: {start_of_month} to {end_of_month}")
        
        total_cost = Decimal('0')
        
        if response['ResultsByTime']:
            for group in response['ResultsByTime'][0]['Groups']:
                service = group['Keys'][0]
                cost = Decimal(group['Metrics']['BlendedCost']['Amount'])
                if cost > 0:
                    print(f"💸 {service}: ${cost:.2f}")
                    total_cost += cost
        
        print("-" * 40)
        print(f"💵 Total Cost This Month: ${total_cost:.2f}")
        print(f"🎯 Budget Remaining: ${Decimal('10.00') - total_cost:.2f}")
        
        # Budget warnings
        if total_cost > Decimal('10.00'):
            print("🚨 BUDGET EXCEEDED! Consider shutting down resources.")
        elif total_cost > Decimal('8.00'):
            print("⚠️  WARNING: Approaching budget limit!")
        elif total_cost > Decimal('5.00'):
            print("📊 NOTICE: Over 50% of budget used.")
        else:
            print("✅ GOOD: Well within budget limits.")
        
        return float(total_cost)
        
    except Exception as e:
        print(f"❌ Error checking costs: {e}")
        print("💡 Make sure you have Cost Explorer permissions")
        return None

def check_free_tier_usage():
    """Check free tier usage (simplified)"""
    print("\n🆓 FREE TIER USAGE ESTIMATES")
    print("=" * 40)
    
    try:
        # EC2 usage (Elastic Beanstalk)
        ec2_client = boto3.client('ec2', region_name='us-east-1')
        instances = ec2_client.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']},
                {'Name': 'instance-type', 'Values': ['t3.micro', 't2.micro']}
            ]
        )
        
        running_instances = 0
        for reservation in instances['Reservations']:
            running_instances += len(reservation['Instances'])
        
        print(f"🖥️  Running t3.micro instances: {running_instances}")
        
        if running_instances > 0:
            hours_used_estimate = running_instances * 24 * datetime.now().day
            free_tier_hours = 750
            print(f"⏰ Estimated hours used this month: {hours_used_estimate}")
            print(f"🆓 Free tier hours remaining: {max(0, free_tier_hours - hours_used_estimate)}")
            
            if hours_used_estimate > free_tier_hours:
                print("⚠️  WARNING: May exceed free tier hours!")
        
    except Exception as e:
        print(f"❌ Error checking free tier: {e}")

def main():
    """Main cost checking function"""
    print("🔍 CHECKING AWS COSTS AND USAGE")
    print("=" * 50)
    
    current_cost = check_current_costs()
    check_free_tier_usage()
    
    print("\n📋 COST OPTIMIZATION TIPS:")
    print("- Keep only 1 t3.micro instance running")
    print("- Use single-instance Elastic Beanstalk (no load balancer)")
    print("- Stay under 200 emails/day with SES")
    print("- Monitor data transfer (100GB free/month)")
    print("- Delete unused resources regularly")
    
    print("\n🔧 IF COSTS ARE HIGH:")
    print("1. Check for unexpected resources in AWS Console")
    print("2. Stop/terminate unused instances")
    print("3. Delete unused load balancers")
    print("4. Check data transfer usage")
    
    if current_cost and current_cost > 8:
        print("\n🚨 IMMEDIATE ACTION NEEDED:")
        print("- Review all running resources")
        print("- Consider shutting down non-essential services")
        print("- Check for data transfer spikes")

if __name__ == "__main__":
    main()