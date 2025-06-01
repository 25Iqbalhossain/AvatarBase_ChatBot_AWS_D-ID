import streamlit as st
import asyncio
import os
import tempfile
import time
import requests
import base64
from dotenv import load_dotenv
from crew import crew_workflow
from q import create_talking_avatar  # Optional; not used below
from langchain.vectorstores import Chroma

# Load environment variables

import ssl
import certifi
import requests

# Set up SSL context with certifi
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Your API endpoint and headers

load_dotenv()
DID_API_KEY = os.getenv("DID_API_KEY", "").strip()
DID_API_URL = "https://api.d-id.com/talks"

# ✅ Ensure API Key is set
if not DID_API_KEY:
    st.error("⚠️ D-ID API Key is missing! Please check your .env file or environment variables.")
    raise ValueError("D-ID API Key is missing!")

# ✅ Set up headers using Basic or Bearer auth
if ":" in DID_API_KEY:
    encoded_auth = base64.b64encode(DID_API_KEY.encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json",
        "accept": "application/json",
    }
else:
    headers = {
        "Authorization": f"Bearer {DID_API_KEY}",
        "Content-Type": "application/json",
        "accept": "application/json",
    }

async def run_workflow_with_streaming(input_text):
    """Handles AI processing and updates the chat UI."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Add user message to chat
    st.session_state["messages"].append({"role": "user", "content": input_text})

    # Call crew_workflow to process the query
    result = crew_workflow(input_text)

    if result.get("status") == "success":
        response_text = result["response"]
    else:
        response_text = f"Error: {result.get('error', 'Unknown error')}"

    # Add AI (chatbot) response to chat
    st.session_state["messages"].append({"role": "assistant", "content": response_text})

    # Refresh UI
    st.rerun()


def process_avatar_request(index):
    """
    Request an avatar video from D-ID API using the chatbot response as input.
    
    The function uses the chatbot response stored in st.session_state["messages"][index]["content"]
    as the text that the talking avatar will speak.
    """
    st.session_state["processing_avatar"] = True
    st.session_state["current_processing_id"] = index

    # DEBUG: print headers for confirmation
    print("🔹 Using Headers:", headers)

    # Retrieve the chatbot response from session state (make sure messages is a list of dictionaries)
    try:
        chatbot_response = st.session_state["messages"][index]["content"]
    except Exception as e:
        st.error("Error retrieving chatbot response from session state: " + str(e))
        return

    # Build payload using the chatbot response as the input for the avatar’s script
    payload = {
        "source_url": "https://d-id-public-bucket.s3.us-west-2.amazonaws.com/alice.jpg",
        "script": {
            "type": "text",
            "provider": {"type": "microsoft", "voice_id": "Sara"},
            "input": chatbot_response,   # <-- use chatbot response here
            "ssml": "false"
        },
        "config": {"fluent": "false"}
    }

    # Step 1: Send request to generate video
    response = requests.post(DID_API_URL, json=payload, headers=headers)
    if response.status_code != 201:
        st.error(f"⚠️ API request failed: {response.status_code} - {response.text}")
        return

    # Extract the talk ID from the response
    response_data = response.json()
    talk_id = response_data.get("id")
    print(f"✅ Video processing started! Talk ID: {talk_id}")

    # Step 2: Poll for video status
    status_url = f"{DID_API_URL}/{talk_id}"
    video_url = None

    print("⏳ Waiting for video to be ready...")

    # Poll up to 20 times (approx. 40 seconds)
    for _ in range(20):
        status_response = requests.get(status_url, headers=headers)
        if status_response.status_code != 200:
            st.error(f"❌ Error checking status: {status_response.text}")
            return

        status_data = status_response.json()
        status = status_data.get("status")

        if status == "done":
            video_url = status_data.get("result_url")
            print(f"✅ Video is ready: {video_url}")
            break
        elif status == "failed":
            st.error("❌ Video processing failed!")
            return

        time.sleep(2)

    if not video_url:
        st.error("⚠️ Video is still processing. Try again later.")
        return

    # Step 3: Download the video from the API
    temp_dir = tempfile.gettempdir()
    video_path = os.path.join(temp_dir, f"avatar_video_{index}.mp4")

    try:
        video_response = requests.get(video_url)
        if video_response.status_code == 200:
            with open(video_path, "wb") as f:
                f.write(video_response.content)
        else:
            st.error("❌ Error downloading video from D-ID API!")
            return
    except Exception as e:
        st.error(f"❌ Error downloading video: {e}")
        return

    # Step 4: Save the video path in session state and refresh UI
    if os.path.exists(video_path):
        if "avatar_videos" not in st.session_state:
            st.session_state["avatar_videos"] = {}
        st.session_state["avatar_videos"][index] = video_path
        print(f"✅ Video successfully downloaded: {video_path}")
    else:
        st.error("⚠️ Video file not found after download!")

    st.session_state["processing_avatar"] = False
    st.rerun()

