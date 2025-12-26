#!/usr/bin/env python3
"""
Verify SES configuration for the passport photo application
"""
import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError

def verify_ses_configuration():
    """Verify SES configuration step by step"""
    print("🔍 VERIFYING SES CONFIGURATION")
    print("=" * 60)
    
    try:
        # Initialize SES client
        ses_client = boto3.client('ses', region_name='us-east-1')
        print("✅ SES client initialized successfully")
        
        # Test 1: Check verified email addresses
        print("\n📧 Checking verified email addresses...")
        try:
            response = ses_client.list_verified_email_addresses()
            verified_emails = response.get('VerifiedEmailAddresses', [])
            
            print(f"  📋 Verified email addresses ({len(verified_emails)}):")
            for email in verified_emails:
                print(f"    ✅ {email}")
            
            # Check if our sender email is verified
            sender_email = "faiz.24365@gmail.com"  # From application.py
            if sender_email in verified_emails:
                print(f"  ✅ Sender email '{sender_email}' is verified")
            else:
                print(f"  ❌ Sender email '{sender_email}' is NOT verified")
                print(f"  💡 You need to verify this email in AWS SES console")
                
        except ClientError as e:
            print(f"  ❌ Error checking verified emails: {e}")
        
        # Test 2: Check SES sending quota
        print("\n📊 Checking SES sending quota...")
        try:
            response = ses_client.get_send_quota()
            max_24_hour = response.get('Max24HourSend', 0)
            max_send_rate = response.get('MaxSendRate', 0)
            sent_last_24_hours = response.get('SentLast24Hours', 0)
            
            print(f"  📈 Max emails per 24 hours: {max_24_hour}")
            print(f"  ⚡ Max send rate per second: {max_send_rate}")
            print(f"  📤 Sent in last 24 hours: {sent_last_24_hours}")
            
            if max_24_hour > 0:
                print(f"  ✅ SES sending quota is configured")
            else:
                print(f"  ❌ SES is in sandbox mode - need to request production access")
                
        except ClientError as e:
            print(f"  ❌ Error checking send quota: {e}")
        
        # Test 3: Check if we're in sandbox mode
        print("\n🏖️  Checking SES sandbox status...")
        try:
            # In sandbox mode, you can only send to verified addresses
            response = ses_client.get_account_sending_enabled()
            sending_enabled = response.get('Enabled', False)
            
            if sending_enabled:
                print(f"  ✅ Account sending is enabled")
            else:
                print(f"  ❌ Account sending is disabled")
                
            # Check if we can send to unverified addresses (production mode)
            test_email = "faiz.undefined@gmail.com"
            if test_email not in verified_emails and max_24_hour <= 200:
                print(f"  ⚠️  SES appears to be in sandbox mode")
                print(f"  💡 In sandbox mode, you can only send to verified email addresses")
                print(f"  💡 To send to '{test_email}', either:")
                print(f"      1. Verify '{test_email}' in SES console, OR")
                print(f"      2. Request production access for SES")
            
        except ClientError as e:
            print(f"  ❌ Error checking account status: {e}")
        
        # Test 4: Test sending an email
        print(f"\n📨 Testing email send to faiz.undefined@gmail.com...")
        try:
            sender_email = "faiz.24365@gmail.com"
            recipient_email = "faiz.undefined@gmail.com"
            
            response = ses_client.send_email(
                Source=sender_email,
                Destination={'ToAddresses': [recipient_email]},
                Message={
                    'Subject': {'Data': 'SES Configuration Test'},
                    'Body': {
                        'Text': {'Data': 'This is a test email to verify SES configuration.'}
                    }
                }
            )
            
            message_id = response.get('MessageId')
            print(f"  ✅ Email sent successfully! Message ID: {message_id}")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"  ❌ Email send failed: {error_code}")
            print(f"  📄 Error details: {error_message}")
            
            if error_code == 'MessageRejected':
                if 'not verified' in error_message:
                    print(f"  💡 Solution: Verify the sender email '{sender_email}' in SES console")
                elif 'sandbox' in error_message.lower():
                    print(f"  💡 Solution: Either verify recipient email or request production access")
            elif error_code == 'AccessDenied':
                print(f"  💡 Solution: Add SES permissions to the IAM role")
        
        # Test 5: Check IAM permissions (if running on EC2)
        print(f"\n🔐 Checking IAM permissions...")
        try:
            # Try to get identity policies (this requires SES permissions)
            response = ses_client.list_identities()
            print(f"  ✅ IAM permissions appear to be working")
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                print(f"  ❌ IAM permissions missing for SES")
                print(f"  💡 Solution: Add SES permissions to the EC2 instance role")
            else:
                print(f"  ⚠️  Unexpected error: {e}")
        
        return True
        
    except NoCredentialsError:
        print("❌ AWS credentials not found")
        print("💡 Make sure AWS credentials are configured")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def print_ses_setup_instructions():
    """Print instructions for setting up SES"""
    print(f"\n" + "=" * 60)
    print("📋 SES SETUP INSTRUCTIONS")
    print("=" * 60)
    
    print("\n1. 🔐 VERIFY SENDER EMAIL:")
    print("   • Go to AWS SES Console → Email Addresses")
    print("   • Click 'Verify a New Email Address'")
    print("   • Enter: faiz.24365@gmail.com")
    print("   • Check your email and click the verification link")
    
    print("\n2. 🔐 VERIFY RECIPIENT EMAIL (if in sandbox mode):")
    print("   • Go to AWS SES Console → Email Addresses")
    print("   • Click 'Verify a New Email Address'")
    print("   • Enter: faiz.undefined@gmail.com")
    print("   • Check your email and click the verification link")
    
    print("\n3. 🚀 REQUEST PRODUCTION ACCESS (recommended):")
    print("   • Go to AWS SES Console → Sending Statistics")
    print("   • Click 'Request a Sending Limit Increase'")
    print("   • Fill out the form explaining your use case")
    print("   • This allows sending to any email address")
    
    print("\n4. 🔧 ADD IAM PERMISSIONS:")
    print("   • The .ebextensions/02_ses_permissions.config should handle this")
    print("   • If issues persist, manually add SES permissions to the EC2 role")
    
    print("\n5. 🧪 TEST CONFIGURATION:")
    print("   • Run this script again after making changes")
    print("   • Test the email functionality in the app")

def main():
    """Main verification function"""
    success = verify_ses_configuration()
    print_ses_setup_instructions()
    
    print(f"\n" + "=" * 60)
    print("📊 SES CONFIGURATION SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ SES client connection working")
        print("⚠️  Check individual test results above")
        print("💡 Follow the setup instructions if any tests failed")
    else:
        print("❌ SES configuration has issues")
        print("💡 Follow the setup instructions above")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)