from rest_framework import viewsets, permissions, status
from backend.models import Recipes, Tags, Ingredients
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from .filters import RecipesFilter
from .permisions import IsAuthor
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
            'avatar_url': user.avatar.url
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


class SubscriptionViewSet(viewsets.ModelViewSet):
    """Вью сет для работы с подписками пользователей"""

    serializer_class = UserMeSerializer
    def get_queryset(self):
        return User.objects.filter(
            is_subscribed=True
        )


class CustomUserViewSet(UserViewSet):
    """Кастомный вью сет для работы с пользователями"""

    serializer_class = CustomUserSerializer

    def get_queryset(self):
        if 'me' in self.request.path:
            return User.objects.filter(id=self.request.user.id)
        if 'subscriptions' in self.request.path:
            return User.objects.filter(
                is_subscribed=True
            )
        return User.objects.all()

    def get_serializer_class(self):
        if 'id' in self.kwargs or self.action == 'list' or 'me' in self.request.path:
            return UserMeSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action in ['destroy', 'update'] or 'me' in self.request.path:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


class TagViewSet(viewsets.ModelViewSet):
    """Вью сет для работы с тегами"""

    http_method_names = ('get', 'head', 'options', 'post',)
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    permission_classes = [permissions.AllowAny]


class IngredientViewSet(viewsets.ModelViewSet):
    """Вью сет для ингредиентов"""

    http_method_names = ('get', 'head', 'options', 'post',)
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
