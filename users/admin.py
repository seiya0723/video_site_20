from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser

class CustomUserAdmin(UserAdmin):

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('handle_name', 'email', 'usericon','self_introduction','shop_owner','black_list')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    #管理サイトから追加するときのフォーム
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2',"handle_name","email","usericon"),
        }),
    )

    list_filter         = [ 'shop_owner','black_list']

    list_per_page       = 10
    list_max_show_all   = 20000

    list_display = ('username', 'email', 'handle_name', 'is_staff','shop_owner','black_list')
    search_fields = ('username', 'handle_name', 'email')

admin.site.register(CustomUser, CustomUserAdmin)
