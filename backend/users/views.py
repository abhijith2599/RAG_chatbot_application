# from django.shortcuts import render

from django.contrib.auth.models import User
from .serializers import *
from .models import UserDocument
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from rest_framework import generics
from chatbot.tasks import process_document_ingestion

# testuser, qwerty
class UserRegistrationView(APIView):

    permission_classes=[AllowAny]

    def post(self,request):

        serializer = UserSerializer(data = request.data)

        # raise_exception will automatically handle validation errors
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response({"message":"user registered sucesfully"},status=status.HTTP_201_CREATED)
    
class UserDocumentUploadView(generics.CreateAPIView):
    """
    API endpoint for uploading documents for a logged-in user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserDocumentSerializer

    def perform_create(self, serializer):
        # When a new document is created, automatically associate it
        # with the currently authenticated user.

        uploaded_file = self.request.data.get('file')

        instance = serializer.save(
            user=self.request.user,
            original_filename=uploaded_file.name
        )
        process_document_ingestion.delay(instance.id)


class UserDocumentListView(generics.ListAPIView):
    """
    API endpoint for listing documents for a logged-in user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserDocumentSerializer

    def get_queryset(self):
        # Only return documents belonging to the currently authenticated user
        return UserDocument.objects.filter(user=self.request.user).order_by('-uploaded_at')



# redis-server.exe  -- use commadn to first run redis
# celery -A core worker -l info -P solo  --- then this command, then runserver