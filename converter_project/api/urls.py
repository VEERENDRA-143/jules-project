from django.urls import path
from . import views

urlpatterns = [
    path('convert/', views.convert_file_view, name='convert_file'),
]
