from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import CurrencyViewSet, OperationViewSet

router = DefaultRouter()
router.register(r'currencies', CurrencyViewSet)
router.register(r'operations', OperationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', obtain_auth_token, name='api_token_auth'),
]
