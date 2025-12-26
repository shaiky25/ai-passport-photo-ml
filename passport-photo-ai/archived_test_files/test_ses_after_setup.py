#!/usr/bin/env python3
"""
Test SES functionality after setup
"""
import requests

def test_ses_after_setup():
    """Test SES after verification setup"""
    backend_url = "http://passport-photo-fixed.eba-mvpmm2ar.us-east-1.elasticbeanstalk.com"
    
    print("🧪 TESTING SES AFTER SETUP")
    print("=" * 50)
    
    # Test with the email you verified
    test_email = "faiz.undefined@gmail.com"  # Change this if you verified a different email
    
    print(f"📧 Testing email send to: {test_email}")
    
    try:
        response = requests.post(f"{backend_url}/api/send-otp", 
                               headers={'Content-Type': 'application/json'},
                               json={'email': test_email},
                               timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        result = response.json()
        print(f"📄 Response: {result}")
        
        if response.status_code == 200:
            print("🎉 SUCCESS! Email sent successfully!")
            print("📬 Check your email inbox for the OTP")
        else:
            print("❌ Email sending still failing")
            print("💡 Make sure the email is verified in SES console")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    test_ses_after_setup()