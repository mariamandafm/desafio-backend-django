from django.urls import path, include
from inventory import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('auto-parts', views.AutoPartView, basename='auto-part')

app_name = 'inventory'

urlpatterns = [
    path('', include(router.urls)),
]
