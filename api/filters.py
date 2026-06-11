import django_filters
from backend.models import Ingredients

class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Ingredients
        fields = ['name']
