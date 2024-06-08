# -*- encoding: utf-8 -*-

import os
from apps.home import blueprint
from flask_login import login_required, current_user
from flask import request, jsonify, send_file, render_template, session

from pathlib import Path

import google.generativeai as genai
from google.cloud import texttospeech, speech

from google.cloud.speech_v2 import SpeechClient
# from pydub import AudioSegment

import subprocess
from openai import OpenAI

from pydub import AudioSegment
import numpy as np
import librosa
import unicodedata
import time as tm

from time import time
import requests
import parselmouth
import random

from flask_socketio import SocketIO

from apps import socketio


openai_client = OpenAI(api_key="REDACTED")

# --- TEXT TO SPEECH CLIENT --- 
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcloud-key/REDACTED.json'

# Create a client using the credentials
tts_client = texttospeech.TextToSpeechClient()

conversation_starter = f""
pre_prompt = ""

system_prompt = ""


pro_player_name = "rez"


transcribe_client = speech.SpeechClient()

transcribe_config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    audio_channel_count=1,
    sample_rate_hertz=16000,
    language_code="en-US",
    enable_automatic_punctuation=True,
)

@blueprint.route("/chat/") # <int:lesson_num>-<int:scenario_num>
def interactive():
    global system_prompt, chat_history, conversation_starter, pre_prompt
    
        
    session['wav_files'] = []
    session['files_to_delete'] = []
    session['audio_count'] = 0
    session['compiled_transcription'] = ""
          
        
    system_prompt = f""" 
    You're a virtual assistant guide to the user at compass venue. You will be posing as {pro_player_name}, a CS2 pro player. The user may ask you any
    question about the venue. Here's all the information about the venue:
    - The toilet is at the reception, to the left
    - The mosque is a four minute walk out of the venue, to the left.
    - FURIA & Ninjas & Pyjamas are competing at 8:00 PM.
    
    Here's modern information about you:
    -You're in team Ninjas in Pyjamas 
    -You won against Fnatic yesterday in the quarterfinals, and you are playing against Furia today
    
    If the user asks you about anything out of the scope of CS2, {pro_player_name}, or the venue, you must tell him that it is out of the scope of your knowledge. You must NOT answer anything not related to CS2, yourself, or the venue.
    Limit your response to a short answer. REMEMBER, YOU ARE A GUIDE TO THE USER IN THE COMPASS VENUE.
    """
    
        
    chat_history =[
        {"role": "system", "content": system_prompt}
    ]
    
    session['chat_history'] = chat_history
        
    
    return render_template(
        "chat/chat.html"
    )
    
def transcribe_audio_google(wav_file):
    with open(wav_file, 'rb') as audio_file:
        content = audio_file.read()

    # Send audio data for transcription
    audio = speech.RecognitionAudio(content=content)
    response = transcribe_client.recognize(config=transcribe_config, audio=audio)
    
        
    return response




def create_webm_file(chunk):
    if 'audio_count' not in session:
        session['audio_count'] = 0
    
    webm_file = f"temp-{session['audio_count']}.webm"
    session['audio_count'] += 1
    with open(webm_file, "wb") as f:
        f.write(chunk)
        
    return webm_file


def webm_to_wav(webm_path):
    # Load the WebM file
    audio = AudioSegment.from_file(webm_path, format="webm")

    # Convert to 16-bit audio
    audio = audio.set_sample_width(2)  # 16-bit = 2 bytes
    audio = audio.set_frame_rate(16000)

    # Save as WAV file
    wav_path = webm_path.replace(".webm", ".wav")
    audio.export(wav_path, format="wav")
    
    return wav_path


def get_audio_duration(path, format):
    audio = AudioSegment.from_file(path, format=format)
    duration = audio.duration_seconds
    return duration


    
@blueprint.route("/send_audio_full", methods=["POST"])
def get_full_audio():    
    
    audio_full = request.files.get("file")
    
    webm_file = create_webm_file(audio_full.read())
    
    wav_file = webm_to_wav(webm_file)
    
    transcription = transcribe_audio_google(wav_file)
    
    if transcription.results and transcription.results[0].alternatives[0].transcript.strip() != "":
        transcription = transcription.results[0].alternatives[0].transcript
        
        gpt_response = send_to_gpt(f"{transcription}")
                
        gpt_response = process_gpt_response(gpt_response)
        gpt_response = gpt_response.replace("CS:GO", "CS2").replace("csgo", "CS2")    
    else:
        gpt_response = "I'm sorry, I didn't catch what you said."
    

    voice_response = get_voice(gpt_response)
    

    
    
    return voice_response

    



def send_to_gpt(text, system=False):
    role = "user"
    if system:
        role = "system"
        
    if 'chat_history' not in session:
        session['chat_history'] = []
        
    session['chat_history'].append({"role": role, "content": text})
    completion = openai_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=session['chat_history'],
    temperature = 0
    )
    
    session['chat_history'].append({"role": "assistant", "content": completion.choices[0].message.content})
        
        
    return completion.choices[0].message.content
    
    
    
def process_gpt_response(text):
  return ''.join(c for c in text if unicodedata.category(c) != 'So')


def get_voice(text):
    speech_file_path = Path(__file__).parent / "speech.mp3"
    response = openai_client.audio.speech.create(
    model="tts-1",
    voice="onyx",
    input=text
    )
    response.stream_to_file(speech_file_path)
    
    file_sent = send_file(speech_file_path)
    
    
    audio_length = get_audio_duration(speech_file_path, "mp3")    
    socketio.emit('duration', audio_length)

    return file_sent



    
