from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services.rag_pipeline import ChatBot
from .services.chatbot_service import get_bot_instance

# Create your views here.

class ChatAPIView(APIView):

    def post(self, request, *args, **kwargs):

        user_message = request.data.get("message")

        if not user_message:
            return Response(
                {'error': 'Message not provided'}, status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the bot instance. lazy-loading singleton
        bot = get_bot_instance()

        bot_response = bot.ask(user_message)

        return Response(bot_response,status=status.HTTP_200_OK)