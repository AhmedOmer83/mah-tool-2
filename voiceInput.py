import speech_recognition as sr

def listen_and_transcribe():
    # Initialize recognizer class (for recognizing the speech)
    recognizer = sr.Recognizer()

    # Reading microphone as source
    # Listening to the speech and storing in audio_text variable
    with sr.Microphone() as source:
        print("Adjusting for ambient noise, please wait...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Please speak into the microphone...")
        audio_text = recognizer.listen(source)
        print("Processing...")

    try:
        # Using Google Speech Recognition to convert audio to text
        text = recognizer.recognize_google(audio_text)
        print("You said: {}".format(text))
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))

if __name__ == "__main__":
    listen_and_transcribe()
