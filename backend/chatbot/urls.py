
# creating the urls here for modular structure

from django.urls import path
from .views import (
    SendMessageAPIView,
    ChatSessionListCreateView,
    ChatSessionDetailView
)

urlpatterns  = [
    # path('chat/',ChatAPIView.as_view(),name="chat_api"),

    path('sessions/<int:session_id>/send/', SendMessageAPIView.as_view(), name='send_message'),
    path('sessions/', ChatSessionListCreateView.as_view(), name='chat_session_list'),
    path('sessions/<int:pk>/', ChatSessionDetailView.as_view(), name='chat_session_detail'),
]