import base64

from rest_framework import serializers
from djoser.serializers import UserSerializer
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.http import Http404

from .models import (Recipes,
                            Tags,
                            Ingredients,
                            CustomUser,
                            UserRecipesSettings,
                            UserSubscriptionsSettings)

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


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # Если полученный объект строка, и эта строка 
        # начинается с 'data:image'...
        if isinstance(data, str) and data.startswith('data:image'):
            # ...начинаем декодировать изображение из base64.
            # Сначала нужно разделить строку на части.
            format, imgstr = data.split(';base64,')  
            # И извлечь расширение файла.
            ext = format.split('/')[-1]  
            # Затем декодировать сами данные и поместить результат в файл,
            # которому дать название по шаблону.
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserMeSerializer(UserSerializer):
    """Сериализатор для модели пользователей"""

    password = serializers.CharField(write_only=True)
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

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

    def get_is_subscribed(self, obj):
        user = self.context['request'].user

        if not user or not user.is_authenticated:
            return False

        if user.is_authenticated:
            return UserSubscriptionsSettings.objects.filter(
                subscriber=user,
                creator=obj,
                is_subscribed=True
            ).exists()


class RecipeIngredientSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(required=False)
    measurement_unit = serializers.CharField(required=False)
    amount = serializers.IntegerField(min_value=1)


class ReducedRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели рецептов"""

    class Meta:
        model = Recipes
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )

class RecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для модели рецептов"""

    ingredients = RecipeIngredientSerializer(many=True)
    ingredient_ids = serializers.PrimaryKeyRelatedField(
        source='ingredients',
        queryset=Ingredients.objects.all(),
        required=False,
        many=True,
        write_only=True
    )
    author = UserMeSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(),
        many=True,
        required=True
    )
    image = Base64ImageField(required=True, allow_null=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = ('id',
                'name',
                'tags',
                'is_favorited',
                'ingredient_ids',
                'is_in_shopping_cart',
                'image',
                'cooking_time',
                'ingredients',
                'text',
                'author')

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.save()
        ingredient_ids = [item['id'] for item in validated_data.get('ingredients', [])]
        tag_ids = validated_data.get('tags', [])
        instance.ingredients.set(ingredient_ids)
        instance.tags.set(tag_ids)
        return instance

    def get_is_favorited(self, obj):
        user = self.context['request'].user

        if not user or not user.is_authenticated:
            return False
        
        if user.is_authenticated:
            return UserRecipesSettings.objects.filter(
                user=user,
                recipe=obj,
                is_favorited=True
            ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user

        if not user or not user.is_authenticated:
            return False
        if user.is_authenticated:
            return UserRecipesSettings.objects.filter(
                user=user,
                recipe=obj,
                is_in_shopping_cart=True
            ).exists()

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        validated_data['date_post'] = timezone.now()
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
        if value is None or value == []:
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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        tags_data = representation.pop('tags')
        tags_qs = Tags.objects.filter(id__in=tags_data)
        representation['tags'] = TagsSerializer(tags_qs, many=True).data
        return representation

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

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)
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

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if request.user.is_authenticated:
            return UserSubscriptionsSettings.objects.filter(
                subscriber=request.user,
                creator=obj,
                is_subscribed=True
            ).exists()


class HomePageSerializer(serializers.Serializer):
    recipes = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        # Фильтрация: только featured товары, отсортированные по цене
        recipes_last = Recipes.objects.filter(
        ).order_by('price')[:5]  # берём первые 5
        serializer = RecipesSerializer(recipes_last, many=True)
        return serializer.data
