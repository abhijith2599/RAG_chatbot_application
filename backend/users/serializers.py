from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *

class UserSerializer(serializers.ModelSerializer):

    class Meta:

        model = User
        fields = ['username','password']
        extra_kwargs = {'password':{'write_only':True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        # user.save() # user already saved using create_user no need to use again
        return user
    

class UserDocumentSerializer(serializers.ModelSerializer):

    class Meta:

        model = UserDocument
        
        fields = ['id', 'file', 'original_filename', 'uploaded_at', 'ingestion_status']
        # fields: Defines all the fields that will be visible in the API response.

        read_only_fields = ['id', 'original_filename', 'uploaded_at', 'ingestion_status']
        # read_only_fields: Defines a subset of those fields that the client is not allowed to write to.
