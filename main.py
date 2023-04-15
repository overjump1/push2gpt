import wave
import threading
import openai
import keyboard
import pyaudio
import time
from pydub import AudioSegment
from pydub.playback import play
from google.cloud import texttospeech

openai.api_key = "<your openai key>"
recording = False
alt_key_pressed = False

client = texttospeech.TextToSpeechClient()

def trigger():
    global recording
    if recording is False:
        recording = True
        print("Recording started")
        threading.Thread(target=record).start()
    else:
        recording = False

def record():
    global recording
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    frames = []
    while recording:
        data = stream.read(1024)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    audio.terminate()
    print("Recording ended")
    sound_file = wave.open("record.wav", "wb")
    sound_file.setnchannels(1)
    sound_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    sound_file.setframerate(44100)
    sound_file.writeframes(b"".join(frames))
    sound_file.close()
    main(transcribe())

def alt_key_event(event):
    global alt_key_pressed
    if event.event_type == 'down' and not alt_key_pressed:
        alt_key_pressed = True
        trigger()
    elif event.event_type == 'up' and alt_key_pressed:
        alt_key_pressed = False
        trigger()

keyboard.on_press_key('alt', alt_key_event)
keyboard.on_release_key('alt', alt_key_event)

def transcribe():
    audio_file= open("record.wav", "rb")
    transcript = openai.Audio.translate("whisper-1", audio_file, response_format="text")
    print("transcribed: "+transcript)
    return transcript

def tts(text):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-GB", name="en-GB-Neural2-D"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    with open("output.wav", "wb") as out:
        out.write(response.audio_content)
    print("TTS complete.")

def main(text):
    text = str(text)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "system", "content": "answers should always be short and to the point."},
                {"role": "user", "content": text},
            ]
    )
    result=""
    for choice in response.choices:
            result += choice.message.content
    print("response:\n"+str(result))
    tts(result)
    audio_file = AudioSegment.from_file('output.wav', format='wav')
    play(audio_file)

while True:
    time.sleep(1)
