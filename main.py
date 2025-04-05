from src.helper import voice_input, llm_model_object, text_to_speech

def main():
    print("Listening for your input...")
    user_input = voice_input()
    
    if user_input:
        print(f"User Input: {user_input}")
        
        print("Generating response...")
        response = llm_model_object(user_input)
        print(f"Response: {response}")
        
        print("Converting response to speech...")
        text_to_speech(response)
        print("Speech saved as 'speech.mp3'.")
    else:
        print("No valid input detected.")

if __name__ == "__main__":
    main()
