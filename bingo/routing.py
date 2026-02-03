from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/bingo/<str:game_id>/', consumers.BingoGameConsumer.as_asgi()),
]