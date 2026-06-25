from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

MAX_LEN_TITLE = 125
MAX_LEN_DESCRIPTION = 625


class CustomUser(AbstractUser):
    """Кастомная модель пользователя"""

    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        upload_to='users/', 
        null=True,
        default=None
    )
    email = models.EmailField(
        unique=True,
        blank=False,
        null=False,
        verbose_name='Почта пользователя'
    )


User = get_user_model()


class Ingredients(models.Model):
    """Модель ингридиентов блюда."""

    measurement_unit = models.TextField(
        verbose_name='Единица измерения'
    )
    name = models.TextField(
        max_length=MAX_LEN_TITLE,
        verbose_name='Название ингредиемна'
    )
    amount = models.IntegerField(null=True)

    class Meta:
        verbose_name_plural = 'Ингредиенты'


class Tags(models.Model):
    """Модель тегов блюда."""

    name = models.TextField(
        max_length=MAX_LEN_TITLE,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        verbose_name='Слаг тега'
    )

    class Meta:
        verbose_name_plural = 'Теги'


class ShortLink(models.Model):
    """Модель для получения короткой ссылки на рецепт"""

    recipe = models.ForeignKey(
        'Recipes',
        on_delete=models.CASCADE
    )
    code = models.CharField()

    class Meta:
        unique_together = ('code', 'recipe')


class Recipes(models.Model):
    """Модель рептов."""

    name = models.TextField(
        max_length=MAX_LEN_TITLE,
        verbose_name='Название рецепта'
    )
    date_post = models.DateTimeField()
    is_published = models.BooleanField(default=True)
    image = models.ImageField(
        upload_to='recipes/', 
    )
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


class UserRecipesSettings(models.Model):
    """Модель для личных полей пользователя"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipes, on_delete=models.CASCADE)
    is_in_shopping_cart = models.BooleanField(default=False)
    is_favorited = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'recipe')


class UserSubscriptionsSettings(models.Model):
    """Модель для личных полей подписчика"""

    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions_as_subscriber'
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions_as_creator'
    )
    is_subscribed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('subscriber', 'creator')
