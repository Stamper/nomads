from django.contrib.auth.models import User, Group
from rest_framework import serializers

from taskz.models import Task, TaskComment


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('name',)


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.StringRelatedField(many=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'groups')


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'title', 'about', 'current_status', 'comments', 'assignees')


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskComment
        fields = ('id', 'user', 'task', 'comment', 'created', 'modified')
