from django.urls import path
from . import views

app_name = 'bingo'

urlpatterns = [
    path('create/', views.CreateGameView.as_view(), name='create_game'),
    path('admin/<str:game_id>/', views.GameAdminView.as_view(), name='game_admin'),
    path('games/<str:game_id>/state/', views.get_game_state, name='game_state'),  # ADD THIS
    path('games/<str:game_id>/call/', views.call_phrase, name='call_phrase'),
    path('games/<str:game_id>/<str:board_uuid>/', views.BoardView.as_view(), name='board_view'),
]