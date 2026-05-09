from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import FormViewSet, SubmissionViewSet

router = DefaultRouter()
router.register(r'forms', FormViewSet)
router.register(r'submissions', SubmissionViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]