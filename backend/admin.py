from django.contrib import admin

from backend.models import Ingredients, Recipes, Tags


@admin.register(Recipes)
class RecipesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'cooking_time')
    list_filter = ('cooking_time',)
    search_fields = ('description', 'author__username')


admin.site.register(Ingredients)
admin.site.register(Tags)
