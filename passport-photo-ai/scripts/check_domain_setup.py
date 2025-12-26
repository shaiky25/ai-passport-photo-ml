#!/usr/bin/env python3
"""
Check domain setup for faizuddinshaik.com
Verifies DNS records and SSL certificate
"""

import socket
import ssl
import requests
import subprocess
import sys
from datetime import datetime

def check_dns_resolution(domain):
    """Check if domain resolves to an IP"""
    try:
        ip = socket.gethostbyname(domain)
        print(f"✅ DNS Resolution: {domain} → {ip}")
        return True
    except socket.gaierror:
        print(f"❌ DNS Resolution: {domain} does not resolve")
        return False

def check_ssl_certificate(domain):
    """Check SSL certificate"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                
        print(f"✅ SSL Certificate: Valid")
        print(f"   Issued to: {cert['subject'][0][0][1]}")
        print(f"   Issued by: {cert['issuer'][1][0][1]}")
        print(f"   Valid until: {cert['notAfter']}")
        return True
    except Exception as e:
        print(f"❌ SSL Certificate: {e}")
        return False

def check_http_response(domain):
    """Check if website responds"""
    try:
        url = f"https://{domain}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ HTTP Response: {response.status_code} OK")
            print(f"   Content length: {len(response.content)} bytes")
            
            # Check if it's our React app
            if "Passport Photo AI" in response.text or "react" in response.text.lower():
                print(f"✅ App Detection: Passport Photo AI detected")
            else:
                print(f"⚠️  App Detection: May not be our app")
            
            return True
        else:
            print(f"❌ HTTP Response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ HTTP Response: {e}")
        return False

def check_dns_propagation(domain):
    """Check DNS propagation using dig"""
    try:
        result = subprocess.run(['dig', '+short', domain], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            ips = result.stdout.strip().split('\n')
            print(f"✅ DNS Propagation: {len(ips)} record(s) found")
            for ip in ips:
                print(f"   → {ip}")
            return True
        else:
            print(f"❌ DNS Propagation: No records found")
            return False
    except Exception as e:
        print(f"⚠️  DNS Propagation: Could not check ({e})")
        return None

def main():
    """Main domain checking function"""
    print("🌐 DOMAIN SETUP VERIFICATION")
    print("=" * 50)
    
    # Get domain from user
    domain = input("Enter your domain (e.g., passport.faizuddinshaik.com): ").strip()
    
    if not domain:
        print("❌ No domain provided")
        return
    
    print(f"\n🔍 Checking: {domain}")
    print("-" * 30)
    
    # Run checks
    dns_ok = check_dns_resolution(domain)
    propagation_ok = check_dns_propagation(domain)
    ssl_ok = check_ssl_certificate(domain) if dns_ok else False
    http_ok = check_http_response(domain) if dns_ok else False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DOMAIN SETUP SUMMARY")
    print("=" * 50)
    
    checks = [
        ("DNS Resolution", dns_ok),
        ("DNS Propagation", propagation_ok),
        ("SSL Certificate", ssl_ok),
        ("HTTP Response", http_ok)
    ]
    
    passed = 0
    for check_name, result in checks:
        if result is True:
            print(f"✅ {check_name}: PASS")
            passed += 1
        elif result is False:
            print(f"❌ {check_name}: FAIL")
        else:
            print(f"⚠️  {check_name}: UNKNOWN")
    
    print(f"\n🎯 Overall: {passed}/4 checks passed")
    
    if passed == 4:
        print(f"🎉 SUCCESS! {domain} is fully configured!")
        print(f"🌐 Your app is live at: https://{domain}")
    elif passed >= 2:
        print(f"⚠️  PARTIAL: Domain is partially configured")
        print("💡 DNS changes can take up to 48 hours to propagate")
    else:
        print(f"❌ FAILED: Domain is not configured yet")
        print("📋 Check your DNS records and try again")
    
    print(f"\n🔧 TROUBLESHOOTING:")
    print(f"- Check DNS: https://dnschecker.org/?domain={domain}")
    print(f"- Check SSL: https://www.ssllabs.com/ssltest/analyze.html?d={domain}")
    print(f"- AWS Amplify Console: https://console.aws.amazon.com/amplify/")

if __name__ == "__main__":
    main()