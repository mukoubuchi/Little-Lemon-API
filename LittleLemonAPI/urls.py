from django.urls import path, include
from .views import category, menuItems, menuItem, managers, delivery_crew, remove_from_manager, remove_from_delivery_crew, cart_items, orders, single_order 

urlpatterns = [
    path('menu-items/', menuItems),
    path('menu-items/<int:id>', menuItem),
    path('groups/manager/users', managers),
    path('groups/manager/users/<int:id>', remove_from_manager),
    path('groups/delivery-crew/users', delivery_crew),
    path('groups/delivery-crew/users/<int:id>', remove_from_delivery_crew),
    path('cart/menu-items/', cart_items),
    path('orders/', orders),
    path('orders/<int:id>', single_order),
    path('category/', category)
]