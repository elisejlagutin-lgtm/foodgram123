from rest_framework import serializers
from djoser.serializers import UserSerializer
import base64
from django.core.files.base import ContentFile

from backend.models import Recipes, Tags, Ingredients, CustomUser
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from django.http import Http404
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
    """Сериализатор для аутентификации по текену"""

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

    ingredients = IngredientsSerializer(many=True)
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
            format, imgstr = value.split(';base64,')
            ext = format.split('/')[-1]
            data = base64.b64decode(imgstr)
            file_name = f'recipe_image.{ext}'
            return ContentFile(data, name=file_name)
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        recipe = super().create(validated_data)
        for tag_id in tags_data:
            recipe.tags.add(tag_id)
        for ingredient_data in ingredients_data:
            ingredient = Ingredients.objects.get(pk=ingredient_data['id'])
            recipe.ingredients.add(ingredient)
        return recipe

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError()
        return value

    def validate_tags(self, value):
        if value is None:
            raise serializers.ValidationError('Список тегов не может быть пустым')
        seen = set()
        for tag in value:
            if tag in seen:
                raise serializers.ValidationError()
            seen.add(tag)
        return value

    def validate_ingredients(self, value):
        if value is None:
            raise serializers.ValidationError()
        seen = set()
        for ingredient in value:
            if ingredient['id'] in seen:
                raise serializers.ValidationError()
            try:
                get_object_or_404(Ingredients, id=ingredient['id'])
            except Http404:
                raise serializers.ValidationError()
            seen.add(ingredient['id'])
        return value

    def validate(self, data):
        ingredients = data.get('ingredients')
        if 'tags' not in data:
            raise serializers.ValidationError()
        if not ingredients:
            raise serializers.ValidationError()
        return data

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


class HomePageSerializer(serializers.Serializer):
    recipes = serializers.SerializerMethodField()

    def get_last_recipes(self, obj):
        recipes = Recipes.objects.order_by('-data_post')[:6]
        return RecipesSerializer(recipes, many=True).data