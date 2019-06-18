from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APITestCase

from model_mommy import mommy

from taskz.models import Task, TaskStatus
from taskz.constants import NEW_TASK_STATUS, LAST_TASK_STATUS, STATUSES, ADMIN_GROUP
from taskz.exceptions import TaskStatusException


class TestTaskModel(TestCase):
    def test_new_status(self):
        task = mommy.make('taskz.Task')
        self.assertEqual(task.statuses.count(), 1)

    def test_single_status(self):
        task = mommy.make('taskz.Task')
        task.save()
        task.save()
        task.save()
        self.assertEqual(task.statuses.count(), 1)

    def test_proper_new_status(self):
        task = mommy.make('taskz.Task')
        self.assertEqual(task.statuses.first().status, NEW_TASK_STATUS)

    def test_save_doesnt_corrupt_status(self):
        task = mommy.make('taskz.Task')
        s = task.statuses.first()
        testing_status = 'TESTING'
        s.status = testing_status
        s.save()
        task.save()
        self.assertEqual(task.statuses.first().status, testing_status)

    def test_new_current_status(self):
        task = mommy.make('taskz.Task')
        self.assertEqual(task.current_status, NEW_TASK_STATUS)

    def test_backward_negative(self):
        task = mommy.make('taskz.Task')
        with self.assertRaises(TaskStatusException):
            task.backward()
        self.assertEqual(task.current_status, NEW_TASK_STATUS)

    def test_forward(self):
        task = mommy.make('taskz.Task')
        task.forward()
        self.assertEqual(task.current_status, STATUSES[1])

    def test_backward(self):
        task = mommy.make('taskz.Task')
        task.forward()
        task.backward()
        self.assertEqual(task.current_status, NEW_TASK_STATUS)

    def test_too_far_forward(self):
        task = mommy.make('taskz.Task')
        for i in range(len(STATUSES) - 1):
            task.forward()
        with self.assertRaises(TaskStatusException):
            task.forward()
        self.assertEqual(task.current_status, LAST_TASK_STATUS)


class TestUsersEndpoint(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('user', 'user@example.com', 'password')
        self.user.save()

    def test_auth_negative(self):
        responce = self.client.get('/users/')
        self.assertEqual(responce.status_code, 403)

    def test_auth_positive(self):
        self.client.login(username='user', password='password')
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 200)

    def test_user(self):
        self.client.login(username='user', password='password')
        response = self.client.get('/users/{}/'.format(self.user.id))
        self.assertEqual(response.data.get('username'), self.user.username)


class TestTaskEndpoint(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('user', 'user@example.com', 'password')
        self.user.save()
        self.client.login(username='user', password='password')

    def test_create_new_task(self):
        response = self.client.post('/tasks/', data={'title': 'test'})
        self.assertEqual(response.data.get('title'), 'test')
        self.assertEqual(response.data.get('current_status'), NEW_TASK_STATUS)

    def test_backward_new_task(self):
        task = self.client.post('/tasks/', data={'title': 'test'})
        response = self.client.post('/tasks/{}/backward/'.format(task.data.get('id')))
        self.assertEqual(response.status_code, 400)

    def test_forward_new_task(self):
        task = self.client.post('/tasks/', data={'title': 'test'})
        response = self.client.post('/tasks/{}/forward/'.format(task.data.get('id')))
        self.assertEqual(response.data.get('current_status'), STATUSES[1])

    def test_forward_too_far(self):
        task = self.client.post('/tasks/', data={'title': 'test'})
        for i in range(len(STATUSES)):
            response = self.client.post('/tasks/{}/forward/'.format(task.data.get('id')))
        self.assertEqual(response.status_code, 400)

    @patch('taskz.models.notify_user')
    def test_notify(self, mock_notify):
        task = mommy.make('taskz.Task')
        user = mommy.make('auth.User')
        task.assignees.add(user)
        mock_notify.assert_called_with(task, user.id)


class TestCommentEndpoint(APITestCase):
    def setUp(self):
        self.task = mommy.make('taskz.Task')
        self.user = User.objects.create_superuser('user', 'user@example.com', 'password')
        self.user.save()
        self.client.login(username='user', password='password')

    def test_create_new_comment(self):
        comment = self.client.post('/comments/', data={'user': self.user.id, 'task': self.task.id, 'comment': 'test'})
        self.assertEqual(comment.status_code, 200)
        response = self.client.get('/comments/{}/'.format(comment.data.get('id')))
        self.assertEqual(response.data.get('comment'), 'test')

    def test_cant_delete_comment(self):
        comment = self.client.post('/comments/', data={'user': self.user.id, 'task': self.task.id, 'comment': 'test'})
        response = self.client.delete('/comments/{}/'.format(comment.data.get('id')))
        self.assertEqual(response.status_code, 400)

    def test_delete_by_admin(self):
        comment = self.client.post('/comments/', data={'user': self.user.id, 'task': self.task.id, 'comment': 'test'})
        group = mommy.make('auth.Group', name=ADMIN_GROUP)
        self.user.groups.add(group)
        response = self.client.delete('/comments/{}/'.format(comment.data.get('id')))
        self.assertEqual(response.status_code, 204)


class TestAssignment(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('user', 'user@example.com', 'password')
        self.user.save()
        self.client.login(username='user', password='password')

    def test_assign(self):
        task = self.client.post('/tasks/', data={'title': 'test'})
        response = self.client.get('/tasks/{}/'.format(task.data.get('id')))
        self.assertNotIn(self.user.id, response.data.get('assignees'))
        self.client.post('/tasks/{}/assign/'.format(task.data.get('id')), data={'user': self.user.id})
        response = self.client.get('/tasks/{}/'.format(task.data.get('id')))
        self.assertIn(self.user.id, response.data.get('assignees'))

    @patch('taskz.models.notify_user')
    def test_notify(self, mock_notify):
        task = self.client.post('/tasks/', data={'title': 'test'})
        self.client.post('/tasks/{}/assign/'.format(task.data.get('id')), data={'user': self.user.id})
        mock_notify.assert_called_with(Task.objects.get(id=task.data.get('id')), self.user.id)
