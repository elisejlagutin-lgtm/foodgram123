from rest_framework import viewsets, permissions
from backend.models import Recipes, Tags, Ingredients, FavoriteRecipe
from .serializers import (RecipesSerializer,
                        UserSerializer,
                        TagsSerializer,
                        FavoriteRecipeSerializer,
                        IngredientsSerializer,
                        ShopCardSerializer)
from django.contrib.auth import get_user_model

User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    """Вью сет для работы с рецептами"""

    queryset = Recipes.objects.all()
    serializer_class = RecipesSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update']:
            return [permissions.IsAuthenticated()]
        else:
            return [permissions.AllowAny()]


class FavoriteRecipesViewSet(viewsets.ModelViewSet):
    """Вью сет для работы с избранными рецептами"""

    serializer_class = FavoriteRecipeSerializer
    queryset = FavoriteRecipe.objects.all()


class UserMeViewSet(viewsets.ModelViewSet):
    """Вью сет для работы с текущим пользователем"""

    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)


class TagViewSet(viewsets.ModelViewSet):
    """Вью сет для работы с тегами"""

    http_method_names = ('get', 'head', 'options',)
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    permission_classes = [permissions.AllowAny]


class IngredientViewSet(viewsets.ModelViewSet):
    """Вью сет для ингредиентов"""

    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer


class ShopCartViewSet(viewsets.ModelViewSet):
    """Вью сет для списка покупок"""

    http_method_names = ('post', 'delete')
    queryset = Recipes.objects.all()
    serializer_class = ShopCardSerializer