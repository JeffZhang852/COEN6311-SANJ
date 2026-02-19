
# used to convert data to JSON format

from rest_framework import serializers
from rest_framework.authtoken.admin import User


#auth api serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = User
        fields = ['id', 'username', 'password', 'email']