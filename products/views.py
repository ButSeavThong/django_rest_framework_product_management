from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Product
from .serializers import ProductSerializer


class ProductListCreateView(APIView):
    """
     GET /api/products/       → List all products 
     POST /api/products/      → Create a new product

    """
    def get(self,request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)


class ProductDetailsView(APIView):

    """
    GET    /api/products/<id>/  → Retrieve a single product
    PUT    /api/products/<id>/  → Full update
    PATCH  /api/products/<id>/  → Partial update
    DELETE /api/products/<id>/  → Delete    
    """

    def get_object(self, pk):
        return self.get_object_or_404(Product, pk=pk)
    
    def get(self, request, pk):
        product    = self.get_object(pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
            product    = self.get_object(pk)
            serializer = ProductSerializer(product, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
            product    = self.get_object(pk)
            # partial=True means not all fields are required
            serializer = ProductSerializer(product, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
            product = self.get_object(pk)
            product.delete()
            return Response(
                {"message": "Product deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )