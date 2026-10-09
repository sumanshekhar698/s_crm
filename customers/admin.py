from django.contrib import admin
from .models import Note, Record


class NoteInline(admin.TabularInline):
    model = Note
    extra = 0
    fields = ('body', 'author', 'created_at')
    readonly_fields = ('created_at',)


# Register your models here.
@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'city', 'state', 'status', 'owner', 'created_at')
    list_filter = ('status', 'owner')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    inlines = [NoteInline]


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('record', 'author', 'created_at')
    search_fields = ('body', 'record__first_name', 'record__last_name')
