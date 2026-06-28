import base64
from random import randint, choice
import string

from django.http import FileResponse
import os
from django.conf import settings
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet

from .filters import RecipesFilter, IngredientFilter
from .permisions import IsAuthor
from .serializers import (RecipesSerializer,
                        ReducedRecipeSerializer,
                        CustomUserSerializer,
                        TagsSerializer,
                        HomePageSerializer,
                        UserMeSerializer,
                        IngredientsSerializer,
                        EmailAuthTokenSerializer,
                        ShopCardSerializer)
from .models import (Recipes,
                            Tags,
                            Ingredients,
                            ShortLink,
                            UserRecipesSettings,
                            UserSubscriptionsSettings)

User = get_user_model()
from django.http import HttpResponse

SYMBOLS = string.ascii_lowercase + string.digits


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """Функция для изменения пароля"""

    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    if not user.check_password(current_password):
        return Response(
            {'current_password': 'Неверный текущий пароль'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not new_password:
        return Response(
            {'new_password': 'Новый пароль обязателен'},
            status=status.HTTP_400_BAD_REQUEST
        )
    user.set_password(new_password)
    user.save()
    return Response(
        status=status.HTTP_204_NO_CONTENT
    )


@api_view(['DELETE', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def my_avatar(request):
    """Функция для работы с аватаром текущего пользователя"""

    data = request.data.get('avatar')
    if request.method == 'PUT':
        if not data:
            return Response(
                {'error': 'Не переданы данные аватара'},
                status=status.HTTP_400_BAD_REQUEST
            )

        base64_data = data.split(',', 1)[1] if data.startswith('data:image') else data

        try:
            user = request.user
            user.avatar.save(
                f'avatar_{user.id}.png',
                ContentFile(base64.b64decode(base64_data)),
                save=True
            )
            return Response({
                'avatar': user.avatar.url
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {'error': 'Ошибка обработки изображения'},
                status=status.HTTP_400_BAD_REQUEST
            )
    if request.method == 'DELETE':
        user = request.user
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def obtain_auth_token(request):
    """Функция для получчения токена аутентификации"""

    serializer = EmailAuthTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    token, created = Token.objects.get_or_create(user=user)

    return Response({
        'auth_token': token.key,
    })


@api_view(['POST'])
def logout_view(request):
    """Функция для удаления токена аутентификации"""

    Token.objects.get(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вью сет для работы с рецептами"""

    queryset = Recipes.objects.all()
    serializer_class = RecipesSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['destroy', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsAuthor()]
        else:
            return [permissions.AllowAny()]

    def _check_status(self, user, recipe, field_name, yes_or_not):
        """Возвращает True, если запись с таким статусом уже существует."""
        filters = {
            'user': user,
            'recipe': recipe,
            field_name: yes_or_not
        }
        return UserRecipesSettings.objects.filter(**filters).exists()


    def  _get_user_recipe_setting(self, user, recipe):
        return UserRecipesSettings.objects.get_or_create(
                user=user,
                recipe=recipe
            )

    def creating_link(self, recipe):
        code = ''
        length = randint(3, 8)
        for _ in range(length):
            simvol = choice(SYMBOLS)
            code += simvol
        obj, create = ShortLink.objects.get_or_create(
            recipe=recipe,
            code=code
        )
        return obj.code

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk):
        recipe = self.get_object()
        code = self.creating_link(recipe=recipe)

        return Response({'short-link': request.build_absolute_uri(f'/s/{code}')})

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_list_txt(self, request):
        items = UserRecipesSettings.objects.filter(user=request.user).select_related('recipe')

        if not items.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        lines = []
        lines.append("СПИСОК ПОКУПОК\n")
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item.recipe.name}")
        content = "\n".join(lines)

        response = HttpResponse(content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def is_favorited(self, request, pk):
        user = request.user
        if not user.is_authenticated:
            return Response(
            status=status.HTTP_401_UNAUTHORIZED
        )
        recipe = get_object_or_404(Recipes, pk=pk)
        if request.method == 'POST':
            setting, created = UserRecipesSettings.objects.get_or_create(
                user=user,
                recipe=recipe
            )
            if self._check_status(user, recipe, 'is_favorited', True):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            setting.is_favorited = True
            setting.save()
            serializer = ReducedRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            setting, created = UserRecipesSettings.objects.get_or_create(
                user=user,
                recipe=recipe
            )
            if self._check_status(
                    user=user,
                    recipe=recipe,
                    field_name='is_favorited',
                    yes_or_not=False
                ):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            setting.is_favorited = False
            setting.save()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk):
        user = request.user
        if not user.is_authenticated:
            return Response(
            status=status.HTTP_401_UNAUTHORIZED
        )
        recipe = get_object_or_404(Recipes, pk=pk)
        setting, _ = UserRecipesSettings.objects.get_or_create(user=user, recipe=recipe)
        if request.method == 'POST':
            if self._check_status(user, recipe, 'is_in_shopping_cart', True):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            setting.is_in_shopping_cart = True
            setting.save()
            serializer = ReducedRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            self._check_status(
                user=user,
                recipe=recipe,
                field_name='is_in_shopping_cart',
                yes_or_not=False
            )
            setting.is_in_shopping_cart = False
            setting.save()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )


class CustomUserViewSet(UserViewSet):
    """Кастомный вью сет для работы с пользователями"""

    serializer_class = CustomUserSerializer

    def get_queryset(self):
        if 'me' in self.request.path:
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()

    def get_serializer_class(self):
        if self.action in ('list', 'me') or self.detail:
            return UserMeSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action in ['destroy', 'update'] or 'me' in self.request.path:
            return [permissions.IsAuthenticated(), IsAuthor()]
        return [permissions.AllowAny()]

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def my_subscriptions(self, request):

        user = request.user
        if not user.is_authenticated:
            return Response(
            status=status.HTTP_401_UNAUTHORIZED
        )
        subscriptions_id = UserSubscriptionsSettings.objects.filter(
            subscriber=user,
            is_subscribed=True
        ).values_list('creator_id', flat=True)
        subscribed_users = User.objects.filter(id__in=subscriptions_id)
        page = self.paginate_queryset(subscribed_users)
        serializer = UserMeSerializer(page, many=True, context={'request': request})
        limit = self.request.query_params.get('recipes_limit')
        if limit:
            try:
                limit = int(limit)
                if limit <= 0:
                    limit = None  # или вернуть ошибку 400
            except ValueError:
                limit = None      # если не число — игнорируем лимит

        users_data = serializer.data

        for user_data in users_data:
            user_obj = User.objects.get(id=user_data['id'])
            recipes = Recipes.objects.filter(author=user_obj)
            recipe_serializer = ReducedRecipeSerializer(recipes[:limit], many=True, context={'request': request})
            user_data['recipes'] = recipe_serializer.data
            user_data['recipes_count'] = len(recipe_serializer.data)

        return self.get_paginated_response(users_data)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscriptions(self, request, id=None):
        user = self.request.user
        if not user.is_authenticated:
            return Response(
            status=status.HTTP_401_UNAUTHORIZED
        )
        creator = get_object_or_404(User, pk=id)
        if user == creator:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        setting, created = UserSubscriptionsSettings.objects.get_or_create(
            subscriber=user,
            creator=creator
        )
        if request.method == 'POST':
            #if setting.is_subscribed:
            #    return Response(status=status.HTTP_400_BAD_REQUEST)
            creator_recipes = Recipes.objects.filter(
                author=creator
            )
            limit = self.request.query_params.get('recipes_limit')
            if limit:
                try:
                    limit = int(limit)
                    if limit <= 0:
                        limit = None  # или вернуть ошибку 400
                except ValueError:
                    limit = None      # если не число — игнорируем лимит

            if limit:
                creator_recipes = creator_recipes[:limit]
            serializer = ReducedRecipeSerializer(creator_recipes, many=True, context={'request': request})
            setting.is_subscribed = True
            setting.save()
            if not creator.avatar:
                avatar = None
            else:
                avatar = creator.avatar
            return Response(
                {
                    "email": creator.email,
                    "id": creator.id,
                    "username": creator.username,
                    "first_name": creator.first_name,
                    "last_name": creator.last_name,
                    "is_subscribed": setting.is_subscribed,
                    "recipes": serializer.data,
                    "avatar": avatar,
                    "recipes_count": len(serializer.data)
                },
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            if not setting.is_subscribed:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            setting.is_subscribed = False
            setting.save()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):
    """Вью сет для работы с тегами"""

    http_method_names = ('get', 'head', 'options', 'post',)
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None
    permission_classes = [permissions.AllowAny]


from django_filters.rest_framework import DjangoFilterBackend

class IngredientViewSet(viewsets.ModelViewSet):
    """Вью сет для ингредиентов"""

    http_method_names = ('get', 'head', 'options', 'post',)
    pagination_class = None
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class ShopCartViewSet(viewsets.ModelViewSet):
    """Вью сет для списка покупок"""

    http_method_names = ('post', 'delete')
    queryset = Recipes.objects.all()
    serializer_class = ShopCardSerializer


class HomeAPIViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для главной страницы"""
    serializer_class = HomePageSerializer

    def list(self, request):
        # Путь к статическому файлу фронтенда
        file_path = os.path.join(settings.STATIC_ROOT, 'index.html')

        if os.path.exists(file_path):
            # Отдаём файл как HTTP-ответ
            return FileResponse(
                open(file_path, 'rb'),
                content_type='text/html'
            )
        else:
            # Если файл не найден — отдаём ошибку 404
            from django.http import HttpResponseNotFound
            return HttpResponseNotFound('Frontend not found')
