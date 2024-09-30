from django.db import models
import uuid
from simple_history.models import HistoricalRecords
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
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        print("without history")
        self.skip_history_when_saving = True
        if not self.name:
            # Generate a unique name
            base_name = 'Untitled'
            count = 1
            unique_name = base_name

            while Project.objects.filter(name=unique_name).exists():
                unique_name = f'{base_name} {count}'
                count += 1

            self.name = unique_name

        #limit Records to Five
        if Project.objects.count() >= 5:
            oldest_project = Project.objects.order_by('created_at').first()  # or 'created_at' if you have a timestamp
            if oldest_project:
                oldest_project.delete()

        super(Project, self).save(*args, **kwargs)

    def save_with_historical_record(self, *args, **kwargs):
        if not self.name:
            count = Project.objects.filter(name__startswith='Untitled').count() + 1
            self.name = f'Untitled{count}'

        print("with history")
        #limit Records to Five
        if Project.objects.count() >= 5:
            oldest_project = Project.objects.order_by('created_at').first()  # or 'created_at' if you have a timestamp
            if oldest_project:
                oldest_project.delete()

        # limits History Records to five versions
        historical_records = self.history.all()
        excess_records = historical_records.count()
        if excess_records >= 5:
            # Get the IDs of the excess records
            oldest_record = historical_records.order_by('history_date').first()
            if oldest_record:
                oldest_record.delete()
            # Delete the excess historical records

        super(Project, self).save(*args, **kwargs)
