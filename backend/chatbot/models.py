from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class ChatSession(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    title = models.CharField(max_length=255, default="New Chat")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat Session with {self.user.username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ChatMessage(models.Model):

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")

    message = models.TextField()

    is_from_ai = models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sender = "AI" if self.is_from_ai else "User"
        return f"{sender}: {self.message[:50]}..."