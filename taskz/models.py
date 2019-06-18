from django.db import models
from model_utils.models import TimeStampedModel
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from taskz.constants import STATUSES, TASK_STATUS_CHOICES, NEW_TASK_STATUS, LAST_TASK_STATUS
from taskz.exceptions import TaskStatusException
from nomads.celery import notify_user


class Task(models.Model):
    title = models.CharField(max_length=50, default='Task')
    about = models.TextField(blank=True, default='')
    assignees = models.ManyToManyField('auth.User', related_name='tasks', blank=True)

    def __str__(self):
        return self.title

    @property
    def current_status(self):
        return TaskStatus.objects.filter(task=self).order_by('-created').first().status

    def _move(self, direction, limit):
        current = self.current_status
        if self.current_status == limit:
            raise TaskStatusException

        else:
            target = STATUSES[STATUSES.index(current) + direction]
            TaskStatus(task=self, status=target).save()

    def forward(self):
        self._move(1, LAST_TASK_STATUS)

    def backward(self):
        self._move(-1, NEW_TASK_STATUS)



class TaskStatus(TimeStampedModel):
    task = models.ForeignKey('taskz.Task', related_name='statuses', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default=NEW_TASK_STATUS)

    class Meta:
        verbose_name_plural = 'Task statuses'


class TaskComment(TimeStampedModel):
    user = models.ForeignKey('auth.User', related_name='comments', on_delete=models.CASCADE)
    task = models.ForeignKey('taskz.Task', related_name='comments', on_delete=models.CASCADE)
    comment = models.TextField()


@receiver(post_save, sender=Task)
def save_task(sender, instance, **kwargs):
    if instance.statuses.count() == 0:
        TaskStatus(task=instance).save()

@receiver(m2m_changed, sender=Task.assignees.through)
def user_assigned(sender, instance, **kwargs):
    action = kwargs.get('action', None)
    pk_set = kwargs.get('pk_set', None)
    if action == 'post_add':
        for user_id in list(pk_set):
            notify_user.delay(instance, user_id)
