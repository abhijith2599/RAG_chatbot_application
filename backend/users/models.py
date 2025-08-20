from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class UserDocument(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    file = models.FileField(upload_to="user_documents/")

    original_filename = models.CharField(max_length=255)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    ingestion_status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('SUCCESS', 'Success'), ('FAILURE', 'Failure')],
        default='PENDING'
    )

    def __str__(self):
        return f"{self.original_filename} ({self.user.username})"