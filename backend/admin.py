from django.contrib import admin

from backend.models import Ingredients, Recipes, Tags


@admin.register(Recipes)
class RecipesAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'cooking_time', 'date_post')
    list_filter = ('cooking_time', 'date_post')
    search_fields = ('description', 'author__username')


admin.site.register(Ingredients)
admin.site.register(Tags)
