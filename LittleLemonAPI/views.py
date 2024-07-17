from django.shortcuts import render, get_object_or_404, get_list_or_404
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import MenuItem, Cart, Order, OrderItem, Category
from django.contrib.auth.models import User, Group
from .serializers import CategorySerializer, MenuItemSerializer, UserSerializer, CartSerializer, OrderSerializer, OrderItemSerializer
from datetime import date
from django.core.paginator import Paginator, EmptyPage
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.exceptions import PermissionDenied, NotFound

# Create your views here.
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def category(request):
    if request.method == 'GET':
        queryset=Category.objects.all()
        serializer=CategorySerializer(queryset, many=True)
        return Response(serializer.data)
    else:
        if request.user.groups.filter(name="Admin").exists():
            serializer = CategorySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response("Category created", 201)
            else:
                return Response(serializer.errors, 400)
        else:
            return Response("Unauthorized", 403)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AnonRateThrottle])
def menuItems(request):
    if request.method == 'GET':
        queryset=MenuItem.objects.select_related('category').all()
        category_name=request.query_params.get("category")
        to_price=request.query_params.get("to_price")
        search=request.query_params.get("search")
        perpage=request.query_params.get("perpage", default=10)
        page=request.query_params.get("page", default=1)
        ordering=request.query_params.get("ordering")

        if category_name:
            queryset=queryset.filter(category__title=category_name)
        if to_price:
            queryset=queryset.filter(price__lte=to_price)
        if search:
            queryset=queryset.filter(title__contains=search)
        if ordering:
            queryset=queryset.order_by(ordering)    
        paginator=Paginator(queryset, per_page=perpage)
        
        try:
            queryset=paginator.page(number=page)
        except EmptyPage:
            queryset = []
        serializer=MenuItemSerializer(queryset, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        if request.user.groups.filter(name__in=["Manager", "Admin"]).exists():
            category = get_object_or_404(Category, id=request.data['category_id'])
            serializer = MenuItemSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, 400)
        else:
            return Response("Unauthorized", 403)

@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def menuItem(request, id):
    if request.method == 'GET':
        item = get_object_or_404(MenuItem, pk=id)   
        serializer = MenuItemSerializer(item)
        return Response(serializer.data)  
    elif request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
        if request.user.groups.filter(name="Manager").exists():
            if request.method == 'POST':
                return Response("Method not allowed on Resource", 405)
            else:
                item = get_object_or_404(MenuItem, pk=id)
                if request.method == 'DELETE':
                    item.delete()
                    return Response('Delete of item successful')
                else:
                    serializer = MenuItemSerializer(item, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return Response(serializer.data)
                    else:
                        return Response(serializer.errors, 400)
        else:
            return Response("Unauthorized", 403) 

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def managers(request):
    if request.user.groups.filter(name="Manager").exists():
        if request.method == 'GET':
            queryset=User.objects.filter(groups__name__in=["Manager"])
            serializer=UserSerializer(queryset, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            user=get_object_or_404(User, username=request.data['username'])
            group = Group.objects.get(name='Manager')
            user.groups.add(group)
            return Response("User assigned to Manager group", 201)
    else:
        return Response("Unauthorized", 403) 

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_manager(request, id):
    if request.user.groups.filter(name="Manager").exists():
        user=get_object_or_404(User, id=id)
        grp = Group.objects.get(name="Manager")
        if grp in user.groups:
            user.groups.remove(grp)
            return Response("User deleted")
        else:
            return Response("User is not part of Manager group", 400)
    else:
        return Response("Unauthorized", 403) 

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def delivery_crew(request):
    if request.user.groups.filter(name="Manager").exists():
        if request.method == 'GET':
            queryset=User.objects.filter(groups__name__in=["Delivery crew"])
            serializer=UserSerializer(queryset, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            user=get_object_or_404(User, username=request.data['username'])
            group = Group.objects.get(name='Delivery crew')
            user.groups.add(group)
            return Response("User assigned to Delivery crew group", 201)
    else:
        return Response("Unauthorized", 403) 
        
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_delivery_crew(request, id):
    if request.user.groups.filter(name="Manager").exists():
        user=get_object_or_404(User, id=id)
        grp = Group.objects.get(name="Delivery crew")
        if user.groups.filter(name="Delivery crew").exists():
            user.groups.remove(grp)
            user.save()
            return Response("User removed from Delivery crew group")
        else:
            return Response("User is not part of Delivery crew group", status=400)
    else:
        return Response("Unauthorized", 403) 
    
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_items(request):
    if request.method == 'GET':
        carts = Cart.objects.filter(user=request.user.id).select_related('menuitem').all()
        serializer = CartSerializer(carts, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
            request.data['user'] = request.user.id
            menuitem = get_object_or_404(MenuItem, id=request.data['menuitem_id'])
            request.data['unit_price'] = menuitem.price
            serializer = CartSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response("Cart saved", 201)
            else:
                return Response(serializer.errors, 400)
    elif request.method == 'DELETE':
        carts = get_list_or_404(Cart, user=request.user)
        for cart in carts:
            cart.delete()
        return Response("Cart items deleted")
    
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def orders(request):
    if request.method == 'GET':
        if request.user.groups.filter(name="Manager").exists():
            queryset=Order.objects.select_related(['user']).all()
        elif request.user.groups.filter(name="Delivery crew").exists():
            queryset=get_list_or_404(Order.objects.prefetch_related('orderitem'), delivery_crew=request.user.id)
        else:
            queryset=get_list_or_404(Order.objects.prefetch_related('orderitem'), user=request.user.id)
        serializer=OrderSerializer(queryset, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        carts = get_list_or_404(Cart, user=request.user)
        order = Order.objects.create(user=request.user, date=date.today(), total=0)
        total = 0
        orderitems=[]
        for cart in carts:
            orderitems.append(OrderItem(
                order=order,
                menuitem=cart.menuitem,
                quantity=cart.quantity,
                unit_price=cart.unit_price,
                price=cart.price
            ))
            total+=cart.price
        Cart.objects.filter(user=request.user).delete()
        OrderItem.objects.bulk_create(orderitems)
        order.total = total
        order.save()
        return Response("Order confirmed", 201)

@api_view(['GET', 'PATCH', 'PUT', 'DELETE'])
def single_order(request, id):
    order = get_object_or_404(Order, id=id)
    if request.method == 'GET':
        queryset=OrderItem.objects.filter(order=order)
        serializer=OrderItemSerializer(queryset)
        return Response(serializer.data)
    elif request.method in ['PUT', 'PATCH']:
        if request.user.groups.filter(name__in=["Manager", "Delivery crew"]).exists():
            serializer=OrderSerializer(order, data=request.data, partial=True, context={'request':request})
            if serializer.is_valid():
                try:
                    serializer.save()
                    return Response(serializer.data)
                except PermissionDenied as e:
                    return Response({"detail": str(e)}, status=403)
                except NotFound as e:
                    return Response({"detail": str(e)}, 404)
            else:
                return Response(serializer.errors, 400)
        else:
            return Response("Unauthorized", 403)
    elif request.method == 'DELETE':
        if request.user.groups.filter(name="Manager").exists():
            order.delete()
            return Response("Order deleted")
        else:
            return Response("Unauthorized", 403)










