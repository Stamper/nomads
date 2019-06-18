import os
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nomads.settings')
celery_app = Celery('nomads')
celery_app.config_from_object('django.conf:settings')
celery_app.autodiscover_tasks()


@celery_app.task(bind=True)
def notify_user(task, user_id):
    send_mail(
        'New assignment',
        'You have been assigned to the "{}" task'.format(task.title),
        settings.EMAIL_HOST_USER,
        [User.objects.get(id=user_id).email, ],
        fail_silently=True,
    )
