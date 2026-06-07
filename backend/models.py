from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

MAX_LEN_TITLE = 125
MAX_LEN_DESCRIPTION = 625


class CustomUser(AbstractUser):
    """Кастомная модель пользователя"""

    is_subscribed = models.BooleanField(default=False)
    avatar = models.ImageField(blank=True, null=True)


User = get_user_model()


class FavoriteRecipe(models.Model):
    """Промежуточная модель для избранных рецептов"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'Recipes',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    class Meta:
        verbose_name_plural = 'Избранные рецепты'

class Ingredients(models.Model):
    """Модель ингридиентов блюда."""

    unit_measurement = models.TextField()
    name = models.TextField(
        max_length=MAX_LEN_TITLE
    )

    class Meta:
        verbose_name_plural = 'Ингредиенты'


class Tags(models.Model):
    """Модель тегов блюда."""

    title = models.TextField(
        max_length=MAX_LEN_TITLE
    )
    slug = models.SlugField()

    class Meta:
        verbose_name_plural = 'Теги'


class Recipes(models.Model):
    """Модель рептов."""

    title = models.TextField(
        max_length=MAX_LEN_TITLE,
        verbose_name='Название рецепта'
    )
    is_publisched = models.BooleanField(
        default=True,
        verbose_name='Разрешение на публикацию'
    )
    date_post = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата публикации'
    )
    image = models.ImageField(
        null=True,
        blank=True,
        verbose_name='Изображение рецепта'
    )
    description = models.TextField(
        max_length=MAX_LEN_DESCRIPTION,
        verbose_name='Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        verbose_name='Ингредиенты'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    tags = models.ManyToManyField(
        Tags,
        verbose_name='Тэги блюда'
    )
    cooking_time = models.IntegerField(
        help_text="Укажите длительность в минутах",
        verbose_name='Время приготовления'
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'Рецепты'
