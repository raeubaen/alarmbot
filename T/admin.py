from django import forms
from django.contrib import admin
from .models import Bot, User, Plaque, Celebrity
from django.contrib.admin.widgets import FilteredSelectMultiple
# Register your models here.

class Plaque_Inline(admin.StackedInline):
    model = Plaque

class User_Admin(admin.ModelAdmin):
    inlines = [
        Plaque_Inline,
    ]

class Plaque_Admin(admin.ModelAdmin):
    filter_horizontal = ("celebrities",)

admin.site.register(User, User_Admin)
admin.site.register(Plaque, Plaque_Admin)
admin.site.register(Bot)
admin.site.register(Celebrity)

