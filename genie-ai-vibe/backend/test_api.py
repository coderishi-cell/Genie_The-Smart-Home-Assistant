import requests
import json

def test_api():
    url = "http://localhost:8000/api/talk"
    payload = {"message": "turn off all the lights"}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nParsed JSON:")
            print(json.dumps(data, indent=2))
            
            if 'device_changes' in data:
                print(f"\nDevice Changes Found:")
                print(json.dumps(data['device_changes'], indent=2))
            else:
                print("\nNo device_changes in response")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api() 