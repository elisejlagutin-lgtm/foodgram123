from django.contrib import admin

from .models import Ingredients, Recipes, Tags, CustomUser, UserRecipesSettings


@admin.register(Recipes)
class RecipesAdmin(admin.ModelAdmin):
    list_display = ('name', 'author__username',)
    search_fields = ('name', 'author__username', 'tags_slug',)

admin.site.register(CustomUser)
admin.site.register(Ingredients)
admin.site.register(Tags)
admin.site.register(UserRecipesSettings)