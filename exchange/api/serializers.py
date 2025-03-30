from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Currency, Operation, CurrencyAmount

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'

class CurrencyAmountSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    currency = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CurrencyAmount
        fields = ['id', 'user', 'currency', 'amount']

class OperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = '__all__'
