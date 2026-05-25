from django.urls import path
from .views import ProductListCreateView, ProductDetailsView

urlpatterns = [
    path("products/", ProductListCreateView.as_view(), name="product-list-create"),
    path("products/<int:pk>/", ProductDetailsView.as_view(), name="product-detail")
] 