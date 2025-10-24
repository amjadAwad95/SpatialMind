from abc import abstractmethod, ABC


class BaseChatbot(ABC):
    """
    Abstract base class for chatbot implementations.

    This class defines the required interface for all chatbot subclasses.
    Any chatbot that inherits from this class must implement the following methods:
    - `chat(input)`
    - `get_history()`
    - `clear_history()`
    - `save_history(question, answer)`
    """

    @abstractmethod
    def chat(self, input):
        """
        Process user input and return the chatbot's response.

        :param input: The user's input message to the chatbot.
        :return: The chatbot's response based on the input.
        """
        pass

    @abstractmethod
    def get_history(self):
        """
        Retrieve the conversation history between the user and the chatbot.

        :return: A list of conversation entries, where each entry contains a question and its corresponding answer.
        """
        pass

    @abstractmethod
    def clear_history(self):
        """
        Clear the entire conversation history.
        """
        pass

    @abstractmethod
    def save_history(self, question, answer):
        """
        Save a single question-answer pair to the conversation history.

        :param question: The user's question or input.
        :param answer: The chatbot's generated answer.
        """
        pass
