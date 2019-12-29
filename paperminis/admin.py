from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import User
from .models import Bestiary
from .models import Creature
from .models import CreatureQuantity

# Register your models here.
# admin.site.register(Creature)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

class BestiaryInline(admin.TabularInline):
    model = CreatureQuantity
    extra = 1

@admin.register(Creature)
class CreatureAdmin(admin.ModelAdmin):
    list_display = ('owner', 'id', 'name', 'size', 'img_url')
    list_filter = ['size']
    fields = ['owner', 'name', 'img_url', 'size']

@admin.register(Bestiary)
class CreatureAdmin(admin.ModelAdmin):
    list_display = ('owner', 'id', 'name')
    fields = ['owner', 'name']
    inlines = [BestiaryInline]
