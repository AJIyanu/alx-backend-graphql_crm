import graphene
import re
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from .filters import CustomerFilter, ProductFilter, OrderFilter



# =========================
# Object Types (GraphQL representation of models)
# =========================
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (relay.Node,)
        filterset_class = CustomerFilter
        fields = ("id", "name", "email", "phone", "created_at")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (relay.Node,)
        filterset_class = ProductFilter
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (relay.Node,)
        filterset_class = OrderFilter
        fields = ("id", "customer", "products", "order_date", "total_amount")

# --- QUERIES ---

class CustomerFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String()
    email_icontains = graphene.String()
    created_at_gte = graphene.Date()
    created_at_lte = graphene.Date()
    phone_pattern = graphene.String()

class CustomFilterConnectionField(DjangoFilterConnectionField):
    @classmethod
    def resolve_queryset(cls, connection, iterable, info, args, filtering_args, filterset_class):
        # Pop the filter input if provided
        filter_input = args.pop("filter", None)
        if filter_input:
            # Flatten filter dict into args (so django-filter can understand)
            for key, value in filter_input.items():
                args[key] = value
        return super().resolve_queryset(connection, iterable, info, args, filtering_args, filterset_class)
    
class Query(graphene.ObjectType):
    all_customers = CustomFilterConnectionField(
        CustomerType,
        filter=CustomerFilterInput(),
        order_by=graphene.List(of_type=graphene.String)
    )
    all_products = DjangoFilterConnectionField(
        ProductType,
        order_by=graphene.List(of_type=graphene.String)
    )
    all_orders = DjangoFilterConnectionField(
        OrderType,
        order_by=graphene.List(of_type=graphene.String)
    )

    # --- Resolvers for ordering ---
    def resolve_all_customers(root, info, order_by=None, **kwargs):
        qs = Customer.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_all_products(root, info, order_by=None, **kwargs):
        qs = Product.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_all_orders(root, info, order_by=None, **kwargs):
        qs = Order.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs


# =========================
# MUTATIONS
# =========================

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)


    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, input=None):

        name = input.get('name')
        email = input.get('email')
        phone = input.get('phone')

        # Validate email uniqueness
        if Customer.objects.filter(email=email).exists():
            return CreateCustomer(success=False, message="Email already exists", customer=None)

        # Validate phone format if provided
        if phone:
            if not re.match(r"^\+?\d{7,15}$|^\d{3}-\d{3}-\d{4}$", phone):
                return CreateCustomer(success=False, message="Invalid phone format", customer=None)

        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(success=True, message="Customer created successfully", customer=customer)


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input=None):
        created = []
        errors = []

        from django.db import transaction
        import re

        with transaction.atomic():
            for data in input:
                try:
                    # Email uniqueness
                    if Customer.objects.filter(email=data.email).exists():
                        errors.append(f"Email {data.email} already exists")
                        continue

                    # Phone format
                    if data.phone and not re.match(r"^\+?\d{7,15}$|^\d{3}-\d{3}-\d{4}$", data.phone):
                        errors.append(f"Invalid phone format for {data.email}")
                        continue

                    c = Customer.objects.create(
                        name=data.name,
                        email=data.email,
                        phone=data.phone
                    )
                    created.append(c)

                except Exception as e:
                    errors.append(str(e))

        return BulkCreateCustomers(customers=created, errors=errors)



class ProductInput(graphene.InputObjectType):
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, input=None):

        name = input.get('name')
        price = Decimal(str(input.get('price')))
        stock = input.get('stock', 0)

        if Decimal(price) <= 0:
            return CreateProduct(success=False, message="Price must be positive", product=None)

        if stock < 0:
            return CreateProduct(success=False, message="Stock cannot be negative", product=None)

        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(success=True, message="Product created successfully", product=product)

class OrderInput(graphene.InputObjectType):
        customer_id = graphene.String(required=True)
        product_ids = graphene.List(graphene.String, required=True)
        order_date = graphene.DateTime(required=False)

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, input=None):
        customer_id = int(input.get('customer_id'))
        product_ids = [int(p_id) for p_id in input.get('product_ids')]
        order_date = input.get('order_date')

        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(success=False, message="Invalid customer ID", order=None)

        if not product_ids:
            return CreateOrder(success=False, message="At least one product required", order=None)

        products = Product.objects.filter(id__in=product_ids)
        if not products.exists():
            return CreateOrder(success=False, message="Invalid product IDs", order=None)

        total = sum([p.price for p in products])

        order = Order.objects.create(customer=customer, total_amount=total)
        order.products.set(products)

        return CreateOrder(success=True, message="Order created successfully", order=order)


# =========================
# ROOT MUTATION
# =========================
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
