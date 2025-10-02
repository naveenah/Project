import logging
from django.db import models

logger = logging.getLogger(__name__)

class PageVisits(models.Model):
    """This class builds the model to store the page visits by users
    The blow field represent a databse table with one more additional
    field called id -> which is a hidden field representing Primary Key"""
    path = models.TextField(blank = True, null=True)
    timestamp = models.DateTimeField(auto_now_add = True)

    def save(self, *args, **kwargs):
        logger.info(f"Page visit recorded for path: {self.path}")
        super().save(*args, **kwargs)
# Create your models here.
