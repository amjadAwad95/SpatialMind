# from chatbot import BaseChatbot
from chatbot.base_chatbot import BaseChatbot
from databace import PostgresqlDBConnector
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config import history_system_prompt, system_prompt
import base64
import os


class GeminiVisionChatbot(BaseChatbot):

    def __init__(self, databace: PostgresqlDBConnector, model_name="gemini-2.5-pro"):
        """
        A self-contained class to handle multimodal input (image + text),
        generate SQL queries, and manage conversation history using LangChain.
        Implements the BaseChatbot abstract interface.
        """
        self.databace = databace
        self.model_name = model_name

        self.model = ChatGoogleGenerativeAI(model=self.model_name, temperature=0.2)
        self.chat_history: list[BaseMessage] = []

        self._initialize_chains()

    def _initialize_chains(self):
        """Sets up the two-stage LangChain pipelines (rephrase and answer)."""

        self.history_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", history_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{question}"),
            ]
        )
        self.rephrase_chain = self.history_prompt | self.model | StrOutputParser()

        self.answer_prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), MessagesPlaceholder("messages")]
        )

        self.answer_chain = self.answer_prompt | self.model | StrOutputParser()

    def _create_multimodal_content(
        self, text_query: str, image_b64: str
    ):  # Changed List[Union[str, Dict[str, Any]]]
        """Creates the list of content parts for a multimodal HumanMessage."""
        content = []

        if image_b64:
            content.append(
                {
                    "inlineData": {
                        "mimeType": "image/png",
                        "data": image_b64,
                    }
                }
            )

        content.append(text_query)

        return content

    def __image_to_base64(self, image_path: str) -> str:
        """
        Reads an image file from a given path and returns its Base64 encoded string.
        """
        if not os.path.exists(image_path):
            print(f"Error: File not found at path: {image_path}")
            return ""

        with open(image_path, "rb") as image_file:
            binary_data = image_file.read()
            base64_encoded_data = base64.b64encode(binary_data)
            base64_string = base64_encoded_data.decode("utf-8")

            return base64_string

    def chat(self, input) -> str:
        """
        Process a multimodal user input (text + image), reformulate the question,
        query the database schema, and generate an intelligent answer.

        :param input: A dict containing 'query' (str) and 'image' (str, path).
        :return: The chatbot's final response after reasoning over the database schema and conversation context.
        """
        input_query = input.get("query", "")
        image = input.get("image", "")
        uploaded_image_b64 = self.__image_to_base64(image) if image else ""

        history = self.get_history()
        schema = self.databace.get_schema()

        reformulated_question = self.rephrase_chain.invoke(
            {
                "question": input_query,
                "chat_history": history,
            }
        )

        multimodal_content_parts = self._create_multimodal_content(
            text_query=f"Question: {reformulated_question}",
            image_b64=uploaded_image_b64,
        )

        current_human_message = HumanMessage(content=multimodal_content_parts)

        final_messages_for_model = history + [current_human_message]

        answer = self.answer_chain.invoke(
            {
                "messages": final_messages_for_model,
                "schema": schema,
            }
        )

        self.save_history(reformulated_question, answer)

        return answer

    def get_history(self) -> list[BaseMessage]:
        """
        Retrieve the current conversation history between the user and the chatbot.
        :return: A list of LangChain message objects (HumanMessage and AIMessage).
        """
        return self.chat_history

    def clear_history(self):
        """
        Clear the conversation history.
        """
        self.chat_history = []

    def save_history(self, question: str, answer: str):
        """
        Save a pair of user question and chatbot answer to the conversation history.
        :param question: The user's question as a string.
        :param answer: The chatbot's answer as a string.
        """
        self.chat_history.append(HumanMessage(content=question))
        self.chat_history.append(AIMessage(content=answer))
