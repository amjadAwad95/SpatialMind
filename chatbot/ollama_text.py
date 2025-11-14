from chatbot import BaseChatbot
from langchain_ollama import ChatOllama
from databace import PostgresqlDBConnector
from config import ollama_system_prompt, history_system_prompt
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class OllamaTextChatbot(BaseChatbot):
    """
    A chatbot class that integrates with the Ollama LLM to interact with
    a PostgreSQL database and generate intelligent responses based on both
    user queries and conversation history.
    This class handles natural language input, reformulates questions for
    better context understanding, and generates appropriate answers using
    the Ollama LLM.
    """

    def __init__(self, databace: PostgresqlDBConnector, model_name="llama3.1:8b"):
        """
        Initialize the OllamaTextChatbot with a database connector and model name.
        :param databace: An instance of PostgresqlDBConnector for database interactions.
        :param model_name: The name of the Ollama model to use (default is "llama3.1:8b").
        """

        self.databace = databace
        self.model_name = model_name

        self.model = ChatOllama(
            model=self.model_name,
            temperature=0.8,
        )

        self.chat_history = []

        self.answer_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", ollama_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "Question: {question}"),
            ]
        )

        self.history_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", history_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "Question: {question}"),
            ]
        )

        self.rephrase_chain = self.history_prompt | self.model | StrOutputParser()
        self.answer_chain = self.answer_prompt | self.model | StrOutputParser()

    def chat(self, input):
        """
        Process a user query, reformulate it for clarity and context,
        query the database schema, and generate an intelligent answer.

        :param input: The raw question or message from the user.
        :return: The chatbot's final response after reasoning over the database schema and conversation context.
        """

        schema = self.databace.get_schema(short=True)

        history = self.get_history()

        reformulated_question = self.rephrase_chain.invoke(
            {
                "question": input,
                "chat_history": history,
            }
        )

        answer = self.answer_chain.invoke(
            {
                "question": reformulated_question,
                "chat_history": history,
                "schema": schema,
            }
        )

        self.save_history(reformulated_question, answer)

        return answer

    def get_history(self):
        """
        Retrieve the current conversation history between the user and the chatbot.

        :return: A list of LangChain message objects (HumanMessage and AIMessage).
        """

        return self.chat_history

    def clear_history(self):
        """
        Clear all stored conversation history.

        :return: None
        """

        self.chat_history = []

    def save_history(self, question, answer):
        """
        Save a pair of user question and chatbot answer to the conversation history.

        :param question: The user's question (possibly reformulated).
        :param answer: The chatbot's generated response.
        :return: None
        """

        self.chat_history.append(HumanMessage(content=question))
        self.chat_history.append(AIMessage(content=answer))
