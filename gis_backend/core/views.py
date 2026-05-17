import json

from django.contrib.gis.geos import Point
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from rest_framework import viewsets

from .models import Form, Submission
from .serializers import FormSerializer, SubmissionSerializer


# ---------------------------------------------------------------------------
# DRF ViewSets — REST API endpoints (used by frontend JS or external clients)
# ---------------------------------------------------------------------------

class FormViewSet(viewsets.ModelViewSet):
    """
    Full CRUD REST API endpoint for Form objects.

    Automatically provides:
        GET    /api/forms/         -> list all forms
        POST   /api/forms/         -> create a new form
        GET    /api/forms/{id}/    -> retrieve a single form
        PUT    /api/forms/{id}/    -> full update
        PATCH  /api/forms/{id}/    -> partial update
        DELETE /api/forms/{id}/    -> delete
    """

    queryset = Form.objects.all()
    serializer_class = FormSerializer


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    Full CRUD REST API endpoint for Submission objects.

    Responses are serialized as GeoJSON Feature objects via
    SubmissionSerializer (GeoFeatureModelSerializer).

    Automatically provides:
        GET    /api/submissions/        -> list all submissions
        POST   /api/submissions/        -> create a new submission
        GET    /api/submissions/{id}/   -> retrieve a single submission
        PUT    /api/submissions/{id}/   -> full update
        PATCH  /api/submissions/{id}/   -> partial update
        DELETE /api/submissions/{id}/   -> delete
    """

    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer


# ---------------------------------------------------------------------------
# Template views — server-rendered HTML pages
# ---------------------------------------------------------------------------

def form_builder(request):
    """
    Render the drag-and-drop form builder UI.

    GET /form-builder/
    Template: core/form_builder.html
    """
    return render(request, 'core/form_builder.html')

@require_POST
def save_form(request):
    """
    Persist a new Form created via the form builder.

    POST /save-form/
    Expects a JSON body:
        {
            "name": "Site Inspection",
            "structure": [{"type": "text", "label": "Site Name"}, ...]
        }

    Returns:
        200 OK  -> {"message": "Form saved successfully"}
        405     -> method not allowed (non-POST requests are ignored)
    """
    if request.method == "POST":
        data = json.loads(request.body)

        Form.objects.create(
            name=data['name'],
            structure=data['structure']
        )

        return JsonResponse({"message": "Form saved successfully"})


def forms_list(request):
    """
    Render a pageable list of all available forms.

    GET /forms/
    Template: core/forms_list.html
    Context:
        forms -> QuerySet of all Form objects
    """
    forms = Form.objects.all()
    return render(request, 'core/forms_list.html', {'forms': forms})


def render_form(request, form_id):
    """
    Render a specific form for data entry.

    GET /forms/<form_id>/
    Template: core/render_form.html
    Context:
        form      -> Form model instance
        structure -> JSON string of form.structure (consumed by frontend JS)

    Raises 404 if no Form with the given id exists.
    """
    form = get_object_or_404(Form, id=form_id)

    return render(request, 'core/render_form.html', {
        'form': form,
        # Serialise structure to JSON string so the template can pass it
        # directly to JavaScript without an extra API call.
        'structure': json.dumps(form.structure),
    })

@require_POST
def submit_data(request):
    """
    Accept and persist a form submission, with optional GPS location.

    POST /submit/
    Expects a JSON body:
        {
            "form_id": 1,
            "data": {"site_name": "Tower A", "condition": "Good"},
            "latitude": -1.2921,   # optional — omit or null to skip location
            "longitude": 36.8219   # optional — omit or null to skip location
        }

    Location handling:
        - If both latitude and longitude are present and truthy, a PostGIS
          Point is created (longitude first — GIS convention).
        - If either coordinate is missing or falsy, location is stored as NULL.

    Returns:
        200 OK -> {"message": "Data submitted successfully"}
        405    -> method not allowed (non-POST requests are ignored)
    """
    if request.method == "POST":
        body = json.loads(request.body)

        # Fetch the related form or raise 404 if it doesn't exist
        form = get_object_or_404(Form, id=body['form_id'])

        # Build a Point only when both coordinates are provided and non-empty.
        # Point() expects (longitude, latitude) — note the reversed order
        # vs. the intuitive (lat, lng) convention.
        location = None
        if body.get('latitude') and body.get('longitude'):
            location = Point(
                float(body['longitude']),
                float(body['latitude'])
            )

        Submission.objects.create(
            form=form,
            data=body['data'],
            location=location
        )

        return JsonResponse({'message': 'Data submitted successfully'})