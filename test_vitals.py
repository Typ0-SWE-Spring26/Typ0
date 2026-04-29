#!/usr/bin/env python3
"""
Test script for the admin vitals endpoint.

Usage:
    python test_vitals.py <password>

Example:
    python test_vitals.py admin_secret_123
"""

import sys
import requests
import json

if len(sys.argv) < 2:
    print("Usage: python test_vitals.py <password>")
    print("Example: python test_vitals.py admin_secret_123")
    sys.exit(1)

password = sys.argv[1]
url = f"http://localhost:15090/api/admin/vitals?password={password}"

try:
    response = requests.get(url)
    
    if response.status_code == 200:
        vitals = response.json()
        print("✓ Server vitals retrieved successfully:\n")
        print(json.dumps(vitals, indent=2))
    elif response.status_code == 401:
        print("✗ Unauthorized: Incorrect password")
        sys.exit(1)
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        sys.exit(1)
        
except requests.exceptions.ConnectionError:
    print("✗ Connection error: Is the server running on localhost:15090?")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
