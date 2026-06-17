from rest_framework import viewsets, permissions, status
from backend.models import (Recipes,
                            Tags,
                            Ingredients,
                            UserRecipesSettings,
                            UserSubscriptionsSettings)
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from .filters import RecipesFilter
from .permisions import IsAuthor
from django.shortcuts import get_object_or_404
import base64
from django.core.files.base import ContentFile
from rest_framework.authtoken.models import Token
from .serializers import (RecipesSerializer,
                        CustomUserSerializer,
                        TagsSerializer,
                        HomePageSerializer,
                        UserMeSerializer,
                        IngredientsSerializer,
                        EmailAuthTokenSerializer,
                        ShopCardSerializer)
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet

User = get_user_model()


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


@api_view(['POST', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def my_avatar(request):
    """Функция для работы с аватаром текущего пользователя"""

    data = request.data.get('avatar')
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
        elif self.action in ['destroy', 'update']:
            return [permissions.IsAuthenticated(), IsAuthor()]
        else:
            return [permissions.AllowAny()]

    def _check_status(self, user, recipe, field_name, yes_or_not):
        existing = UserRecipesSettings.objects.filter(
            user=user,
            recipe=recipe,
            field_name=yes_or_not
        ).exists()
        if existing:
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )

    def  _get_user_recipe_setting(self, user, recipe):
        return UserRecipesSettings.objects.get_or_create(
                user=user,
                recipe=recipe
            )

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
            self._check_status(
                user=user,
                recipe=recipe,
                field_name='is_favorited',
                yes_or_not=True
            )
            setting.is_favorited = True
            setting.save()
            return Response(
                {
                    'id': recipe.id,
                    'name': recipe.name,
                    'image': recipe.image,
                    'cooking_time': recipe.cooking_time
                },
                status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            setting, created = UserRecipesSettings.objects.get_or_create(
                user=user,
                recipe=recipe
            )
            self._check_status(
                user=user,
                recipe=recipe,
                field_name='is_favorited',
                yes_or_not=False
            )
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
        if request.method == 'POST':
            setting, created = UserRecipesSettings.objects.get_or_create(
                user=user,
                recipe=recipe
            )
            self._check_status(
                user=user,
                recipe=recipe,
                field_name='is_in_shopping_cart',
                yes_or_not=True
            )
            setting.is_in_shopping_cart = True
            setting.save()
            return Response(
                {
                    'id': recipe.id,
                    'name': recipe.name,
                    'image': recipe.image,
                    'cooking_time': recipe.cooking_time
                },
                status=status.HTTP_201_CREATED
            )
        if request.method == 'DELETE':
            setting, created = UserRecipesSettings.objects.get_or_create(
                user=user,
                recipe=recipe
            )
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
        if 'id' in self.kwargs or self.action == 'list' or 'me' in self.request.path:
            return UserMeSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action in ['destroy', 'update'] or 'me' in self.request.path:
            return [permissions.IsAuthenticated()]
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
        serializer = UserMeSerializer(subscribed_users, many=True, context={'request': request})
        return Response(
            serializer.data
        )

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
            creator_recipes = Recipes.objects.filter(
                author=creator
            )
            serializer = RecipesSerializer(creator_recipes, many=True, context={'request': request})
            setting.is_subscribed = True
            setting.save()
            return Response(
                {
                    "email": creator.email,
                    "id": creator.id,
                    "username": creator.username,
                    "first_name": creator.first_name,
                    "last_name": creator.last_name,
                    "is_subscribed": setting.is_subscribed,
                    "recipes": serializer.data,
                    "avatar": creator.avatar,
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

    http_method_names = ('get', 'head', 'options',)
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    permission_classes = [permissions.AllowAny]


class IngredientViewSet(viewsets.ModelViewSet):
    """Вью сет для ингредиентов"""

    http_method_names = ('get', 'head', 'options',)
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer


class ShopCartViewSet(viewsets.ModelViewSet):
    """Вью сет для списка покупок"""

    http_method_names = ('post', 'delete')
    queryset = Recipes.objects.all()
    serializer_class = ShopCardSerializer


class HomeAPIView(APIView):
    """Вьюсет для главной страницы"""

    def list(self, request):
        serializer = HomePageSerializer(
            instance=None,
            context={'request': request}
        )
        return Response(serializer.data)
