
# creating the urls here for modular structure

from django.urls import path
from .views import *

urlpatterns  = [
    path('chat/',ChatAPIView.as_view(),name="chat_api"),
]