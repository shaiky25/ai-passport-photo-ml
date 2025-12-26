#!/usr/bin/env python3
"""
Check if SES production access has been granted
"""
import boto3
from botocore.exceptions import ClientError

def check_production_status():
    """Check if SES is in production mode"""
    print("🔍 CHECKING SES PRODUCTION STATUS")
    print("=" * 50)
    
    try:
        ses_client = boto3.client('ses', region_name='us-east-1')
        
        # Check sending quota
        response = ses_client.get_send_quota()
        max_24_hour = response.get('Max24HourSend', 0)
        max_send_rate = response.get('MaxSendRate', 0)
        
        print(f"📊 Current Limits:")
        print(f"  📈 Max emails per 24 hours: {max_24_hour}")
        print(f"  ⚡ Max send rate per second: {max_send_rate}")
        
        # Determine if in production mode
        if max_24_hour > 200 or max_send_rate > 1:
            print(f"\n🎉 PRODUCTION ACCESS GRANTED!")
            print(f"✅ You can now send to any email address")
            print(f"✅ Your app will work for all customers")
        else:
            print(f"\n⏳ Still in sandbox mode")
            print(f"📝 Limits suggest sandbox mode (200 emails/day, 1/second)")
            print(f"💡 Submit production access request if you haven't already")
            
        # Test with unverified email
        print(f"\n🧪 Testing unverified email send...")
        try:
            response = ses_client.send_email(
                Source='faiz.24365@gmail.com',
                Destination={'ToAddresses': ['test-unverified@example.com']},
                Message={
                    'Subject': {'Data': 'Production Test'},
                    'Body': {'Text': {'Data': 'Testing production access'}}
                }
            )
            print(f"✅ Can send to unverified emails - PRODUCTION MODE!")
        except ClientError as e:
            if 'not verified' in str(e):
                print(f"❌ Still in sandbox mode - can't send to unverified emails")
            else:
                print(f"⚠️  Other error: {e}")
                
    except Exception as e:
        print(f"❌ Error checking status: {e}")

if __name__ == "__main__":
    check_production_status()