import os
from celery import Celery
from models import SETTINGS


celery_app = Celery("analyzer", broker=SETTINGS.redis_url, backend=SETTINGS.redis_url)
