
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegistrationSerializer

class UserRegistrationView(APIView):
	def post(self, request):
		serializer = UserRegistrationSerializer(data=request.data)
		if serializer.is_valid():
			user = serializer.save()
			return Response({
				"id": user.id,
				"email": user.email,
				"username": user.username,
				"first_name": user.first_name,
				"last_name": user.last_name,
				"role": user.role
			}, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
