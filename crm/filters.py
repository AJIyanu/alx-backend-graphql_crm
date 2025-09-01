# crm/filters.py
import django_filters
from django.db.models import Q
from .models import Customer, Product, Order


# -------------------- Customer Filter --------------------
class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")

    created_at__gte = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    created_at__lte = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")

    phone_pattern = django_filters.CharFilter(method="filter_phone_pattern")

    def filter_phone_pattern(self, queryset, name, value):
        """
        Example usage: ?phone_pattern=+1
        Returns all customers whose phone starts with the given value
        """
        return queryset.filter(phone__startswith=value)

    class Meta:
        model = Customer
        fields = ["name", "email", "phone"]


# -------------------- Product Filter --------------------
class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    # numeric range filters
    price__gte = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price__lte = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    stock__gte = django_filters.NumberFilter(field_name="stock", lookup_expr="gte")
    stock__lte = django_filters.NumberFilter(field_name="stock", lookup_expr="lte")

    # extra: filter low stock
    low_stock = django_filters.BooleanFilter(method="filter_low_stock")

    def filter_low_stock(self, queryset, name, value):
        """
        Example usage: ?low_stock=true
        Returns all products with stock < 10
        """
        if value:
            return queryset.filter(stock__lt=10)
        return queryset

    class Meta:
        model = Product
        fields = ["name", "price", "stock"]


# -------------------- Order Filter --------------------
class OrderFilter(django_filters.FilterSet):
    total_amount__gte = django_filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    total_amount__lte = django_filters.NumberFilter(field_name="total_amount", lookup_expr="lte")

    order_date__gte = django_filters.DateFilter(field_name="order_date", lookup_expr="gte")
    order_date__lte = django_filters.DateFilter(field_name="order_date", lookup_expr="lte")

    # filter by related fields
    customer_name = django_filters.CharFilter(method="filter_customer_name")
    product_name = django_filters.CharFilter(method="filter_product_name")

    # challenge: filter by product_id
    product_id = django_filters.NumberFilter(method="filter_by_product_id")

    def filter_customer_name(self, queryset, name, value):
        return queryset.filter(customer__name__icontains=value)

    def filter_product_name(self, queryset, name, value):
        return queryset.filter(products__name__icontains=value)

    def filter_by_product_id(self, queryset, name, value):
        return queryset.filter(products__id=value)

    class Meta:
        model = Order
        fields = ["total_amount", "order_date", "customer", "products"]
