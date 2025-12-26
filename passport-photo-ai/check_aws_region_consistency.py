#!/usr/bin/env python3
"""
AWS Region Consistency Checker
Ensures all AWS resources are in the same region to avoid cross-region transfer costs
"""

import boto3
import json
import os
from botocore.exceptions import ClientError, NoCredentialsError

def check_region_consistency():
    """Check that all AWS resources are in the same region"""
    print("🌍 AWS REGION CONSISTENCY CHECKER")
    print("=" * 50)
    
    # Expected region (from our configuration)
    expected_region = 'us-east-1'
    print(f"Expected region: {expected_region}")
    print()
    
    issues = []
    resources_checked = []
    
    try:
        # 1. Check SES (Simple Email Service)
        print("🔍 Checking SES configuration...")
        try:
            ses_client = boto3.client('ses', region_name=expected_region)
            
            # Check if SES is configured in the expected region
            identities = ses_client.list_identities()
            if identities['Identities']:
                print(f"  ✅ SES identities found in {expected_region}: {len(identities['Identities'])}")
                resources_checked.append(f"SES ({expected_region})")
            else:
                print(f"  ⚠️ No SES identities found in {expected_region}")
                
        except ClientError as e:
            print(f"  ❌ SES check failed: {e}")
            issues.append(f"SES access error in {expected_region}")
        
        # 2. Check Elastic Beanstalk
        print("\n🔍 Checking Elastic Beanstalk configuration...")
        try:
            eb_client = boto3.client('elasticbeanstalk', region_name=expected_region)
            
            # List applications
            apps = eb_client.describe_applications()
            if apps['Applications']:
                for app in apps['Applications']:
                    app_name = app['ApplicationName']
                    print(f"  ✅ EB Application found: {app_name} in {expected_region}")
                    resources_checked.append(f"EB App: {app_name} ({expected_region})")
                    
                    # Check environments for this application
                    envs = eb_client.describe_environments(ApplicationName=app_name)
                    for env in envs['Environments']:
                        env_name = env['EnvironmentName']
                        env_status = env['Status']
                        print(f"    ✅ EB Environment: {env_name} ({env_status}) in {expected_region}")
                        resources_checked.append(f"EB Env: {env_name} ({expected_region})")
            else:
                print(f"  ⚠️ No EB applications found in {expected_region}")
                
        except ClientError as e:
            print(f"  ❌ EB check failed: {e}")
            issues.append(f"Elastic Beanstalk access error in {expected_region}")
        
        # 3. Check S3 buckets (EB creates buckets for deployments)
        print("\n🔍 Checking S3 buckets...")
        try:
            s3_client = boto3.client('s3', region_name=expected_region)
            
            # List buckets
            buckets = s3_client.list_buckets()
            eb_buckets = []
            
            for bucket in buckets['Buckets']:
                bucket_name = bucket['Name']
                
                # Check if it's an EB bucket
                if 'elasticbeanstalk' in bucket_name and expected_region in bucket_name:
                    try:
                        # Get bucket location
                        location = s3_client.get_bucket_location(Bucket=bucket_name)
                        bucket_region = location['LocationConstraint'] or 'us-east-1'  # us-east-1 returns None
                        
                        if bucket_region == expected_region:
                            print(f"  ✅ EB S3 Bucket: {bucket_name} in {bucket_region}")
                            resources_checked.append(f"S3: {bucket_name} ({bucket_region})")
                            eb_buckets.append(bucket_name)
                        else:
                            print(f"  ❌ EB S3 Bucket: {bucket_name} in {bucket_region} (expected {expected_region})")
                            issues.append(f"S3 bucket {bucket_name} in wrong region: {bucket_region}")
                            
                    except ClientError as e:
                        print(f"  ⚠️ Could not check bucket {bucket_name}: {e}")
            
            if not eb_buckets:
                print(f"  ⚠️ No Elastic Beanstalk S3 buckets found")
                
        except ClientError as e:
            print(f"  ❌ S3 check failed: {e}")
            issues.append(f"S3 access error")
        
        # 4. Check CloudWatch Logs (EB uses CloudWatch)
        print("\n🔍 Checking CloudWatch Logs...")
        try:
            logs_client = boto3.client('logs', region_name=expected_region)
            
            # Look for EB-related log groups
            log_groups = logs_client.describe_log_groups()
            eb_log_groups = []
            
            for log_group in log_groups['logGroups']:
                log_group_name = log_group['logGroupName']
                if 'aws/elasticbeanstalk' in log_group_name:
                    print(f"  ✅ EB CloudWatch Log Group: {log_group_name} in {expected_region}")
                    resources_checked.append(f"CloudWatch: {log_group_name} ({expected_region})")
                    eb_log_groups.append(log_group_name)
            
            if not eb_log_groups:
                print(f"  ⚠️ No EB CloudWatch log groups found in {expected_region}")
                
        except ClientError as e:
            print(f"  ❌ CloudWatch Logs check failed: {e}")
            issues.append(f"CloudWatch Logs access error in {expected_region}")
        
        # 5. Check EC2 instances (EB creates EC2 instances)
        print("\n🔍 Checking EC2 instances...")
        try:
            ec2_client = boto3.client('ec2', region_name=expected_region)
            
            # Look for EB-related instances
            instances = ec2_client.describe_instances()
            eb_instances = []
            
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instance_state = instance['State']['Name']
                    
                    # Check if it's an EB instance
                    tags = instance.get('Tags', [])
                    is_eb_instance = any(tag.get('Key') == 'elasticbeanstalk:environment-name' for tag in tags)
                    
                    if is_eb_instance:
                        env_name = next((tag['Value'] for tag in tags if tag.get('Key') == 'elasticbeanstalk:environment-name'), 'unknown')
                        print(f"  ✅ EB EC2 Instance: {instance_id} ({instance_state}) for env '{env_name}' in {expected_region}")
                        resources_checked.append(f"EC2: {instance_id} ({expected_region})")
                        eb_instances.append(instance_id)
            
            if not eb_instances:
                print(f"  ⚠️ No EB EC2 instances found in {expected_region}")
                
        except ClientError as e:
            print(f"  ❌ EC2 check failed: {e}")
            issues.append(f"EC2 access error in {expected_region}")
        
        # Summary
        print("\n📊 REGION CONSISTENCY SUMMARY")
        print("=" * 50)
        
        print(f"Expected region: {expected_region}")
        print(f"Resources checked: {len(resources_checked)}")
        print(f"Issues found: {len(issues)}")
        
        if resources_checked:
            print("\n✅ Resources in correct region:")
            for resource in resources_checked:
                print(f"  • {resource}")
        
        if issues:
            print("\n❌ Issues found:")
            for issue in issues:
                print(f"  • {issue}")
            print("\n⚠️ CROSS-REGION TRANSFER COSTS MAY APPLY!")
            return False
        else:
            print("\n🎉 All AWS resources are in the same region!")
            print("✅ No cross-region transfer costs expected")
            return True
            
    except NoCredentialsError:
        print("❌ AWS credentials not found. Please configure AWS CLI.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def estimate_cross_region_costs():
    """Provide information about cross-region transfer costs"""
    print("\n💰 CROSS-REGION TRANSFER COST INFORMATION")
    print("=" * 50)
    print("AWS Cross-Region Data Transfer Costs (as of 2024):")
    print("• Data transfer OUT from us-east-1 to other US regions: $0.02/GB")
    print("• Data transfer OUT from us-east-1 to Europe/Asia: $0.09/GB")
    print("• Data transfer IN: FREE (to any region)")
    print()
    print("For a passport photo app processing 1000 photos/day:")
    print("• Average photo size: ~2MB")
    print("• Daily data transfer: ~2GB")
    print("• Monthly cross-region cost (US): ~$1.20")
    print("• Monthly cross-region cost (International): ~$5.40")
    print()
    print("💡 Best practice: Keep all resources in the same region!")

if __name__ == "__main__":
    success = check_region_consistency()
    
    if not success:
        estimate_cross_region_costs()
    
    exit(0 if success else 1)