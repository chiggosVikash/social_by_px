import sys
import os

# Ensure src is in the path
sys.path.insert(0, os.path.abspath("src"))

from core.config import get_settings
from agents.nodes import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

def test_llm():
    print("Testing OpenRouter configuration...")
    settings = get_settings()
    print(f"OPENROUTER_MODEL config: {settings.OPENROUTER_MODEL}")
    
    if not settings.OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY is not set.")
        return

    print("Initializing LLM...")
    llm = get_llm(temperature=0.7)
    
    messages = [
        SystemMessage(content="You are a helpful assistant. Always reply with valid JSON array of 1 object."),
        HumanMessage(content="Please reply with exactly this JSON: [{\"test\": \"successful\"}]")
    ]
    
    print("Invoking LLM... this may take a few seconds.")
    try:
        response = llm.invoke(messages)
        print("=== Response received! ===")
        print(response.content)
    except Exception as e:
        print(f"Error invoking LLM: {e}")

if __name__ == "__main__":
    test_llm()
