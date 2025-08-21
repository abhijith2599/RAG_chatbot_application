from rest_framework import serializers
from .models import ChatSession, ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):

    class Meta:
        
        model = ChatMessage
        fields = ['id', 'message', 'is_from_ai', 'timestamp']

class ChatSessionSerializer(serializers.ModelSerializer):

    # This nested serializer will include all messages for a session
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'title', 'created_at', 'messages']
        read_only_fields = ['user'] # User is set automatically