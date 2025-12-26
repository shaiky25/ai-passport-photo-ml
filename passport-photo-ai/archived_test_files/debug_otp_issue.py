#!/usr/bin/env python3
"""
Debug the OTP issue step by step
"""
import requests
import json

def debug_otp_issue():
    """Debug the OTP sending issue"""
    backend_url = "http://passport-photo-fixed.eba-mvpmm2ar.us-east-1.elasticbeanstalk.com"
    test_email = "faiz.undefined@gmail.com"
    
    print("🔍 DEBUGGING OTP ISSUE")
    print("=" * 50)
    
    # Test 1: Health check
    print("🔄 Step 1: Health check...")
    try:
        response = requests.get(f"{backend_url}/api/health", timeout=30)
        print(f"  📊 Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Health: {result.get('message')}")
        else:
            print(f"  ❌ Health check failed")
            return False
    except Exception as e:
        print(f"  ❌ Health error: {e}")
        return False
    
    # Test 2: Send OTP with detailed debugging
    print(f"\n🔄 Step 2: Send OTP to {test_email}...")
    
    try:
        # Make the request
        response = requests.post(
            f"{backend_url}/api/send-otp", 
            headers={'Content-Type': 'application/json'},
            json={'email': test_email},
            timeout=30
        )
        
        print(f"  📊 HTTP Status: {response.status_code}")
        print(f"  📄 Response Headers: {dict(response.headers)}")
        
        try:
            result = response.json()
            print(f"  📄 Response Body: {json.dumps(result, indent=2)}")
        except:
            print(f"  📄 Response Text: {response.text}")
        
        if response.status_code == 200:
            print(f"  ✅ OTP request successful!")
            return True
        else:
            print(f"  ❌ OTP request failed")
            return False
            
    except Exception as e:
        print(f"  ❌ OTP request error: {e}")
        return False

def test_local_ses():
    """Test SES locally to compare"""
    print(f"\n🔄 Step 3: Test SES locally for comparison...")
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        ses_client = boto3.client('ses', region_name='us-east-1')
        
        # Generate a test OTP
        import random
        import string
        otp = ''.join(random.choices(string.digits, k=6))
        
        print(f"  🔢 Generated OTP: {otp}")
        
        # Try to send email
        response = ses_client.send_email(
            Source='faiz.24365@gmail.com',
            Destination={'ToAddresses': ['faiz.undefined@gmail.com']},
            Message={
                'Subject': {'Data': 'Local Test OTP'},
                'Body': {
                    'Text': {'Data': f'Your test OTP is: {otp}'},
                    'Html': {'Data': f'<p>Your test OTP is: <strong>{otp}</strong></p>'}
                }
            }
        )
        
        message_id = response.get('MessageId')
        print(f"  ✅ Local SES test successful! Message ID: {message_id}")
        print(f"  📧 Check your email for OTP: {otp}")
        return True
        
    except ClientError as e:
        print(f"  ❌ Local SES error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Local test error: {e}")
        return False

def main():
    """Main debug function"""
    
    backend_success = debug_otp_issue()
    local_success = test_local_ses()
    
    print(f"\n" + "=" * 50)
    print("📊 DEBUG RESULTS")
    print("=" * 50)
    
    print(f"🔗 Backend OTP: {'✅ Working' if backend_success else '❌ Failed'}")
    print(f"🏠 Local SES: {'✅ Working' if local_success else '❌ Failed'}")
    
    if local_success and not backend_success:
        print(f"\n💡 DIAGNOSIS:")
        print(f"✅ SES works locally (your credentials)")
        print(f"❌ SES fails on backend (IAM role permissions)")
        print(f"\n🔧 SOLUTION:")
        print(f"The IAM role on the EC2 instance needs SES permissions")
        print(f"The .ebextensions config might not have applied correctly")
        
    elif backend_success:
        print(f"\n🎉 BOTH WORKING!")
        print(f"Check your email for the OTP")
        
    else:
        print(f"\n❌ BOTH FAILING - Check SES configuration")
    
    return backend_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)