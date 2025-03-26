from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Currency, Operation

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model: User
        fields = ['id', 'username', 'email']

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'

class OperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = '__all__'
