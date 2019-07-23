from rest_framework import serializers

from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import ugettext_lazy as _


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user model"""
    password = serializers.CharField(
        style={'input_type': 'password', },
        trim_whitespace=False,
        write_only=True,
        min_length=5
    )

    class Meta:
        model = get_user_model()
        fields = ('email', 'password')

    def create(self, validated_data):
        """Creates a new user and returns it"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Updates a user correctly"""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for authentication and returning token"""
    email = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password', },
        trim_whitespace=False
    )

    def validate(self, attrs):
        """Validate and authenticate the user"""
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        if not user:
            msg = _('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code='authentication')

        attrs['user'] = user
        return attrs
