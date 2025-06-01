# shared_utils.py
import os
import tempfile
from turtle import st
from wsgiref import headers
import requests
import time
from langchain.vectorstores import Chroma


from avatar_utils import DID_API_URL

def process_avatar_request(index):
    """Generate an avatar video using the chatbot response as input."""
    st.session_state["processing_avatar"] = True
    st.session_state["current_processing_id"] = index

    try:
        chatbot_response = st.session_state["messages"][index]["content"]
    except Exception as e:
        st.error(f"Error retrieving chatbot response: {e}")
        return

    payload = {
        "source_url": "https://d-id-public-bucket.s3.us-west-2.amazonaws.com/alice.jpg",
        "script": {
            "type": "text",
            "provider": {"type": "microsoft", "voice_id": "Sara"},
            "input": chatbot_response,  
            "ssml": "false"
        },
        "config": {"fluent": "false"}
    }

    response = requests.post(DID_API_URL, json=payload, headers=headers)
    if response.status_code != 201:
        st.error(f"API request failed: {response.status_code} - {response.text}")
        return

    response_data = response.json()
    talk_id = response_data.get("id")
    status_url = f"{DID_API_URL}/{talk_id}"

    print(f"✅ Video processing started! Talk ID: {talk_id}")

    # Increased polling time to 120 seconds (1 check every 5 sec)
    for _ in range(24):  # 24 iterations * 5 sec = 120 sec
        time.sleep(5)
        status_response = requests.get(status_url, headers=headers)
        if status_response.status_code != 200:
            st.error(f"Error checking status: {status_response.text}")
            return

        status_data = status_response.json()
        if status_data.get("status") == "done":
            video_url = status_data.get("result_url")
            break
        elif status_data.get("status") == "failed":
            st.error("❌ Video processing failed!")
            return

    if not video_url:
        st.error("⚠️ Video is still processing. Try again later.")
        return

    # Download the video
    temp_dir = tempfile.gettempdir()
    video_path = os.path.join(temp_dir, f"avatar_video_{index}.mp4")

    try:
        video_response = requests.get(video_url)
        if video_response.status_code == 200:
            with open(video_path, "wb") as f:
                f.write(video_response.content)
        else:
            st.error("Error downloading video from D-ID API!")
            return
    except Exception as e:
        st.error(f"Error downloading video: {e}")
        return

    st.session_state.setdefault("avatar_videos", {})[index] = video_path
    st.session_state["processing_avatar"] = False
    st.rerun()
