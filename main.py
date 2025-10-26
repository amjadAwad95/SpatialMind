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

vision_chatbot = ChatbotFactory.create_chatbot(
    chatbot_type=ChatbotType.GEMINI_VISION, database_connector=databace
)


def main():
    print("Welcome to the Gemini Chatbot!")
    print("\nPlease select the chatbot model:")
    print("1. Text Chatbot")
    print("2. Vision Chatbot")
    
    while True:
        try:
            model_choice = int(input("\nEnter your choice (1 or 2): "))
            if model_choice in [1, 2]:
                break
            else:
                print("Please enter either 1 or 2.")
        except ValueError:
            print("Invalid input. Please enter a number (1 or 2).")

    # Get image path once if vision chatbot is selected
    image_path = None
    if model_choice == 2:
        while True:
            image_path = input("\nEnter the image path: ")
            if os.path.exists(image_path):
                break
            print("Error: Image file not found! Please enter a valid path.")

    print("\nType 'exit' to quit at any time.")
    
    while True:
        if model_choice == 1:
            user_input = input("\nYou: ")
            
            if user_input.lower() == "exit":
                print("Goodbye!")
                databace.close()
                break

            response = chatbot.chat(user_input)
            print(f"Chatbot: {response}")

        else:  # Vision chatbot
            text_input = input("\nEnter your question: ")
            
            if text_input.lower() == "exit":
                print("Goodbye!")
                databace.close()
                break

            response = vision_chatbot.chat({
                "query": text_input,
                "image": image_path
            })
            print(f"Chatbot: {response}")

if __name__ == "__main__":
    main()