from django.urls import path, include
from rest_framework.routers import SimpleRouter

from . import views

other_router = SimpleRouter()
other_router.register(r'subscription', views.SubscriptionViewSet, basename='sub')
other_router.register(r'users', views.CustomUserViewSet, basename='user')
other_router.register(r'shopping_cart', views.ShopCartViewSet, basename='cart_shop')
other_router.register(r'recipes', views.RecipeViewSet, basename='recipes')
other_router.register(r'tags', views.TagViewSet, basename='tags')
other_router.register(r'ingredients', views.IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('auth/token/login/', views.obtain_auth_token, name='token_obtain_pair'),
    path('auth/token/logout/', views.logout_view, name='token_logout'),
    path('users/set_password/', views.change_password, name='change_password'),
    path('users/me/avatar/', views.my_avatar, name='my_avatar'),
    path('', include(other_router.urls)),
]