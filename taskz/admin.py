from django.contrib import admin

from taskz.models import Task, TaskStatus, TaskComment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass


@admin.register(TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ('task', 'status', 'created')


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'comment')
