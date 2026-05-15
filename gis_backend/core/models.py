# GeoDjango models module — superset of standard django.db.models,
# includes spatial field types like PointField, PolygonField, etc.
from django.contrib.gis.db import models


class Form(models.Model):
    """
    Represents a dynamic data collection form.

    Forms are configurable at runtime via the `structure` field, allowing
    different field definitions without requiring schema migrations.
    """

    # Human-readable name for the form (e.g. "Site Inspection Form")
    name = models.CharField(max_length=255)

    # Optional long-form description of the form's purpose or instructions
    description = models.TextField(blank=True)

    # Stores the form's field definitions as a JSON array.
    # Each element typically describes a field: type, label, validation rules, etc.
    # Example: [{"type": "text", "label": "Site Name", "required": true}]
    structure = models.JSONField(default=list)

    def __str__(self):
        # Display the form name in admin and shell representations
        return self.name


class Submission(models.Model):
    """
    Represents a single user submission for a given Form.

    Captures the submitted field values as JSON and optionally records
    the GPS coordinates where the submission was made.
    """

    # Link to the parent form — deleting a Form cascades and removes all its submissions
    form = models.ForeignKey(Form, on_delete=models.CASCADE)

    # The submitted form data as a key-value JSON object.
    # Keys correspond to field identifiers defined in Form.structure.
    # Example: {"site_name": "Tower A", "condition": "Good"}
    data = models.JSONField()

    # Optional GPS coordinates captured at submission time (e.g. from a mobile device).
    # Stored as a PostGIS Point geometry (longitude, latitude).
    # Requires GeoDjango + a spatial database backend (e.g. PostGIS).
    location = models.PointField(null=True, blank=True)

    # Automatically set to the datetime when the submission record is first created.
    # Not editable after creation.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Display the submission ID for easy identification in admin and logs
        return f"Submission {self.id}"

    class Meta:
        # Return submissions newest-first in all default querysets
        ordering = ["-created_at"]