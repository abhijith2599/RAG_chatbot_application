import os
from django.conf import settings
from typing import Dict, Any, List

from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.retrievers.multi_query import MultiQueryRetriever
from chatbot.models import ChatMessage, ChatSession
from langchain_core.messages import AIMessage, HumanMessage

CHROMA_PATH = os.path.join(settings.BASE_DIR, 'chroma_db')

class ChatBot:

    def __init__(self):

        self.llm = ChatGroq(
            model="llama3-70b-8192", temperature=0.4
        )

        self.embedding_model = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

        self.vector_db = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=self.embedding_model
        )

        # chain and retriever will be created dynamically inside the 'ask' method.

    def ask(self, question: str, session: ChatSession) -> Dict[str, Any]:

        # Save the user's message to the database first.
        ChatMessage.objects.create(session=session, message=question, is_from_ai=False)

        try:
            # --- Step 1: Create a User-Specific Retriever This is created dynamically for each request. ---

            user_collection_name = f"user_{session.user.id}"

            # Create user-specific vector DB instance
            user_vector_db = Chroma(
                persist_directory=CHROMA_PATH,
                embedding_function=self.embedding_model,
                collection_name=user_collection_name
            )

            base_retriever = user_vector_db.as_retriever(search_kwargs={'k': 5})

            # user_collection_name = f"user_{session.user.id}"
            
            # base_retriever = self.vector_db.as_retriever(
            #     search_kwargs={'k': 5},
            #     # This ensures we only search this user's documents
            #     collection_name=user_collection_name
            # )
            
            multi_query_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an AI language model assistant. Your task is to generate five different versions of the given user question to retrieve relevant documents from a vector database. Provide these alternative questions separated by newlines."),
                ("human", "{question}")
            ])

            generate_queries_chain = (
                multi_query_prompt | self.llm | StrOutputParser() | (lambda x: x.split("\n"))
            )

            retriever = MultiQueryRetriever(
                retriever=base_retriever,
                llm_chain=generate_queries_chain,
                include_original=True
            )

            # --- Step 2: Build Chat History from the Database ---
            recent_messages = session.messages.order_by('timestamp').all()
            chat_history = []

            for msg in recent_messages:
                if msg.is_from_ai:
                    chat_history.append(AIMessage(content=msg.message))
                else:
                    chat_history.append(HumanMessage(content=msg.message))
            
            # --- Step 3: Route the question ---
            retrieved_docs = retriever.invoke(question)
            context_for_router = "\n\n".join([doc.page_content for doc in retrieved_docs])
            
            router_prompt = ChatPromptTemplate.from_template(
                """You are an expert at routing a user's question. 
            Given the user's question, classify it as either "RAG" or "General".
            - Choose "RAG" if the retrieved documents seem relevant to the question.
            - Choose "General" if the retrieved documents are not relevant to the question, or if the question is a greeting or general chit-chat.
            Return only the single word "RAG" or "General".
                Retrieved Documents:
                \n{context}\n\nQuestion: {question}\nClassification:"""
            )

            router_chain = router_prompt | self.llm | StrOutputParser()
            topic = router_chain.invoke({"context": context_for_router, "question": question})

            # --- Step 4: Execute the Correct Chain ---
            if "RAG" in topic:
                print("--> Routing to Document-Specific RAG Chain...")
                
                condense_question_prompt = ChatPromptTemplate.from_messages([
                    ("system", "Given a chat history and a follow up question, rephrase the follow up question to be a standalone question."),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}")
                ])

                history_aware_retriever = create_history_aware_retriever(
                    self.llm, retriever, condense_question_prompt
                )
                
                qa_prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are an expert AI assistant. Your task is to answer the user's question based ONLY on the provided context. 
                    Read all the context snippets carefully, combine information from them if necessary, and formulate a single, coherent response.
                    If the context does not contain the answer, state that you do not have enough information. Do not use any outside knowledge. 
                     Context:\n{context}"""),
                    ("human", "{input}")
                ])

                question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
                
                rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

                response = rag_chain.invoke({"chat_history": chat_history, "input": question})

                answer = response.get("answer", "No answer found.")
                sources = [doc.metadata.get('source', 'Unknown') for doc in response.get('context', [])]

            else:
                print("--> Routing to General Knowledge Chain...")
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a helpful assistant. Answer the following question."),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}")
                ])

                general_chain = prompt | self.llm | StrOutputParser()
                answer = general_chain.invoke({"chat_history": chat_history, "input": question})
                sources = []

            # Save the AI's response to the database
            ChatMessage.objects.create(session=session, message=answer, is_from_ai=True)

            return {'answer': answer, 'sources': sources}

        except Exception as e:

            print(f"An exception occurred in the 'ask' method: {e}")

            import traceback
            traceback.print_exc()

            return {'answer': "I'm sorry, an internal error occurred.", 'sources': []}
        


# Context:\n{context}

# You are an expert AI assistant. Your task is to answer the user's question based ONLY on the provided context. 
                    # Read all the context snippets carefully, combine information from them if necessary to answer the user's question, and formulate a single, coherent response.
                    # **IMPORTANT RULE: If the new question is on a completely different topic from the chat history, ignore the chat history and answer the question using only the provided context.**
                    # If the context does not contain the answer, state that you do not have enough information. Do not use any outside knowledge.