from enum import Enum
from chatbot import BaseChatbot, GeminiTextChatbot, GeminiVisionChatbot


class ChatbotType(Enum):
    """Enumeration of supported chatbot types."""

    GEMINI_TEXT = "gemini_text"
    GEMINI_VISION = "gemini_vision"


class  ChatbotFactory:
    """
    Factory class to create chatbot instances based on type.
    """

    @staticmethod
    def create_chatbot(chatbot_type: ChatbotType, database_connector):
        """
        Create a chatbot instance based on the specified type.
        :param chatbot_type: Type of chatbot to create (e.g., "gemini_text").
        :param database_connector: An instance of the database connector.
        :return: An instance of a chatbot.
        """

        if chatbot_type == chatbot_type.GEMINI_TEXT:
            return GeminiTextChatbot(database_connector)
        elif chatbot_type == chatbot_type.GEMINI_VISION:
            return GeminiVisionChatbot(database_connector)
        else:
            raise ValueError(
                f"Unknown chatbot type: {chatbot_type}, the supported type is 'gemini_text'"
            )
