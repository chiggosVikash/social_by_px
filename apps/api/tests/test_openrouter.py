import os
import sys
from dotenv import load_dotenv

# Ensure we load the latest .env file
load_dotenv("../../.env")

# Verify the environment variable is set
if not os.getenv("OPENROUTER_API_KEY"):
    print("❌ ERROR: OPENROUTER_API_KEY is not set in your .env file!")
    print("Please add OPENROUTER_API_KEY=\"sk-or-v1-...\" to your .env file and run this again.")
    sys.exit(1)

from src.agents.nodes import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

def run_test():
    print(f"🔧 Testing OpenRouter Configuration...")
    print(f"🔑 Using API Key: {os.getenv('OPENROUTER_API_KEY')[:10]}...")
    
    # get_llm() uses OPENROUTER_MODEL from config, falling back to meta-llama/llama-3-70b-instruct
    os.environ['OPENROUTER_MODEL'] = 'meta-llama/llama-3-70b-instruct'
    llm = get_llm()
    llm.model_name = 'meta-llama/llama-3-70b-instruct'
    print(f"🧠 Loaded LLM Model: {llm.model_name}")
    print("--------------------------------------------------")
    
    messages = [
        SystemMessage(content="You are a helpful assistant. Please reply with a valid JSON array containing exactly one object with the keys 'status' and 'message'."),
        HumanMessage(content="Hello! Can you confirm you are working?")
    ]
    
    print("⏳ Sending request to OpenRouter...")
    try:
        response = llm.invoke(messages)
        print("✅ SUCCESS! Response received:")
        print("--------------------------------------------------")
        print(response.content)
        print("--------------------------------------------------")
    except Exception as e:
        print("❌ ERROR: API request failed!")
        print(e)

if __name__ == "__main__":
    run_test()
