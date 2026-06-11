from rest_framework import serializers
from djoser.serializers import UserSerializer
from django.utils import timezone
import base64
from django.core.files.base import ContentFile

from backend.models import Recipes, Tags, Ingredients, CustomUser
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class TagsSerializer(serializers.ModelSerializer):
    """Сериализер для модели тегов"""

    class Meta:
        model = Tags
        fields = (
            'id',
            'name',
            'slug',
        )


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиентов"""

    class Meta:
        model = Ingredients
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email"))
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                               email=email, password=password)

            if not user:
                msg = _('Невозможно войти с указанными учётными данными.')
                raise serializers.ValidationError(msg, code='authorization')
            elif not user.is_active:
                msg = _('Аккаунт не активен.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Необходимо указать "email" и "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email"))
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                               email=email, password=password)

            if not user:
                msg = _('Невозможно войти с указанными учётными данными.')
                raise serializers.ValidationError(msg, code='authorization')
            elif not user.is_active:
                msg = _('Аккаунт не активен.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Необходимо указать "email" и "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

class RecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для модели рецептов"""

    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Recipes
        fields = ('id',
                'name',
                'tags',
                'is_favorited',
                'is_in_shopping_cart',
                'image',
                'cooking_time',
                'ingredients',
                'text',
                'author')

    def validate_image(self, value):
        if isinstance(value, str) and value.startswith('data:image'):
            # Извлекаем формат и данные
            format, imgstr = value.split(';base64,')
            ext = format.split('/')[-1]
            # Декодируем Base64
            data = base64.b64decode(imgstr)
            # Создаём файл
            file_name = f'recipe_image.{ext}'
            return ContentFile(data, name=file_name)
        return value

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        recipe = super().create(validated_data)
        return recipe


class ShopCardSerializer(serializers.ModelSerializer):
    """Сериализатор для покупок"""

    class Meta:
        model = Recipes
        fields = (
            'id',
            'image',
            'name',
            'cooking_time',
        )


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.HiddenField(default=False)
    avatar = serializers.ImageField(write_only=True, required=False)
    password = serializers.CharField(write_only=True)

    class Meta(UserSerializer.Meta):
        model = CustomUser
        fields = (
            'email',
            'username',
            "id",
            "first_name",
            "password",
            "last_name",
            'is_subscribed',
            'avatar',
        )
        read_only_fields = ()

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)  # хешируем пароль
        user.save()
        return user


class UserMeSerializer(UserSerializer):
    """Сериализатор для модели пользователей"""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'email',
            "username",
            "password",
            'id',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
