from django.contrib import admin
from django.urls import path, include
from bingo.views import healthz

urlpatterns = [
    path('admin/', admin.site.urls),
    path('bingo/', include('bingo.urls')),
    path('healthz', healthz, name="healthz"),
]