from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User
from .models import Currency, Operation
from .serializers import UserSerializer, CurrencySerializer, OperationSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAdminUser])
    def remove_user(self, request, pk=None):
        """Remove a user and all associated operations"""
        try:
            user = self.get_object()
            username = user.username
            user.delete()
            return Response(
                {"message": f"User '{username}' has been deleted successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to delete user: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['delete'], permission_classes=[IsAdminUser])
    def delete_currencies(self, request):
        """Delete all currencies from the database"""
        try:
            count = Currency.objects.count()
            Currency.objects.all().delete()
            return Response(
                {"message": f"Successfully deleted {count} currencies"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to delete currencies: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

class OperationViewSet(viewsets.ModelViewSet):
    queryset = Operation.objects.all()
    serializer_class = OperationSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_user(self, request, user_id=None):
        operations = self.queryset.filter(user_id=user_id)
        serializer = self.get_serializer(operations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_date(self, request, date=None):
        operations = self.queryset.filter(date__date=date)
        serializer = self.get_serializer(operations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def get_user_operations(self, request):
        """Get operations for a specific user_id provided as a query parameter"""
        user_id = request.query_params.get('user_id', None)
        if user_id is None:
            return Response(
                {"error": "user_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            operations = Operation.objects.filter(user_id=user_id)
            serializer = self.get_serializer(operations, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve operations: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['delete'], permission_classes=[IsAdminUser])
    def delete_db(self, request):
        """Delete all operations from the database"""
        try:
            count = Operation.objects.count()
            Operation.objects.all().delete()
            return Response(
                {"message": f"Successfully deleted {count} operations"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to delete operations: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
