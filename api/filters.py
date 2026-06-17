from backend.models import Ingredients
from django_filters import rest_framework
from django.contrib.auth import get_user_model
from backend.models import Recipes, UserRecipesSettings, Tags

User = get_user_model()

class RecipesFilter(rest_framework.FilterSet):
    author = rest_framework.ModelChoiceFilter(
        field_name='author',
        queryset=User.objects.all(),
        to_field_name='id'
    )
    tags = rest_framework.ModelChoiceFilter(
        field_name='tags',
        queryset=Tags.objects.all(),
        to_field_name='slug'
    )
    is_in_shopping_cart = rest_framework.ModelChoiceFilter(
        field_name='is_in_shopping_cart',
        queryset=UserRecipesSettings.objects.values_list(
            'is_in_shopping_cart'
        ),
        to_field_name='recipe__id'
    )
    is_favorited = rest_framework.BooleanFilter(
        method='filter_is_favorited'
    )

    class Meta:
        model = Recipes
        fields = ['author', 'tags']
