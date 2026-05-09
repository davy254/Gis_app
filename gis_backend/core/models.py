from django.db import models

from django.contrib.gis.db import models

class Form(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    structure = models.JSONField(default=list)  # dynamic form fields

    def __str__(self):
        return self.name


class Submission(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    data = models.JSONField()
    location = models.PointField()  # GPS coordinates
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission {self.id}"
