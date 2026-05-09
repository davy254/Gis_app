from rest_framework import viewsets
from .models import Form, Submission
from .serializers import FormSerializer, SubmissionSerializer
import json

from django.shortcuts import render
from django.http import JsonResponse

class FormViewSet(viewsets.ModelViewSet):
    queryset = Form.objects.all()
    serializer_class = FormSerializer


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer


def form_builder(request):

    return render(request, 'core/form_builder.html')


def save_form(request):

    if request.method == "POST":

        data = json.loads(request.body)

        Form.objects.create(
            name=data['name'],
            structure=data['structure']
        )

        return JsonResponse({
            "message": "Form saved successfully"
        })
