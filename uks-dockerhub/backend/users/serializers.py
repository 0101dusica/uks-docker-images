
from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password

class UserRegistrationSerializer(serializers.ModelSerializer):
	password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
	class Meta:
		model = User
		fields = ('email', 'username', 'first_name', 'last_name', 'password')

	def create(self, validated_data):
		user = User(
			email=validated_data['email'],
			username=validated_data['username'],
			first_name=validated_data.get('first_name', ''),
			last_name=validated_data.get('last_name', '')
		)
		user.set_password(validated_data['password'])
		user.save()
		return user
