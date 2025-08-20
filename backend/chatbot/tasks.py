
import os
import shutil
from celery import shared_task
from django.conf import settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from users.models import UserDocument

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