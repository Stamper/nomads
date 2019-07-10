# Basic task management back-end API
### Installation
`$ pip install -r Requirements.txt`
### Project bootstrap
```
$ python manage.py migrate
$ python manage.py createsuperuser
```

Regular django-based app flow
### Run server
`$ python manage.py runserver`

Visit [127.0.0.1:8000](http://127.0.0.1:8000) to operate with API endpoints and [127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) to see admin dashboard
### Tests
`$ python manage.py test`
### Background tasks worker
`$ celery -A nomads worker -l info`
