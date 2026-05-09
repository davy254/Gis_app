from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import FormViewSet, SubmissionViewSet, form_builder, save_form

router = DefaultRouter()
router.register(r'forms', FormViewSet)
router.register(r'submissions', SubmissionViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('builder/', form_builder),
    path('save-form/', save_form),
]