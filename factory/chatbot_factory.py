from enum import Enum
from chatbot import (
    BaseChatbot,
    GeminiTextChatbot,
    GeminiVisionChatbot,
    OllamaTextChatbot,
)


class ChatbotType(Enum):
    """Enumeration of supported chatbot types."""

    GEMINI_TEXT = "gemini_text"
    GEMINI_VISION = "gemini_vision"
    OLLAMA_TEXT = "ollama_text"


class ChatbotFactory:
    """
    Factory class to create chatbot instances based on type.
    """

    @staticmethod
    def create_chatbot(chatbot_type: ChatbotType, database_connector, model_name):
        """
        Create a chatbot instance based on the specified type.
        :param chatbot_type: Type of chatbot to create (e.g., "gemini_text").
        :param database_connector: An instance of the database connector.
        :return: An instance of a chatbot.
        """

        if chatbot_type == chatbot_type.GEMINI_TEXT:
            return GeminiTextChatbot(database_connector, model_name)
        elif chatbot_type == chatbot_type.GEMINI_VISION:
            return GeminiVisionChatbot(database_connector, model_name)
        elif chatbot_type == chatbot_type.OLLAMA_TEXT:
            return OllamaTextChatbot(database_connector, model_name)
        else:
            raise ValueError(
                f"Unknown chatbot type: {chatbot_type}, the supported type is 'gemini_text', 'gemini_vision', 'ollama_text'."
            )
