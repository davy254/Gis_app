from django.contrib.gis.geos import Point
# Standard DRF serializer base classes
from rest_framework import serializers

# GeoFeatureModelSerializer outputs data as GeoJSON FeatureCollection —
# required for any serializer that exposes a spatial (geometry) field.
from rest_framework_gis.serializers import GeoFeatureModelSerializer

# Local models to serialize
from .models import Form, Submission


class FormSerializer(serializers.ModelSerializer):
    """
    Serializer for the Form model.

    Exposes all form fields for CRUD operations via the API.
    Used in list, retrieve, create, and update endpoints.
    """

    class Meta:
        model = Form
        # Expose all model fields: id, name, description, structure
        fields = '__all__'

        # Prevent id from being writable on POST/PUT
        read_only_fields = ('id',)


class SubmissionSerializer(GeoFeatureModelSerializer):
    """
    GeoJSON serializer for the Submission model.

    Inherits from GeoFeatureModelSerializer to render submissions
    as valid GeoJSON Feature objects, with `location` as the geometry.

    Output format example:
    {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [36.8219, -1.2921]
        },
        "properties": {
            "id": 1,
            "form": 2,
            "data": {"site_name": "Tower A"},
            "created_at": "2024-01-15T08:30:00Z"
        }
    }
    """

    class Meta:
        model = Submission

        # The model field to use as the GeoJSON geometry.
        # Must be a spatial field (PointField, PolygonField, etc.)
        geo_field = "location"

        # `location` is excluded from `fields` here —
        # GeoFeatureModelSerializer handles it separately via `geo_field`
        # and places it under the GeoJSON "geometry" key automatically.
        # It is included to support write operations (POST/PATCH)
        # where a GeoJSON Point can be submitted for the location field.
        fields = ('id', 'form', 'data', 'location', 'created_at')

        # Prevent id and created_at from being writable on POST/PUT
        read_only_fields = ('id', 'created_at')

    
    # -----------------------------------------------------
    # Robust GIS validation (handles dict + Point)
    # -----------------------------------------------------

    def validate_location(self, value):


        if value is None:
            return value

        # -----------------------------------------------------
        # CASE 1: Incoming GeoJSON dict
        # -----------------------------------------------------
        if isinstance(value, dict):

            try:
                geometry_type = value.get("type")
                coords = value.get("coordinates", [])

                # Ensure geometry type is Point
                if geometry_type != "Point":
                    raise serializers.ValidationError(
                        "Only Point geometry is supported."
                    )

                longitude = coords[0]
                latitude = coords[1]

            except (IndexError, TypeError):
                raise serializers.ValidationError(
                    "Invalid GeoJSON coordinates."
                )

        # -----------------------------------------------------
        # CASE 2: Already a GeoDjango Point
        # -----------------------------------------------------
        elif isinstance(value, Point):

            longitude = value.x
            latitude = value.y

            return value

        else:
            raise serializers.ValidationError(
                "Invalid location format."
            )

        # -----------------------------------------------------
        # Ensure coordinates are numeric
        # -----------------------------------------------------
        try:
            longitude = float(longitude)
            latitude = float(latitude)

        except (ValueError, TypeError):
            raise serializers.ValidationError(
                "Coordinates must be numeric values."
            )

        # -----------------------------------------------------
        # Validate coordinate ranges
        # -----------------------------------------------------
        if not (-180 <= longitude <= 180):
            raise serializers.ValidationError(
                "Longitude out of range."
            )

        if not (-90 <= latitude <= 90):
            raise serializers.ValidationError(
                "Latitude out of range."
            )

        # -----------------------------------------------------
        # Convert GeoJSON -> GeoDjango Point
        # IMPORTANT FIX
        # -----------------------------------------------------
        return Point(longitude, latitude)
        