
# software design patter - lazy-loading singleton technique 
#  Its purpose is to create and manage a single, shared instance of your resource-intensive ChatBot class, ensuring it's only loaded into memory when it's first needed.


from .rag_pipeline import ChatBot

class ChatbotService:
    _instance = None

    @classmethod
    def get_instance(cls):
        """
        Returns a single, shared instance of the ChatBot.
        The instance is created only on the first call.
        """
        if cls._instance is None:
            print("Initializing ChatBot instance for the first time...")
            cls._instance = ChatBot()
            print("ChatBot instance created successfully.")

        return cls._instance

def get_bot_instance():

    return ChatbotService.get_instance()