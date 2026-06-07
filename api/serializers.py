from rest_framework import serializers
from djoser.serializers import UserSerializer
from django.utils import timezone

from backend.models import Recipes, Tags, Ingredients, CustomUser, FavoriteRecipe


class RecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для модели рецептов"""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(),
        many=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    ingredients = serializers.StringRelatedField()

    class Meta:
        model = Recipes
        fields = ('id',
                'title',
                'is_publisched',
                'tags',
                'image',
                'cooking_time',
                'ingredients',
                'date_post',
                'description',
                'author')
        read_only_fields = ('date_post', 'author', 'is_publisched',)

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        validated_data['author'] = self.context['request'].user
        validated_data['date_post'] = timezone.now()
        validated_data['is_publisched'] = True
        recipe = super().create(validated_data)
        recipe.tags.set(tags_data)
        return recipe


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для избранных рецептов"""

    class Meta:
        model = FavoriteRecipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )

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


class TagsSerializer(serializers.ModelSerializer):
    """Сериализер для модели тегов"""

    class Meta:
        model = Tags
        fields = (
            'id',
            'title',
            'slug',
        )


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиентов"""

    class Meta:
        model = Ingredients
        fields = (
            'id',
            'name',
            'unit_measurement',
        )


class UserSerializer(UserSerializer):
    """Сериализатор для модели пользователей"""

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
