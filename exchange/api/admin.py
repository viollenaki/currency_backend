from django.contrib import admin
from .models import Currency, Operation, CurrencyAmount

admin.site.register(Currency)
admin.site.register(Operation)
admin.site.register(CurrencyAmount)
# Register your models here.
