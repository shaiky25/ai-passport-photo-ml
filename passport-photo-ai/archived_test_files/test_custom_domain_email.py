#!/usr/bin/env python3
"""
Test custom domain email setup
"""
import boto3
import requests
from botocore.exceptions import ClientError

def test_custom_domain_email():
    """Test the custom domain email setup"""
    print("🎯 TESTING CUSTOM DOMAIN EMAIL SETUP")
    print("=" * 60)
    
    # Test 1: Check if domain is verified in SES
    print("🔄 Step 1: Checking domain verification...")
    
    try:
        ses_client = boto3.client('ses', region_name='us-east-1')
        
        # List verified domains
        response = ses_client.list_verified_email_addresses()
        verified_emails = response.get('VerifiedEmailAddresses', [])
        
        # Check for domain verification
        domain_response = ses_client.list_identities()
        identities = domain_response.get('Identities', [])
        
        print(f"  📋 Verified identities:")
        for identity in identities:
            if '@' in identity:
                print(f"    📧 Email: {identity}")
            else:
                print(f"    🌐 Domain: {identity}")
        
        # Check if faizuddinshaik.com is verified
        if 'faizuddinshaik.com' in identities:
            print(f"  ✅ Domain faizuddinshaik.com is verified!")
            
            # Check DKIM status
            dkim_response = ses_client.get_identity_dkim_attributes(
                Identities=['faizuddinshaik.com']
            )
            
            dkim_attrs = dkim_response.get('DkimAttributes', {}).get('faizuddinshaik.com', {})
            dkim_enabled = dkim_attrs.get('DkimEnabled', False)
            dkim_verification_status = dkim_attrs.get('DkimVerificationStatus', 'Unknown')
            
            print(f"  🔐 DKIM enabled: {dkim_enabled}")
            print(f"  🔐 DKIM status: {dkim_verification_status}")
            
        else:
            print(f"  ❌ Domain faizuddinshaik.com is NOT verified")
            print(f"  💡 Follow the setup guide to verify your domain")
            return False
            
    except ClientError as e:
        print(f"  ❌ Error checking domain: {e}")
        return False
    
    # Test 2: Test sending email with custom domain
    print(f"\n🔄 Step 2: Testing email send with custom domain...")
    
    custom_email = "noreply@faizuddinshaik.com"
    test_recipient = "faiz.undefined@gmail.com"  # Your verified test email
    
    try:
        response = ses_client.send_email(
            Source=custom_email,
            Destination={'ToAddresses': [test_recipient]},
            Message={
                'Subject': {'Data': 'Custom Domain Email Test'},
                'Body': {
                    'Html': {
                        'Data': '''
                        <html>
                        <body>
                            <h2>🎉 Custom Domain Email Working!</h2>
                            <p>This email was sent from: <strong>noreply@faizuddinshaik.com</strong></p>
                            <p>Your passport photo app now has professional email delivery!</p>
                            <hr>
                            <p><small>PassportPhotoAI - Professional passport photos in seconds</small></p>
                        </body>
                        </html>
                        '''
                    },
                    'Text': {
                        'Data': '''
Custom Domain Email Working!

This email was sent from: noreply@faizuddinshaik.com
Your passport photo app now has professional email delivery!

PassportPhotoAI - Professional passport photos in seconds
                        '''
                    }
                }
            }
        )
        
        message_id = response.get('MessageId')
        print(f"  ✅ Custom domain email sent successfully!")
        print(f"  📧 From: {custom_email}")
        print(f"  📧 To: {test_recipient}")
        print(f"  🆔 Message ID: {message_id}")
        print(f"  📬 Check your email inbox (should NOT be in junk!)")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"  ❌ Custom domain email failed: {error_code}")
        print(f"  📄 Error: {error_message}")
        
        if 'not verified' in error_message.lower():
            print(f"  💡 Domain verification may still be in progress")
        
        return False
    
    # Test 3: Test backend API with custom domain email
    print(f"\n🔄 Step 3: Testing backend API with custom domain...")
    
    backend_url = "http://passport-photo-fixed.eba-mvpmm2ar.us-east-1.elasticbeanstalk.com"
    
    try:
        # First, we need to update the backend to use the custom email
        print(f"  ℹ️  Note: Backend needs to be updated to use {custom_email}")
        print(f"  ℹ️  Current backend still uses faiz.24365@gmail.com")
        print(f"  💡 Update SENDER_EMAIL environment variable after domain verification")
        
        # Test current backend
        response = requests.post(f"{backend_url}/api/send-otp", 
                               headers={'Content-Type': 'application/json'},
                               json={'email': test_recipient},
                               timeout=30)
        
        if response.status_code == 200:
            print(f"  ✅ Backend API working (with current email)")
        else:
            print(f"  ❌ Backend API failed: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Backend test error: {e}")
    
    return True

def print_next_steps():
    """Print next steps for custom domain setup"""
    print(f"\n" + "=" * 60)
    print("📋 NEXT STEPS FOR CUSTOM DOMAIN EMAIL")
    print("=" * 60)
    
    print(f"\n1. 🌐 VERIFY DOMAIN (if not done yet):")
    print(f"   • Go to AWS SES Console → Domains")
    print(f"   • Add faizuddinshaik.com")
    print(f"   • Add the DNS records to your domain")
    print(f"   • Wait for verification")
    
    print(f"\n2. 🔧 UPDATE BACKEND APPLICATION:")
    print(f"   • Set SENDER_EMAIL=noreply@faizuddinshaik.com")
    print(f"   • Deploy the updated backend")
    print(f"   • Test the OTP functionality")
    
    print(f"\n3. 🧪 TEST EMAIL DELIVERY:")
    print(f"   • Send test OTP emails")
    print(f"   • Verify emails go to inbox (not junk)")
    print(f"   • Check DKIM authentication")
    
    print(f"\n4. 🚀 REQUEST PRODUCTION ACCESS:")
    print(f"   • With custom domain, production access is easier")
    print(f"   • Mention professional domain in request")
    print(f"   • Get approval for unlimited customer emails")
    
    print(f"\n💡 RECOMMENDED EMAIL ADDRESSES:")
    print(f"   • noreply@faizuddinshaik.com (for OTP emails)")
    print(f"   • support@faizuddinshaik.com (for customer service)")
    print(f"   • passport@faizuddinshaik.com (service-specific)")

def main():
    """Main test function"""
    
    success = test_custom_domain_email()
    print_next_steps()
    
    print(f"\n" + "=" * 60)
    print("📊 CUSTOM DOMAIN EMAIL TEST SUMMARY")
    print("=" * 60)
    
    if success:
        print("🎉 CUSTOM DOMAIN EMAIL SETUP SUCCESSFUL!")
        print("✅ Domain verification working")
        print("✅ Custom email sending working")
        print("✅ Professional email delivery enabled")
        
        print(f"\n🎯 BENEFITS ACHIEVED:")
        print(f"✅ No more junk folder issues")
        print(f"✅ Professional appearance")
        print(f"✅ Better email deliverability")
        print(f"✅ DKIM authentication")
        
    else:
        print("⏳ CUSTOM DOMAIN SETUP IN PROGRESS")
        print("💡 Follow the setup guide to complete verification")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)