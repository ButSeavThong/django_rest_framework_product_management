from django.contrib import admin
from products.models import Product
# Register your models here.

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ['id', 'name', 'price', 'stock', 'category', 'created_at']
    search_fields = ['name', 'category']
    list_filter   = ['category']