
# import getpass
# from langchain.prompts import PromptTemplate
# from langchain.chains import ConversationalRetrievalChain
# from dotenv import load_dotenv

'''No need for loading dotenv(), django will automatically do it on startup, so write it on manage.py , wsgi/asgi.py'''
# load_dotenv()

# os.environ["GROQ_API_KEY"] = os.getenv("GROQ_SECRET_KEY")

# if "GROQ_API_KEY" not in os.environ:
#     os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API key: ")


import os
from django.conf import settings
from typing import Dict, List, Any

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

# LCEL new methods which replaces ConversationalRetrievalChain
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from langchain.retrievers.multi_query import MultiQueryRetriever


CHROMA_PATH = os.path.join(settings.BASE_DIR,'chroma_db')

class ChatBot:

    def __init__(self):
        
        self.llm = ChatGroq(
            model = "llama3-70b-8192",
            temperature = 0.4
        )

        self.embedding_model = HuggingFaceEmbeddings(
            model_name = "all-MiniLM-L6-v2"
        )

        self.vector_db = Chroma(
            persist_directory = CHROMA_PATH,
            embedding_function = self.embedding_model,
            collection_name = "document_collection"
        )

        # self.retriever = self.vector_db.as_retriever(search_kwargs={'k': 4})
        self.retriever = self._create_multi_query_retriever()

        self.memory = ConversationBufferWindowMemory(
            memory_key = "chat_history",
            return_messages = True,
            k = 3,
            output_key = 'answer'
        )

        self._rag_chain = self._create_rag_chain()
        self._general_chain = self._create_general_chain()
        self.router = self._create_router()


    def _create_multi_query_retriever(self):

        multi_query_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI language model assistant. Your task is to generate five different versions of the given user question to retrieve relevant documents from a vector database. Provide these alternative questions separated by newlines."),
            ("human", "{question}")
        ])

        generate_queries_chain = (
            multi_query_prompt | self.llm | StrOutputParser() | (lambda x: x.split("\n"))
        )
        
        return MultiQueryRetriever(
            retriever=self.vector_db.as_retriever(search_kwargs={'k': 5}),
            llm_chain=generate_queries_chain,
            include_original=True
        )


    def _create_rag_chain(self):

        # 1. Prompt for rephrasing the question with history
        condense_question_prompt = ChatPromptTemplate.from_messages([
            ("system", "Given a chat history and a follow up question, rephrase the follow up question to be a standalone question."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

        # 2. The history aware retriever
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, condense_question_prompt
        )

        # 3. The main prompt for answering the question using retrieved context
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert AI assistant. Your task is to answer the user's question based ONLY on the provided context. 
            Read all the context snippets carefully, combine information from them if necessary to answer the user's question, and formulate a single, coherent response.
            **IMPORTANT RULE: If the new question is on a completely different topic from the chat history, ignore the chat history and answer the question using only the provided context.**
            If the context does not contain the answer, state that you do not have enough information. Do not use any outside knowledge.
            Context:\n{context}"""),
            ("human", "{input}")
        ])

        # 4. The document combination chain
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)

        # 5. The final retrieval chain
        return create_retrieval_chain(history_aware_retriever, question_answer_chain)


    def _create_general_chain(self):

        prompt = ChatPromptTemplate([
            ("system", "You are a helpful assistant. Answer the following question."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

        return prompt | self.llm | StrOutputParser()
    

    def _create_router(self):

        router_prompt_template = """You are an expert at routing a user's question.
            Given the user's question, classify it as either "RAG" or "General".
            - Choose "RAG" if the retrieved documents seem relevant to the question.
            - Choose "General" if the retrieved documents are not relevant to the question, or if the question is a greeting or general chit-chat.
            Return only the single word "RAG" or "General".
            Retrieved Documents:
            {context}
            Question: {question}
            Classification:"""
        
        router_prompt = ChatPromptTemplate.from_template(router_prompt_template)

        return router_prompt | self.llm | StrOutputParser()


    def ask(self,question: str) -> Dict[str, Any]:

        try:
            # retreiving the document regardless of question (for better routing)
            retrieved_docs = self.retriever.invoke(question)

            # formatting into string for the router
            context_for_router = "\n\n".join([doc.page_content for doc in retrieved_docs])

            topic = self.router.invoke({
                "context":context_for_router,
                "question":question
            })
            
            # Load conversation history for the current turn
            chat_history = self.memory.load_memory_variables({}).get("chat_history", [])

            if "RAG" in topic:
                print("--> Routing to Document-Specific RAG Chain...")
                response = self._rag_chain.invoke({
                    "chat_history":chat_history,
                    "input":question
                })

                answer = response.get("answer", "No answer found.")
                sources = [doc.metadata.get('source', 'Unknown') for doc in response.get('context', [])]

            else:
                print("--> Routing to General Knowledge Chain...")
                answer = self._general_chain.invoke({
                    "chat_history": chat_history,
                    "input": question
                })
                sources = []
            
            # Save the interaction to memory AFTER getting the response
            self.memory.save_context({"input": question}, {"answer": answer})

            return {'answer': answer, 'sources': sources}

        except Exception as e:
            print(f"An exception occurred in the 'ask' method: {e}")

            import traceback
            traceback.print_exc()
            return {'answer': "I'm sorry, an internal error occurred. Please try again.", 'sources': []}