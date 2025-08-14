from flask import Flask, render_template, request, jsonify, send_file
from more import getresponse, createlog
from waitress import serve
from datetime import datetime
import os
import threading
import time
from openai import OpenAI
from pathlib import Path
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './uploads/'

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
speech_folder = Path(__file__).parent / "static" / "speech"
speech_folder.mkdir(parents=True, exist_ok=True)
uploads_folder = Path(__file__).parent / "uploads"
uploads_folder.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def midnight_checker():
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            with open("previd.txt") as p:
                previd = p.read()
            if previd:
                createlog(previd)
        time.sleep(60)

midnight_thread = threading.Thread(target=midnight_checker, daemon=True)
midnight_thread.start()


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/chat')
def getresp():
    usertext = request.args.get('usertext')
    if usertext:
        getresponse(usertext)

    with open("chathistory.txt") as c:
        history = [line.split("%") for line in c.read().split("\n") if line]

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(history=history)

    return render_template("chat.html", history=history)


@app.route('/journal')
def journal():
    with open("journal.txt") as j:
        journ = j.read()
    return render_template('journal.html', journal=journ)


@app.route('/morevoice')
def morevoice():
    return render_template('morevoice.html')


@app.route('/tts')
def tts():
    text = request.args.get('text', '')
    if not text:
        return jsonify({"error": "No text provided"}), 400

    speech_file_path = speech_folder / "speech.mp3"
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text,
        instructions="""Voice Affect:
Calm, composed, and deeply empathetic. A steady, reassuring presence that conveys safety and understanding. The voice should exude competence and emotional attunement, fostering trust and openness.
Tone:
Warm, nonjudgmental, and reflective. Sincere with gentle curiosity—never rushed or authoritative. A balance of professionalism and human connection, validating emotions while guiding insight.
Pacing:
Slow to moderate, allowing space for processing emotions and thoughts. Deliberate pauses after important reflections or questions to let words resonate. Slightly quicker when summarizing or transitioning to action steps, signaling structure and forward movement.
Emotions:
Empathic attunement (reflecting care and deep listening), gentle encouragement (supporting growth without pressure), and grounded stability (a steady anchor in distress).
Pronunciation:
Clear and measured, with careful articulation to ensure key therapeutic phrases land effectively (e.g., "How does that feel for you?" or "Let’s explore that together."). Softened inflection when addressing sensitive topics.
Pauses:
Before reflective statements to invite contemplation.
After emotionally charged disclosures to honor the weight of the moment.
Between questions to avoid overwhelming the client.
"""
    ) as response:
        response.stream_to_file(speech_file_path)

    return send_file(speech_file_path, mimetype="audio/mpeg")


@app.route('/stt', methods=['POST'])
def stt():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    audio_file = request.files['audio']
    audio_path=os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(audio_file.filename))
    audio_file.save(audio_path)
    with open(audio_path, "rb") as af:
        transcription = client.audio.transcriptions.create(
            file=af,
            model="whisper-1"
        )
    text = transcription.text
    return jsonify({"text": text})


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000)