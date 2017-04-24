from django.db import models

# Create your models here.
class Alarm(models.Model):
    text = models.CharField(max_length=200)

    def __unicode__(self):
        return self.text
    def __str__(self):
        return self.__unicode__()