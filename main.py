import os
from dotenv import load_dotenv
from factory import ChatbotFactory, DatabaseFactory, ChatbotType, DatabaseType

load_dotenv()

databace = DatabaseFactory.get_database_connector(
    db_type=DatabaseType.POSTGRESQL,
    db_name=os.getenv("db_name"),
    db_user=os.getenv("db_user"),
    db_password=os.getenv("db_password"),
    db_host=os.getenv("db_host"),
    db_port=os.getenv("db_port"),
)

databace.connect()


chatbot = ChatbotFactory.create_chatbot(
    chatbot_type=ChatbotType.GEMINI_TEXT, database_connector=databace
)


def main():
    print("Welcome to the Gemini Text Chatbot! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Goodbye!")
            databace.close()
            break

        response = chatbot.chat(user_input)
        print(f"Chatbot: {response}")


if __name__ == "__main__":
    main()
