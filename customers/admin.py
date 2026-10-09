from django.contrib import admin
from .models import Record

# Register your models here.
@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'city', 'state', 'status', 'owner', 'created_at')
    list_filter = ('status', 'owner')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
