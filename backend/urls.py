from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'backend'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('recipe/<int:pk>/', views.RecipeView.as_view(), name='recipe'),
    path('user_page', views.UserView.as_view(), name='user'),
]