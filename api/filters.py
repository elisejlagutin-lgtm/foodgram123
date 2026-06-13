from backend.models import Ingredients
from django_filters import rest_framework
from django.contrib.auth import get_user_model
from backend.models import Recipes

User = get_user_model()

class RecipesFilter(rest_framework.FilterSet):
    author = rest_framework.ModelChoiceFilter(
        field_name='author',
        queryset=User.objects.all(),
        to_field_name='id'
    )
    class Meta:
        model = Recipes
        fields = ['author', 'tags']
