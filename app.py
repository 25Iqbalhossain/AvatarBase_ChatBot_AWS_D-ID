import asyncio
import streamlit as st
from crew import crew_workflow
import sys
import pyttsx3
from avatar_utils import process_avatar_request, run_workflow_with_streaming
from speech import record_audio, transcribe_audio_with_aws  # Fixed import issue
from avatar_utils import run_workflow_with_streaming
from langchain_community.vectorstores import Chroma


# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "avatar_videos" not in st.session_state:
    st.session_state["avatar_videos"] = {}
if "processing_avatar" not in st.session_state:
    st.session_state["processing_avatar"] = False
if "current_processing_id" not in st.session_state:
    st.session_state["current_processing_id"] = None
if "recording" not in st.session_state:
    st.session_state["recording"] = False

async def main():
    st.title("GenZMarketing Chatbot")
    st.write("Ask questions about GenZ marketing - type or use voice input!")

    # Display errors if they exist
    if "avatar_error" in st.session_state:
        st.error(st.session_state["avatar_error"])
        del st.session_state["avatar_error"]

    for i, message in enumerate(st.session_state["messages"]):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            if message["role"] == "assistant":
                if i in st.session_state["avatar_videos"]:
                    st.video(st.session_state["avatar_videos"][i])
                else:
                    if st.session_state["processing_avatar"] and st.session_state["current_processing_id"] == i:
                        st.spinner("Generating talking avatar...")
                    else:
                        st.button("Create Talking Avatar", key=f"history_btn_{i}", 
                                  on_click=process_avatar_request, args=(i,))
    
    st.subheader("Voice Input")
    
    if not st.session_state["recording"]:
        if st.button("🎤 Start Recording"):
            st.session_state["recording"] = True
            st.session_state["audio_file"] = record_audio()
    else:
        if st.button("🛑 Stop Recording"):
            st.session_state["recording"] = False
            if "audio_file" in st.session_state and st.session_state["audio_file"]:
                transcript = transcribe_audio_with_aws()
                st.write("Transcription:", transcript)
                if transcript:
                    print("\n🔹 Sending to chatbot (Voice Input):", transcript)
                    await run_workflow_with_streaming(transcript)
    
    st.subheader("Text Input")
    user_query = st.chat_input("Type your question here...")
    if user_query:
        print("\n🔹 Sending to chatbot (Text Input):", user_query)
        await run_workflow_with_streaming(user_query)

if __name__ == "__main__":
    try:
        import pyaudio
    except ImportError:
        st.error("PyAudio not found! Install with: pip install pyaudio")

    try:
        import pyttsx3
        
    except ImportError:
        st.error("pyttsx3 not found! Install with: pip install pyttsx3")

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except RuntimeError:
        asyncio.run(main())
