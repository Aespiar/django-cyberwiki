from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # Revisa que la vista esté bien conectada
]