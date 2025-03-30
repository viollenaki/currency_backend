from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .models import Currency, Operation, CurrencyAmount
from .serializers import UserSerializer, CurrencySerializer, OperationSerializer, CurrencyAmountSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.db import connection  # Import connection for executing raw SQL

# Add this new API view at the top of the file
@api_view(['POST'])
@permission_classes([IsAdminUser])
def reset_database(request):
    """Reset the entire database (except admin users)"""
    try:
        # Count items before deletion for reporting
        operation_count = Operation.objects.count()
        currency_count = Currency.objects.count()
        
        # Delete all operations
        Operation.objects.all().delete()
        
        # Delete all currencies and reset their primary key sequence
        with connection.cursor() as cursor:
            Currency.objects.all().delete()
            # Reset the primary key sequence for the Currency table (MySQL-specific)
            cursor.execute("ALTER TABLE api_currency AUTO_INCREMENT = 1;")
        
        # Delete non-admin users (optional - comment out if you want to keep users)
        # Get superuser IDs to preserve them
        admin_ids = User.objects.filter(is_superuser=True).values_list('id', flat=True)
        # Delete non-admin users
        deleted_users = User.objects.exclude(id__in=admin_ids).delete()[0]
        
        return Response({
            "message": "Database reset successful",
            "deleted": {
                "operations": operation_count,
                "currencies": currency_count,
                "users": deleted_users  # Will be 0 if user deletion is commented out
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "error": f"Failed to reset database: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def add_user(self, request):
        """Add a new user (accessible only to staff users)"""
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            is_staff = request.data.get('is_staff', False)
            is_superuser = request.data.get('is_superuser', False)

            if not username or not password:
                return Response(
                    {"error": "Username and password are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
            # Create the user
            user = User.objects.create(
                username=username,
                password=make_password(password),  # Hash the password
                is_staff=is_staff,
                is_superuser=is_superuser
            )
            return Response(
                {"message": f"User '{user.username}' created successfully."},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to create user: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def get_user(self, request, pk=None):
        """Retrieve a specific user's details"""
        try:
            user = self.get_object()
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve user: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def change_password(self, request, pk=None):
        """Change a user's password (accessible only to staff users)"""
        try:
            user = self.get_object()
            new_password = request.data.get('new_password')

            if not new_password:
                return Response(
                    {"error": "New password is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update the user's password
            user.password = make_password(new_password)
            user.save()
            return Response(
                {"message": f"Password for user '{user.username}' updated successfully."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to change password: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Override get_queryset to ensure we always get a fresh count from the database
        """
        # Clear queryset cache to ensure fresh results
        if hasattr(self, '_queryset'):
            delattr(self, '_queryset')
        
        # Return a fresh queryset
        return Currency.objects.all()
    
    def create(self, request, *args, **kwargs):
        """
        Override the create method to handle duplicate currency codes
        """
        code = request.data.get('code', '').upper()  # Ensure the code is uppercase
        if Currency.objects.filter(code=code).exists():
            return Response(
                {"error": f"Currency with code '{code}' already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Proceed with the default creation process
        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['delete'], permission_classes=[IsAdminUser])
    def delete_currencies(self, request):
        """Delete all currencies from the database and reset the primary key sequence"""
        try:
            count = Currency.objects.count()
            Currency.objects.all().delete()
            
            # Reset the primary key sequence for the Currency table
            with connection.cursor() as cursor:
                # For PostgreSQL
                cursor.execute("ALTER SEQUENCE exchange_currency_id_seq RESTART WITH 1;")
                
                # For MySQL
                # cursor.execute("ALTER TABLE exchange_currency AUTO_INCREMENT = 1;")
                
                # For SQLite, no need to reset as it automatically resets the sequence when the table is emptied
            
            return Response(
                {"message": f"Successfully deleted {count} currencies and reset the ID sequence"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to delete currencies: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def names(self, request):
        """Get currencies with their IDs and codes"""
        try:
            currencies = Currency.objects.all()
            # Return a list of currency objects with id and code
            currency_data = [{"id": currency.id, "code": currency.code} for currency in currencies]
            return Response(currency_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve currencies: {str(e)}"},
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

class CurrencyAmountViewSet(viewsets.ModelViewSet):
    queryset = CurrencyAmount.objects.all()
    serializer_class = CurrencyAmountSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Override create to associate the logged-in user with the currency amount"""
        user = request.user
        currency_id = request.data.get('currency_id')
        amount = request.data.get('amount')

        if not currency_id or not amount:
            return Response(
                {"error": "currency_id and amount are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            currency = Currency.objects.get(id=currency_id)
        except Currency.DoesNotExist:
            return Response(
                {"error": "Currency does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if the user already added an amount for this currency
        currency_amount, created = CurrencyAmount.objects.get_or_create(
            user=user,
            currency=currency,
            defaults={'amount': amount}
        )

        if not created:
            return Response(
                {"error": f"Currency amount for '{currency.code}' already exists for this user."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(currency_amount)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CustomAuthToken(ObtainAuthToken):
    """
    Custom auth token view that also returns user ID and username
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser
        })
