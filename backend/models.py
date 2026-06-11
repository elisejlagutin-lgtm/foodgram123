from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from rest_framework import serializers

MAX_LEN_TITLE = 125
MAX_LEN_DESCRIPTION = 625


class CustomUser(AbstractUser):
    """Кастомная модель пользователя"""

    is_subscribed = models.BooleanField(default=False)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    avatar = models.ImageField()
    email = models.EmailField(
        unique=True,
        blank=False,
        null=False
    )


User = get_user_model()


class Ingredients(models.Model):
    """Модель ингридиентов блюда."""

    measurement_unit = models.TextField()
    name = models.TextField(
        max_length=MAX_LEN_TITLE
    )

    class Meta:
        verbose_name_plural = 'Ингредиенты'


class Tags(models.Model):
    """Модель тегов блюда."""

    name = models.TextField(
        max_length=MAX_LEN_TITLE
    )
    slug = models.SlugField()

    class Meta:
        verbose_name_plural = 'Теги'


class Recipes(models.Model):
    """Модель рептов."""

    name = models.TextField(
        max_length=MAX_LEN_TITLE,
        verbose_name='Название рецепта'
    )
    image = models.TextField()
    is_favorited = models.BooleanField(default=False)
    is_in_shopping_cart = models.BooleanField(default=False)
    text = models.TextField(
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
