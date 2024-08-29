from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import pygame
from dotenv import load_dotenv
from groq import Groq
from deepgram import DeepgramClient, SpeakOptions
from deepgram import Deepgram
import time
import speech_recognition as sr
import logging

load_dotenv()
filename='output.wav,'
# greet='greeting_audio.wav/'

app = Flask(__name__)
CORS(app)

groq_api_key = os.getenv('GROQ_APIKEY2')
deepgram_api_key = os.getenv('DG_API_KEY')
filename = 'output.wav'


def play_audio(file_path):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        logging.info(file_path)
        pygame.mixer.music.play()
        logging.info("playing file")
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.quit()
    except pygame.error as e:
        logging.error(f"Failed to play audio: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while playing audio: {e}")



recognizer = sr.Recognizer()



def update_status(message):
    print(message)

# def listen_and_process(selected_topic, selected_prompt):
    conversation = []
    with sr.Microphone() as source:
        update_status("Adjusting for ambient noise, please wait...")
        recognizer.adjust_for_ambient_noise(source)
        while True:
            update_status("Listening...")
            audio = recognizer.listen(source)
            update_status("Processing...")
            try:
                # Use the microphone as source for input
                with sr.Microphone() as source:
                    print("Listening...")
                    audio = recognizer.listen(source)
                
                # Recognize speech using Google Speech Recognition
                user_input = recognizer.recognize_google(audio)
                conversation.append({"role": "user", "content": user_input})
                print(f"👦User said: {user_input}")

                # Check for the stop phrase
                if "thank" in user_input.lower():
                    print("Conversation ended.")
                    quit()

                # Generate the response
                selected_topic = "example_topic"  # Replace with your actual topic
                selected_prompt = "example_prompt"  # Replace with your actual prompt
                response = process_input(selected_topic, selected_prompt, user_input)
                conversation.append({"role": "assistant", "content": response})
                print(f"🖥️Response: {response}")

                # Convert response to speech
                file = text_to_speech(response)
                if file:
                    print(f"Audio file created: {file}")
                    play_audio(file)
                else:
                    print("Failed to generate audio file.")

            except sr.UnknownValueError:
                print("Sorry, could not understand the audio.")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
            except Exception as e:
                print(f"An error occurred: {e}")



@app.route('/start', methods=['POST'])
def start_function():
    data = request.get_json()
    topic = data['topic']
    level = data['level']
    greeting = f"Hello, how can I help you learn about {topic}?"
    
    # greet = "greeting_audio.wav/"
    audio_file = text_to_speech(greeting, filename)
    
    # if audio_file:
    play_audio(filename)        
    # listen_and_process()
        
    
    return jsonify({
        'greeting': greeting,
        'audio_file': f"/audio/{audio_file}" if audio_file else None
    })


def text_to_speech(text, filename):
    
        api_key = os.getenv("DG_API_KEY")
        if not api_key:
            raise ValueError("Deepgram API key not set in environment variables.")

        SPEAK_OPTIONS = {"text": text}

        deepgram = DeepgramClient(api_key=api_key)

        options = SpeakOptions(
            model="aura-asteria-en",
            encoding="linear16",
            container="wav"
        )

        response = deepgram.speak.v("1").save(filename, SPEAK_OPTIONS, options)
        return filename

    # except Exception as e:
    #     print(f"Exception: {e}")
    #     return None


@app.route('/api/process', methods=['POST'])
def process_input():
    data = request.get_json()
    user_input = data['input']
    topic = data['topic']
    level = data['level']

    prompt_template = """
    You are a tutor. Your task is to guide user students through {selected_topic} and help users in the learning process step by step of students' concerns, problems, and subjects. You should instruct the AI to act as a tutor, focusing on understanding the student’s needs and delivering personalized, step-by-step instructions. Go step by step and keep the response short and easy to understand for the user. The response should be a maximum of 70 words.
    User: {user_input}
    AI: 
    """

    formatted_prompt = prompt_template.format(selected_topic=topic, user_input=user_input)

    client = Groq(api_key=groq_api_key)
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": formatted_prompt}],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )

    response = ""
    for chunk in completion:
        response += (chunk.choices[0].delta.content or "")
    
    audio_file = text_to_speech(response,filename=filename)
    
    if audio_file:
        play_audio(filename)
        logging.info("playing")
        # os.remove(filename)
  
    return jsonify({
        'response': response,
        'audio_file': f"/audio/{audio_file}" if audio_file else None
    })
     

if __name__ == "__main__":
    if not os.path.exists('audio'):
        os.makedirs('audio')
    # play_audio()
    app.run(host='0.0.0.0', port=5001,debug=True, allow_unsafe_werkzeug=True)
    

