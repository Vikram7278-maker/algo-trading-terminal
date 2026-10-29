import requests

CLIENT_ID = "1112708516"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJ1c2VyUmVnaW9uIjoiUjEiLCJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzkzMTE3NTYyLCJpYXQiOjE3OTMwMzExNjIsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTEyNzA4NTE2In0.eNfjWVzc0A4rN1PbxCF5Fdm-nOVWqCEIiagvhl3LzrZw7dX7vHQHZdJMIZ66dTdQRLBe8Eybetgrt1yP0SMYQA"

# Updated DhanHQ v2 Headers
headers = {
    'access-token': ACCESS_TOKEN,
    'client-id': CLIENT_ID,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# DhanHQ v2 Endpoint for Fund Limits
url = "https://api.dhan.co/v2/fundlimit"

response = requests.get(url, headers=headers)

print(f"HTTP Status Code: {response.status_code}")

if response.status_code == 200:
    try:
        data = response.json()
        print("=== API Connection Successful! ===")
        print(data)
    except Exception as e:
        print("Raw Response Text (Not JSON):", response.text)
else:
    print("Error Details:", response.status_code, response.text)