from django.contrib import admin
from .models import Treasury, TreasuryMovement, Expense, ClientPayment

@admin.register(Treasury)
class TreasuryAdmin(admin.ModelAdmin):
    list_display = ('name', 'center', 'balance', 'initial_balance')
    list_filter = ('center',)

@admin.register(TreasuryMovement)
class TreasuryMovementAdmin(admin.ModelAdmin):
    list_display = ('treasury', 'type', 'amount', 'reference', 'created_at')
    list_filter = ('type', 'treasury')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'center', 'amount', 'date', 'treasury')
    list_filter = ('center', 'category')

@admin.register(ClientPayment)
class ClientPaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'client', 'amount', 'date', 'method', 'status')
    list_filter = ('date', 'method', 'status')
