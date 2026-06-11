from django.views.generic import ListView, DetailView
from .models import Recipes, Tags, Ingredients
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model

User = get_user_model()

class HomeView(ListView):
    """Вью класс для отрисовки главной страницы"""

    model = Recipes
    paginate_by = 6
    context_object_name = 'recipes'


class RecipeView(DetailView):
    """Вью класс для отрисовки рецепта"""

    model = Recipes



class UserView(LoginRequiredMixin, DetailView):
    """Вью класс для открисовки страницы пользователя"""

    model = User
