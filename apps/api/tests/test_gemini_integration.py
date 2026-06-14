import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Add src to python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from core.config import get_settings
from agents.nodes import get_llm, ChatGeminiGemma
from langchain_core.messages import HumanMessage

def test_gemini_config():
    settings = get_settings()
    api_key = settings.GEMINI_API_KEY
    model = settings.GEMINI_MODEL or "gemma-4-31b-it"
    
    print("=== Gemini Configuration Check ===")
    print(f"GEMINI_API_KEY configured: {'Yes (Ends with ...' + api_key[-4:] + ')' if api_key else 'No'}")
    print(f"GEMINI_MODEL: {model}")
    
    if not api_key:
        print("\n[ERROR] GEMINI_API_KEY is not set in environment or .env file.")
        print("Please add 'GEMINI_API_KEY=your_api_key' to your .env file.")
        sys.exit(1)
        
    print("\nAttempting to call Gemini API live...")
    llm = get_llm(temperature=0.7)
    
    if not isinstance(llm, ChatGeminiGemma):
        print(f"[ERROR] get_llm() resolved to {type(llm).__name__} instead of ChatGeminiGemma.")
        sys.exit(1)
        
    try:
        messages = [HumanMessage(content="Hello! Please respond with exactly the word 'SUCCESS' if you receive this message.")]
        print(f"Sending prompt to {model}...")
        response = llm.invoke(messages)
        print("\n=== Live API Response ===")
        print(f"Status: OK")
        print(f"Content: {response.content.strip()}")
        
        if "SUCCESS" in response.content.upper():
            print("\n[SUCCESS] Live integration check passed!")
        else:
            print("\n[WARNING] Received a response, but it did not contain the keyword 'SUCCESS'.")
    except Exception as e:
        print(f"\n[ERROR] Live API call failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_gemini_config()
