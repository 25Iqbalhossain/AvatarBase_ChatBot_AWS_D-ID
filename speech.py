import os
import sys
import logging
import threading
from queue import Queue
import pyttsx3
import speech_recognition as sr
from pydub import AudioSegment
from io import BytesIO
import boto3
from dotenv import load_dotenv
import requests
import uuid
import time
import traceback

# === Load environment variables ===
load_dotenv()
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY", "").strip()
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY", "").strip()
AWS_REGION = "eu-north-1"
S3_BUCKET_NAME = "tedbotai"

# Debug check: Is .env loaded?
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info(f"AWS_ACCESS_KEY loaded? {'Yes' if AWS_ACCESS_KEY else 'No'}")

# === File path setup ===
audio_dir = os.path.join(os.getcwd(), "audio_files")
os.makedirs(audio_dir, exist_ok=True)
audio_file_path = os.path.join(audio_dir, "user.wav")

# === TTS setup ===
tts_queue = Queue()
engine = pyttsx3.init()

try:
    engine.setProperty('rate', 150)
    voices = engine.getProperty('voices')
    if voices:
        engine.setProperty('voice', voices[0].id)

    def tts_worker():
        while True:
            text = tts_queue.get()
            if text is None:
                break
            if text:
                engine.say(text)
                engine.runAndWait()

    threading.Thread(target=tts_worker, daemon=True).start()
    logging.info("TTS worker thread started.")
except Exception as e:
    logging.error(f"TTS Initialization Error: {e}")

# === Audio recording function ===
def record_audio(timeout=10, phrase_time_limit=30):
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            logging.info("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            logging.info("Start speaking now...")
            audio_data = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            logging.info("Recording complete.")

            # Convert and save audio as WAV
            wav_data = audio_data.get_wav_data()
            audio_segment = AudioSegment.from_wav(BytesIO(wav_data)).set_channels(1)
            audio_segment.export(audio_file_path, format="wav")
            file_size = os.path.getsize(audio_file_path)
            logging.info(f"Audio saved to {audio_file_path}, size: {file_size} bytes")
            return audio_file_path
    except Exception as e:
        logging.error(f"Error recording audio: {e}")
        return None

# === AWS Transcribe function ===
def transcribe_audio_with_aws():
    logging.info(f"Transcribing audio from: {audio_file_path}")

    try:
        # AWS Clients
        transcribe_client = boto3.client(
            'transcribe',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )

        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )

        # Upload to S3
        s3_key = f"user_audio_{uuid.uuid4().hex}.wav"
        s3_client.upload_file(audio_file_path, S3_BUCKET_NAME, s3_key)
        logging.info(f"Uploaded to s3://{S3_BUCKET_NAME}/{s3_key}")

        # Use raw S3 URI
        media_url = f"s3://{S3_BUCKET_NAME}/{s3_key}"

        # Start Transcription Job
        job_name = f"transcription_job_{uuid.uuid4().hex}"
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': media_url},
            MediaFormat='wav',
            LanguageCode='en-US'
        )

        # Poll for Completion
        logging.info(f"Check job manually in AWS console: https://{AWS_REGION}.console.aws.amazon.com/transcribe/home?region={AWS_REGION}#jobs")
        max_tries = 6
        for i in range(max_tries):
            try:
                result = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
                status = result['TranscriptionJob']['TranscriptionJobStatus']
                logging.info(f"[{i+1}] Transcription job status: {status}")
                if status in ["COMPLETED", "FAILED"]:
                    break
            except Exception as loop_error:
                logging.error(f"Polling error: {loop_error}")
                break
            time.sleep(3)

        if status == "COMPLETED":
            transcript_url = result['TranscriptionJob']['Transcript']['TranscriptFileUri']
            response = requests.get(transcript_url)
            transcript = response.json().get('results', {}).get('transcripts', [{}])[0].get('transcript', '')
            logging.info("Transcription successful.")
            return transcript or "No speech detected."
        else:
            logging.error("Transcription failed.")
            return "Transcription failed."

    except Exception as e:
        logging.error(f"Transcription error: {e}")
        traceback.print_exc()
        return "Error during transcription."


# === Main runner ===
if __name__ == "__main__":
    try:
        while True:
            recorded = record_audio()
            if recorded:
                logging.info("Finished recording, about to transcribe...")
                result = transcribe_audio_with_aws()
                logging.info(f"Transcript: {result}")
                print("Transcription:", result)
                tts_queue.put(f"You said: {result}")
            else:
                logging.warning("Recording failed or no speech detected.")
            logging.info("Waiting 2 seconds before next recording...")
            time.sleep(2)
    except KeyboardInterrupt:
        logging.info("Program stopped by user.")
        tts_queue.put(None)  # Shut down TTS worker
    except Exception as e:
        logging.error(f"Unexpected error in main loop: {e}")
        traceback.print_exc()