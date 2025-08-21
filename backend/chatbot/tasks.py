
import os
import shutil
from celery import shared_task
from django.conf import settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from users.models import UserDocument

from chatbot.models import ChatSession 
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

CHROMA_PATH = os.path.join(settings.BASE_DIR, 'chroma_db')

@shared_task
def process_document_ingestion(user_document_id: int):

    try:
        doc = UserDocument.objects.get(id=user_document_id)
        doc.ingestion_status = 'PROCESSING'
        doc.save()

        # Load Document
        loader = PyPDFLoader(doc.file.path)
        documents = loader.load()

        # Split Document
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=120,
            length_function = len,
            separators=["\n\n", "\n", ".", " "]
        )

        chunks = text_splitter.split_documents(documents)

        # Create user-specific collection
        user_collection_name = f"user_{doc.user.id}"
        
        embedding_model = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
        
        # We add to the existing collection or create a new one if it doesn't exist
        Chroma.from_documents(
            documents=chunks,
            embedding=embedding_model,
            persist_directory=CHROMA_PATH,
            collection_name=user_collection_name
        )

        doc.ingestion_status = 'SUCCESS'
        doc.save()
        return f"Successfully ingested document ID {user_document_id}"

    except UserDocument.DoesNotExist:
        return f"Error: UserDocument with ID {user_document_id} not found."
    except Exception as e:
        if 'doc' in locals():
            doc.ingestion_status = 'FAILURE'
            doc.save()
        return f"Error processing document ID {user_document_id}: {str(e)}"
    

@shared_task
def generate_chat_title(session_id: int):
    """
    Generates a descriptive title for a chat session based on its first message.
    """
    try:
        session = ChatSession.objects.get(id=session_id)
        # only need the first message to generate a title
        first_message = session.messages.order_by('timestamp').first()

        if not first_message:
            return f"No messages found for session {session_id}."

        # Create a simple chain for title generation
        llm = ChatGroq(model="llama3-8b-8192", temperature=0.2)
        
        prompt = ChatPromptTemplate.from_template(
            "Based on the following user message, create a short, descriptive title (5 words or less) for this conversation.\n\nMessage: '{message}'\n\nTitle:"
        )
        chain = prompt | llm | StrOutputParser()

        # Generate the title
        title = chain.invoke({"message": first_message.message})
        
        # Save the new title to the database
        session.title = title.strip().strip('"') # Clean up any extra quotes
        session.save()

        return f"Successfully generated title for session {session_id}: {title}"
    except ChatSession.DoesNotExist:
        return f"Error: ChatSession with ID {session_id} not found."
    except Exception as e:
        return f"Error generating title for session {session_id}: {str(e)}"