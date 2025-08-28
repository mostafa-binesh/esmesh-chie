from rest_framework import serializers
from .models import User


class AuthorPublicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name']
