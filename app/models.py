from django.db import models
import uuid
# Create your models here.

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Project(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    f_icons = models.JSONField(default=list, blank=True)
    screen_link =models.URLField(blank=True)

    def save(self, *args, **kwargs):
        if not self.name:
            count = Project.objects.filter(name__startswith='Untitled').count() + 1
            self.name = f'Untitled{count}'
        super(Project, self).save(*args, **kwargs)