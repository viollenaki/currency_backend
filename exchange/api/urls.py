from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CurrencyViewSet, OperationViewSet, UserViewSet, reset_database, CustomAuthToken, CurrencyAmountViewSet

router = DefaultRouter()
router.register(r'currencies', CurrencyViewSet)
router.register(r'operations', OperationViewSet)
router.register(r'users', UserViewSet)
router.register(r'currency-amounts', CurrencyAmountViewSet)  # Add this line

urlpatterns = [
    path('', include(router.urls)),
    path('token/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('reset-database/', reset_database, name='reset_database'),
]
