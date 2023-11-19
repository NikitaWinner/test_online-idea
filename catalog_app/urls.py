# catalog/urls.py
from django.urls import path
from .views import UpdateCatalogView, HomeView

urlpatterns = [
    path('home/', HomeView.as_view(), name='home'),
    path('update_autoru_catalog/', UpdateCatalogView.as_view(), name='update_autoru_catalog'),
]
