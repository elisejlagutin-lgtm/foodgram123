from django_filters import rest_framework
from django.contrib.auth import get_user_model
from .models import Recipes, UserRecipesSettings, Tags, Ingredients

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
        method='filter_is_in_shopping_cart'
    )
    is_favorited = rest_framework.BooleanFilter(
        method='filter_is_favorited'
    )


    def filter_is_favorited(self, queryset, name, value):
        return queryset

    class Meta:
        model = Recipes
        fields = ['author', 'tags', 'is_in_shopping_cart']


# filters.py
import django_filters

class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Ingredients
        fields = ['name']

