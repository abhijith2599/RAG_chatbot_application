# from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from rest_framework.permissions import IsAuthenticated, AllowAny

from .services.rag_pipeline import ChatBot
from .services.chatbot_service import get_bot_instance

from .models import ChatSession
from .serializers import ChatSessionSerializer
from chatbot.tasks import generate_chat_title


# --- view for managing chat sessions ---
class ChatSessionListCreateView(generics.ListCreateAPIView):
    """
    API view to retrieve list of chat sessions or create a new one.
    """
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return sessions belonging to the logged-in user
        return ChatSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically associate the new session with the logged-in user
        serializer.save(user=self.request.user)


# --- view for retrieving a single session's history ---
class ChatSessionDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve a single chat session with all its messages.
    """
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    queryset = ChatSession.objects.all()


# --- view for sending a message ---
class SendMessageAPIView(APIView):
    """
    API View to handle sending a message to a specific chat session.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        session_id = kwargs.get('session_id')
        user_message = request.data.get('message')

        if not session_id or not user_message:
            return Response(
                {'error': 'session_id and message are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Ensure session belongs to the current user
            session = ChatSession.objects.get(id=session_id, user=request.user)
            # Check if this is the first message from the user in this session
            is_first_message = not session.messages.filter(is_from_ai=False).exists()

        except ChatSession.DoesNotExist:
            return Response(
                {'error': 'Chat session not found or access denied.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        bot = get_bot_instance()
        # Pass the session to the ask method to handle history
        bot_response = bot.ask(user_message, session)

        # --- TRIGGERING BACKGROUND TASK ---
        if is_first_message:
            generate_chat_title.delay(session.id)
        
        return Response(bot_response, status=status.HTTP_200_OK)







# class ChatAPIView(APIView):

#     def post(self, request, *args, **kwargs):

#         user_message = request.data.get("message")

#         if not user_message:
#             return Response(
#                 {'error': 'Message not provided'}, status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # Get the bot instance. lazy-loading singleton
#         bot = get_bot_instance()

#         bot_response = bot.ask(user_message)

#         return Response(bot_response,status=status.HTTP_200_OK)