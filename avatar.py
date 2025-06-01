import asyncio
import streamlit as st
from avatar_utils import process_avatar_request, run_workflow_with_streaming
from speech import record_audio, transcribe_audio
from crew import crew_workflow
from langchain.vectorstores import Chroma


# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "avatar_videos" not in st.session_state:
    st.session_state["avatar_videos"] = {}
if "processing_avatar" not in st.session_state:
    st.session_state["processing_avatar"] = False
if "current_processing_id" not in st.session_state:
    st.session_state["current_processing_id"] = None

async def main():
    st.title("GenZMarketing Chatbot")

    # Error Handling
    if "avatar_error" in st.session_state:
        st.error(st.session_state["avatar_error"])
        del st.session_state["avatar_error"]

    st.subheader("Voice Input")
    if st.button("🎤 Use Microphone"):
        with st.spinner("Listening..."):
            audio_file = record_audio()
        if audio_file:
            transcript = transcribe_audio()
            if transcript:
                print("\n🔹 Sending to chatbot:", transcript)
                await run_workflow_with_streaming(transcript)

if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except RuntimeError:
        asyncio.run(main())
