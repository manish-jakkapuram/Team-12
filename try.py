import streamlit as st
from src.helper import voice_input, llm_model_object, text_to_speech

def main():
    st.title("Empathetic Response Chat Bot 🤖")
    
    # Choose input method: voice or text
    input_method = st.radio("Choose input method:", ("Voice", "Text"))
    
    if input_method == "Voice":
        if st.button("Ask me anything (Voice)"):
            with st.spinner("Listening..."):
                # Capture voice input
                text = voice_input()
                
                # Check if the text is None or empty
                if not text:
                    st.warning("Sorry, I didn't hear anything. Please try again.")
                    return
                
                # Generate response
                response = llm_model_object(text)
                
                # Convert response to speech
                text_to_speech(response)
                
                # Read audio file
                audio_file = open("speech.mp3", "rb")
                audio_bytes = audio_file.read()
                
                # Display response and audio options
                st.text_area("Response:", response, height=200)
                st.audio(audio_bytes)
                st.download_button(
                    "Download Speech",
                    data=audio_bytes,
                    file_name="speech.mp3",
                    mime="audio/mp3"
                )
    
    elif input_method == "Text":
        user_input = st.text_input("Type your question:")
        
        if user_input:
            # Generate response based on text input
            response = llm_model_object(user_input)
            
            # Convert response to speech
            text_to_speech(response)
            
            # Read audio file
            audio_file = open("speech.mp3", "rb")
            audio_bytes = audio_file.read()
            
            # Display response and audio options
            st.text_area("Response:", response, height=200)
            st.audio(audio_bytes)
            st.download_button(
                "Download Speech",
                data=audio_bytes,
                file_name="speech.mp3",
                mime="audio/mp3"
            )

if __name__ == '__main__':
    main()
