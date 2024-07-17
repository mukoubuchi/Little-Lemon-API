from rest_framework import serializers
from .models import MenuItem, Category, Cart, Order, OrderItem
from .models import User, Group
from rest_framework.exceptions import PermissionDenied, NotFound
from django.shortcuts import get_object_or_404

class CategorySerializer(serializers.ModelSerializer):
	class Meta:
		model=Category
		fields=['id', 'slug', 'title']

class MenuItemSerializer(serializers.ModelSerializer):
	category=CategorySerializer(read_only=True)
	category_id=serializers.IntegerField()
	class Meta:
		model=MenuItem
		fields=['id', 'title', 'price', 'featured', 'category', 'category_id']

class CartSerializer(serializers.ModelSerializer):
	menuitem=MenuItemSerializer(read_only=True)
	menuitem_id=serializers.IntegerField()
	price = serializers.ReadOnlyField()
	
	class Meta:
		model=Cart
		fields=['user', 'menuitem', 'quantity', 'price', 'unit_price', 'menuitem_id']
	
	def create(self, validated_data):
		validated_data['price'] = validated_data['quantity'] * validated_data['unit_price']
		return super().create(validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
	menuitem=MenuItemSerializer(read_only=True)
	class Meta:
		model=OrderItem
		fields=['menuitem', 'quantity', 'unit_price', 'price']
	
class OrderSerializer(serializers.ModelSerializer):
	orderitem = OrderItemSerializer(many=True, read_only=True)
	class Meta:
		model=Order
		fields=['id','user', 'delivery_crew', 'status', 'total', 'date', 'orderitem']
	
	def update(self, instance, validated_data):
		user = self.context['request'].user

		if user.groups.filter(name="Manager").exists():
			allowed_fields = ['delivery_crew']
			user=get_object_or_404(User, id=validated_data['delivery_crew'].id)
			if user.groups.filter(name="Delivery crew").exists():
				validated_data['delivery_crew'] = user
			else:
				raise NotFound("No such delivery crew")
		elif user.groups.filter(name="Delivery crew").exists():
			allowed_fields = ['status']
		else:
			allowed_fields = []

		for field in validated_data:
			if field in allowed_fields:
				setattr(instance, field, validated_data[field])
			else:
				raise PermissionDenied(f"User does not have permission to update {field}")

		instance.save()
		return instance


class GroupSerializer(serializers.ModelSerializer):
	class Meta:
		model=Group
		fields=['name']

class UserSerializer(serializers.ModelSerializer):
	groups=GroupSerializer(read_only=True, many=True)
	class Meta:
		model=User
		fields=['id','username','first_name', 'last_name', 'groups']