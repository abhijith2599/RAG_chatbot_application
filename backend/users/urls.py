from django.urls import path
from .views import *

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('registration/',UserRegistrationView.as_view(),name='user_registration'),
    path('login/',TokenObtainPairView.as_view(),name='token_obtain_pair'),
    path('login/refresh/',TokenRefreshView.as_view(),name='token_refresh'),
    path('documents/upload/', UserDocumentUploadView.as_view(), name='document_upload'),
    path('documents/', UserDocumentListView.as_view(), name='document_list'),
]