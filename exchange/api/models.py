from django.db import models
from django.contrib.auth.models import User

class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)
       
    def save(self, *args, **kwargs):
        # Convert code to uppercase before saving
        self.code = self.code.upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"({self.code})"
    
    class Meta:
        verbose_name_plural = "Currencies"

class CurrencyAmount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="currency_amounts")
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="amounts")
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.currency.code}: {self.amount} (Added by {self.user.username})"

class Operation(models.Model):
    OPERATION_TYPES = (
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='operations')
    amount = models.DecimalField(max_digits=10, decimal_places=2, 
                               help_text="Amount of currency bought or sold")
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, 
                               help_text="Exchange rate at which currency was bought or sold")
    operation_type = models.CharField(max_length=4, choices=OPERATION_TYPES, default='BUY')
    date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        operation = "Bought" if self.operation_type == 'BUY' else "Sold"
        return f"{self.user.username} {operation} {self.amount} {self.currency.code} at rate {self.exchange_rate} on {self.date.strftime('%Y-%m-%d')}"
