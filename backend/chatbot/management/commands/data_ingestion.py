# these are used to interact with os and to do file operations (like del)
import os
import shutil

# import django project settings, give access to BASE_DIR and other's
from django.conf import settings
from django.core.management.base import BaseCommand  # Need for to inherit this

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings

PROJECT_ROOT = os.path.dirname(settings.BASE_DIR)
PDFS_PATH = os.path.join(PROJECT_ROOT,'pdfs')
CHROMA_PATH = os.path.join(settings.BASE_DIR,'chroma_db')

class Command(BaseCommand):

    help = 'Ingests PDF documents into the Chroma vector store.'

    def handle(self,*args,**options) -> None:

        self.stdout.write(self.style.SUCCESS("--- Starting Data Ingestion ---"))   # Same as print

        # 1. Loading Documents

        documents = []
        if not os.path.exists(PDFS_PATH):
            self.stdout.write(self.style.ERROR(f"PDFs directory not found at: {PDFS_PATH}"))
            return
        
        for file in os.listdir(PDFS_PATH):
            if file.endswith('.pdf'):
                pdf_path = os.path.join(PDFS_PATH,file)
                loader = PyPDFLoader(pdf_path)
                documents.extend(loader.load())
                self.stdout.write(f"Sucessfully loaded : {file}")

        if not documents:
            self.stdout.write(self.style.ERROR("No PDF document found to ingest"))
            return
        
        self.stdout.write(f"Loaded a total of {len(documents)} pages from all PDFs.")

        # 2. Splitting Documents

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 300,
            chunk_overlap = 180,
            length_function = len,  # Function to compute the length of the text
            separators=["\n\n", "\n", ".", " "]
        )

        chunks = text_splitter.split_documents(documents)
        self.stdout.write(self.style.SUCCESS(f"Split documents into {len(chunks)} chunks."))

        # 3. Deleting Vector DB if it exist

        if os.path.exists(CHROMA_PATH):
            self.stdout.write(self.style.WARNING("Existing ChromaDB found. Removing it..."))
            shutil.rmtree(CHROMA_PATH)

        self.stdout.write("Creating new ChromaDB and embedding documents...")

        # 4. Initializing an Embedding Model

        embedding_model = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

        Chroma.from_documents(
            documents = chunks,
            embedding =  embedding_model,
            persist_directory = CHROMA_PATH,
            collection_name = "document_collection"
        )

        self.stdout.write(self.style.SUCCESS(f"--- Data Ingestion Complete. Vector store created at {CHROMA_PATH} ---"))