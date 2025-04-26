import os
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
from playsound import playsound 
load_dotenv()

# Load the API key from environment variables
API_KEY = os.getenv("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")
if not API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set.")

client = Groq(api_key=API_KEY)  # Pass the API key explicitly

speech_file_path = Path(__file__).parent / "speech.wav"

try:
    # Primary request
    response = client.audio.speech.create(
        model="playai-tts",
        voice="Aaliyah-PlayAI",
        response_format="wav",
        input="es extraordinary photos, and appreciate its fast charging and CPU performance. The phone is easy to set up and offers good value for money, with one customer noting its long-lasting battery. They like its features, with one mentioning the interesting AI functions, though opinions about the phone's size are mixed, with some appreciating the larger screen while others find it too big.AI-generated from the text of customer reviews",
    )
    response.write_to_file(speech_file_path)
    playsound(speech_file_path)

except Exception as e:
    print(f"An error occurred: {e}")
    print("Falling back to the Arabic model and voice...")

    # Fallback request
    response = client.audio.speech.create(
        model="playai-tts-arabic",
        voice="Amira-PlayAI",
        response_format="wav",
        input="es extraordinary photos, and appreciate its fast charging and CPU performance. The phone is easy to set up and offers good value for money, with one customer noting its long-lasting battery. They like its features, with one mentioning the interesting AI functions, though opinions about the phone's size are mixed, with some appreciating the larger screen while others find it too big.AI-generated from the text of customer reviews",
    )
    response.write_to_file(speech_file_path)
    
playsound(speech_file_path)

