from model_utils import Choices

STATUSES = ('New', 'In progress', 'Completed', 'Archived')

TASK_STATUS_CHOICES = Choices(*STATUSES)

NEW_TASK_STATUS = STATUSES[0]
LAST_TASK_STATUS = STATUSES[-1]

ADMIN_GROUP = 'ADMIN'
