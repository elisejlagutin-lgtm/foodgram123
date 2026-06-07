from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView,
                                            TokenVerifyView)


from . import views


router = SimpleRouter()
router.register(r'shopping_cart', views.ShopCartViewSet, basename='cart_shop')
router.register(r'me', views.UserMeViewSet, basename='me')
router.register(r'recipes', views.RecipeViewSet, basename='recipes')
router.register(r'tags', views.TagViewSet, basename='tags')
router.register(r'ingredients', views.IngredientViewSet, basename='ingredients')
router.register(r'favorite', views.FavoriteRecipesViewSet, basename='favorite')

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('', include(router.urls)),
]