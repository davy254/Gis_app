from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import Form, Submission

class FormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = '__all__'


class SubmissionSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Submission
        geo_field = "location"
        fields = ('id', 'form', 'data', 'created_at')