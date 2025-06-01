import requests
import time
from langchain.vectorstores import Chroma


# Replace with your new API key if needed
api_key = "c2hyaXpvbi5yZXhAZ21haWwuY29t:Y2otyV0B0MXdKvzpUHYpg"

# D-ID API endpoints
base_url = "https://api.d-id.com"
talks_url = f"{base_url}/talks"

# Headers for authentication
headers = {
    "Authorization": f"Basic {api_key}",
    "Content-Type": "application/json"
}

def create_talking_avatar(script_text, voice_id="en-US-AmberNeural"):
    """
    Create a talking avatar video using the D-ID API with a stock presenter.
    
    Parameters:
        script_text: The text for the avatar.
        voice_id: The voice identifier (default: "en-US-AmberNeural").
        
    Returns:
        dict: The created talk object containing status and result_url, or None on error.
    """
    presenter_id = "rian"  # D-ID's stock presenter

    payload = {
        "presenter_id": presenter_id,
        "script": {
            "type": "text",
            "input": script_text
        },
        "voice_id": voice_id
    }
    
    response = requests.post(talks_url, headers=headers, json=payload)
    
    if response.status_code != 201:
        print(f"Error creating talk: {response.text}")
        return None
    
    talk_id = response.json()["id"]
    print(f"Talk created with ID: {talk_id}")
    
    talk_status_url = f"{talks_url}/{talk_id}"
    
    while True:
        status_response = requests.get(talk_status_url, headers=headers)
        talk_data = status_response.json()
        
        if talk_data.get("status") == "done":
            print("Talk processing completed!")
            return talk_data
        elif talk_data.get("status") == "error":
            print(f"Error processing talk: {talk_data.get('error', 'Unknown error')}")
            return None
        
        print(f"Status: {talk_data.get('status')}. Waiting...")
        time.sleep(5)

def main():
    script = "Hello! This is a test of the D-ID talking avatar API. Isn't this cool?"
    
    result = create_talking_avatar(script)
    
    if result:
        print(f"Video URL: {result.get('result_url')}")
    else:
        print("Error creating talking avatar.")

if __name__ == "__main__":
    main()
