import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agents.nodes import ChatGeminiGemma, get_llm

class DummySettings:
    def __init__(self):
        self.GEMINI_API_KEY = "test-gemini-key"
        self.GOOGLE_API_KEY = ""
        self.GEMINI_MODEL = "gemma-4-31b-it"
        self.OPENAI_API_KEY = ""

@pytest.fixture
def mock_gemini_settings():
    return DummySettings()

def test_chat_gemini_gemma_payload_mapping():
    client = ChatGeminiGemma(model="gemma-4-31b-it", api_key="test-key", temperature=0.5)
    messages = [
        SystemMessage(content="You are a helper bot."),
        HumanMessage(content="Hello!"),
        AIMessage(content="Hi there!")
    ]

    with patch("httpx.post") as mock_post:
        # Create a mock response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Mock Response content"}]
                    }
                }
            ]
        }
        mock_post.return_value = mock_resp

        response = client.invoke(messages)

        # Assert response value
        assert response.content == "Mock Response content"

        # Assert payload mapping structure
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["headers"]["x-goog-api-key"] == "test-key"
        
        json_payload = call_kwargs["json"]
        assert json_payload["systemInstruction"] == {
            "parts": [{"text": "You are a helper bot."}]
        }
        assert json_payload["contents"] == [
            {"role": "user", "parts": [{"text": "Hello!"}]},
            {"role": "model", "parts": [{"text": "Hi there!"}]}
        ]
        assert json_payload["generationConfig"] == {"temperature": 0.5}


def test_chat_gemini_gemma_api_error():
    client = ChatGeminiGemma(model="gemma-4-31b-it", api_key="test-key")
    messages = [HumanMessage(content="Hello")]

    with patch("httpx.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("API Error")
        mock_post.return_value = mock_resp

        with pytest.raises(RuntimeError, match="Gemini API call failed"):
            client.invoke(messages)


def test_get_llm_resolves_gemini(mock_gemini_settings):
    with patch("agents.nodes.get_settings", return_value=mock_gemini_settings):
        llm = get_llm(temperature=0.8)
        assert isinstance(llm, ChatGeminiGemma)
        assert llm.model == "gemma-4-31b-it"
        assert llm.api_key == "test-gemini-key"
        assert llm.temperature == 0.8
