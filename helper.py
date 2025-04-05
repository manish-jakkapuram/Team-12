import speech_recognition as sr
import google.generativeai as genai
from dotenv import load_dotenv
import os
from gtts import gTTS

print("Perfect!!")
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

def voice_input():
    r = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("Listening...")  # Debug message to see when the microphone is activated
        audio = r.listen(source)
        print("Audio captured.")  # Debug message after audio is captured
    try:
        # Recognize speech using Google Web Speech API
        text = r.recognize_google(audio)
        print(f"You said: {text}")  # Debug the recognized text
        return text
    except sr.UnknownValueError:
        print("Sorry, could not understand the audio")  # Debug message for unrecognized speech
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service: {e}")  # Debug for API errors
        return None
def text_to_speech(text):
    tts = gTTS(text=text, lang="en")
    tts.save("speech.mp3")

def llm_model_object(user_text):
    """Generate response using the Gemini model."""
    
    # Check if user_text is None or empty
    if not user_text or not user_text.strip():  # Check if None or empty string
        return "Sorry, I didn't catch that. Please try again."  # Return a default message
    
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    try:
        response = model.generate_content(user_text)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"  # Handle any errors from the API
