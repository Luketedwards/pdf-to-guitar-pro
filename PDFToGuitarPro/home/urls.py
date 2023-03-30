from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload-pdf/', views.upload_pdf, name='upload_pdf'),
]
