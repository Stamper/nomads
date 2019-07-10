from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from taskz.serializers import UserSerializer, GroupSerializer, TaskSerializer, CommentSerializer
from taskz.models import Task, TaskComment
from taskz.exceptions import TaskStatusException
from taskz.constants import ADMIN_GROUP


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    @action(detail=True, methods=['post'])
    def backward(self, request, pk=None):
        task = get_object_or_404(Task, id=pk)
        try:
            task.backward()
            return Response(TaskSerializer(task).data)

        except TaskStatusException:
            return Response(status=400)

    @action(detail=True, methods=['post'])
    def forward(self, request, pk=None):
        task = get_object_or_404(Task, id=pk)
        try:
            task.forward()
            return Response(TaskSerializer(task).data)

        except TaskStatusException:
            return Response(status=400)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        task = get_object_or_404(Task, id=pk)
        user = get_object_or_404(User, id=request.data.get('user'))
        task.assignees.add(user)
        return Response(status=200)


class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = TaskComment.objects.order_by('-created').all()
    serializer_class = CommentSerializer

    def create(self, request, *args, **kwargs):
        user = request.user
        comment = TaskComment(user=user, task_id=request.data.get('task'), comment=request.data.get('comment'))
        comment.save()
        return Response(CommentSerializer(comment).data)

    def destroy(self, request, pk=None):
        user = request.user

        if user.groups.filter(name=ADMIN_GROUP).exists():
            comment = get_object_or_404(TaskComment, id=pk)
            comment.delete()
            return Response(status=204)

        else:
            return Response(status=400)
