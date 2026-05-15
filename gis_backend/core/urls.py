from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core.views import (
    FormViewSet,
    SubmissionViewSet,
    form_builder,
    forms_list,
    render_form,
    save_form,
    submit_data,
)

# ---------------------------------------------------------------------------
# DRF Router — auto-generates REST API URL patterns for registered ViewSets
# ---------------------------------------------------------------------------

router = DefaultRouter()

# Registers the following endpoints for FormViewSet:
#   GET/POST   /api/forms/
#   GET/PUT/PATCH/DELETE /api/forms/{id}/
router.register(r'forms', FormViewSet)

# Registers the following endpoints for SubmissionViewSet:
#   GET/POST   /api/submissions/
#   GET/PUT/PATCH/DELETE /api/submissions/{id}/
router.register(r'submissions', SubmissionViewSet)


# ---------------------------------------------------------------------------
# URL patterns
# ---------------------------------------------------------------------------

urlpatterns = [

    # --- REST API ---
    # Mounts all router-generated API routes under /api/
    # e.g. /api/forms/, /api/submissions/, /api/forms/{id}/
    path('api/', include(router.urls)),

    # --- Form Builder UI ---
    # Renders the drag-and-drop form builder page
    path('builder/', form_builder, name='form-builder'),

    # Accepts POST request to persist a newly built form
    path('save-form/', save_form, name='save-form'),

    # --- Form List & Rendering ---
    # Lists all available forms
    path('forms/', forms_list, name='forms-list'),

    # Renders a specific form for data entry by its primary key
    path('render-form/<int:form_id>/', render_form, name='render-form'),

    # --- Data Submission ---
    # Accepts POST with form data and optional GPS coordinates
    path('submit-data/', submit_data, name='submit-data'),
]