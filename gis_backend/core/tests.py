import json

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.gis.geos import Point

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Form, Submission
from core.serializers import FormSerializer, SubmissionSerializer


# =========================================================
# TEST CASE: FORM MODEL
# =========================================================
class FormModelTestCase(TestCase):

    # -----------------------------------------------------
    # Test: Form creation and field integrity
    # Ensures a Form can be created with valid data
    # and JSON structure is stored correctly.
    # -----------------------------------------------------
    def test_form_creation(self):
        form = Form.objects.create(
            name="Site Inspection Form",
            description="Used for field inspections",
            structure=[
                {"type": "text", "label": "Site Name"},
                {"type": "number", "label": "Height"}
            ]
        )

        self.assertEqual(Form.objects.count(), 1)
        self.assertEqual(form.name, "Site Inspection Form")
        self.assertIsInstance(form.structure, list)

    # -----------------------------------------------------
    # Test: Default value of structure field
    # Ensures JSONField default is properly set to empty list
    # -----------------------------------------------------
    def test_form_default_structure(self):
        form = Form.objects.create(name="Empty Form")

        self.assertEqual(form.structure, [])
        self.assertIsInstance(form.structure, list)

    # -----------------------------------------------------
    # Test: String representation of Form model
    # Ensures admin display and debugging output is readable
    # -----------------------------------------------------
    def test_form_str(self):
        form = Form.objects.create(name="GIS Form")

        self.assertEqual(str(form), "GIS Form")


# =========================================================
# TEST CASE: SUBMISSION MODEL
# =========================================================
class SubmissionModelTestCase(TestCase):

    # -----------------------------------------------------
    # Setup: Runs before each test
    # Creates a reusable Form instance for submissions
    # -----------------------------------------------------
    def setUp(self):
        self.form = Form.objects.create(
            name="Survey Form",
            structure=[
                {"type": "text", "label": "Name"}
            ]
        )

    # -----------------------------------------------------
    # Test: Creating a submission
    # Ensures submissions are linked to forms correctly
    # and JSON data is stored without corruption
    # -----------------------------------------------------
    def test_submission_creation(self):
        submission = Submission.objects.create(
            form=self.form,
            data={"Name": "Tower A"}
        )

        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(submission.form, self.form)
        self.assertEqual(submission.data["Name"], "Tower A")

    # -----------------------------------------------------
    # Test: GIS PointField storage
    # Ensures spatial coordinates are correctly stored
    # and retrievable using GeoDjango Point object
    # -----------------------------------------------------
    def test_submission_location_field(self):
        point = Point(36.8219, -1.2921)  # (longitude, latitude)

        submission = Submission.objects.create(
            form=self.form,
            data={"Name": "Site A"},
            location=point
        )

        self.assertIsNotNone(submission.location)
        self.assertEqual(submission.location.x, 36.8219)
        self.assertEqual(submission.location.y, -1.2921)

    # -----------------------------------------------------
    # Test: Cascade delete behavior
    # Ensures that deleting a Form removes all related Submissions
    # -----------------------------------------------------
    def test_form_cascade_deletes_submissions(self):
        Submission.objects.create(
            form=self.form,
            data={"Name": "Site A"}
        )

        self.assertEqual(Submission.objects.count(), 1)

        # Delete parent form
        self.form.delete()

        # Ensure child submissions are also deleted
        self.assertEqual(Submission.objects.count(), 0)

    # -----------------------------------------------------
    # Test: Default ordering (newest first)
    # Ensures dashboard queries always return latest data first
    # -----------------------------------------------------
    def test_submission_ordering(self):
        s1 = Submission.objects.create(form=self.form, data={"a": 1})
        s2 = Submission.objects.create(form=self.form, data={"a": 2})

        submissions = Submission.objects.all()

        self.assertEqual(submissions[0], s2)
        self.assertEqual(submissions[1], s1)

# =========================================================
# TEST CASE: FORM SERIALIZER
# =========================================================
class FormSerializerTestCase(TestCase):

    # -----------------------------------------------------
    # Test: Serialize Form model correctly
    # Ensures serializer outputs expected fields and values
    # -----------------------------------------------------
    def test_form_serializer_output(self):

        form = Form.objects.create(
            name="Site Inspection",
            description="Inspection checklist",
            structure=[
                {"type": "text", "label": "Site Name"}
            ]
        )

        serializer = FormSerializer(form)

        self.assertEqual(serializer.data["name"], "Site Inspection")
        self.assertEqual(
            serializer.data["description"],
            "Inspection checklist"
        )

        self.assertEqual(len(serializer.data["structure"]), 1)

    # -----------------------------------------------------
    # Test: Create Form using serializer
    # Ensures serializer saves valid data correctly
    # -----------------------------------------------------
    def test_form_serializer_create(self):

        payload = {
            "name": "Road Survey",
            "description": "Road condition collection",
            "structure": [
                {"type": "number", "label": "Road Width"}
            ]
        }

        serializer = FormSerializer(data=payload)

        self.assertTrue(serializer.is_valid())

        form = serializer.save()

        self.assertEqual(form.name, "Road Survey")
        self.assertEqual(Form.objects.count(), 1)

    # -----------------------------------------------------
    # Test: ID field is read-only
    # Ensures API clients cannot override primary keys
    # -----------------------------------------------------
    def test_form_serializer_id_read_only(self):

        payload = {
            "id": 999,
            "name": "Protected Form",
            "structure": []
        }

        serializer = FormSerializer(data=payload)

        self.assertTrue(serializer.is_valid())

        form = serializer.save()

        # Django should ignore client-provided ID
        self.assertNotEqual(form.id, 999)

    # -----------------------------------------------------
    # Test: Missing required name field
    # Ensures serializer validation catches invalid input
    # -----------------------------------------------------
    def test_form_serializer_missing_name(self):

        payload = {
            "description": "Missing name",
            "structure": []
        }

        serializer = FormSerializer(data=payload)

        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    # -----------------------------------------------------
    # Test: Empty structure allowed
    # Ensures dynamic forms can initially contain no fields
    # -----------------------------------------------------
    def test_form_serializer_empty_structure(self):

        payload = {
            "name": "Blank Form",
            "structure": []
        }

        serializer = FormSerializer(data=payload)

        self.assertTrue(serializer.is_valid())


# =========================================================
# TEST CASE: SUBMISSION SERIALIZER
# =========================================================
class SubmissionSerializerTestCase(TestCase):

    # -----------------------------------------------------
    # Setup reusable Form object
    # -----------------------------------------------------
    def setUp(self):

        self.form = Form.objects.create(
            name="GIS Survey",
            structure=[
                {"type": "text", "label": "Site"}
            ]
        )

    # -----------------------------------------------------
    # Test: Serialize Submission as GeoJSON
    # Ensures GeoFeatureModelSerializer outputs valid structure
    # -----------------------------------------------------
    def test_submission_geojson_output(self):

        submission = Submission.objects.create(
            form=self.form,
            data={"Site": "Tower A"},
            location=Point(36.8219, -1.2921)
        )

        serializer = SubmissionSerializer(submission)

        # GeoJSON structure assertions
        self.assertEqual(serializer.data["type"], "Feature")

        self.assertIn("geometry", serializer.data)
        self.assertIn("properties", serializer.data)

    # -----------------------------------------------------
    # Test: Geometry coordinates correctness
    # Ensures PointField serializes accurately
    # -----------------------------------------------------
    def test_submission_geometry_coordinates(self):

        submission = Submission.objects.create(
            form=self.form,
            data={"Site": "Tower B"},
            location=Point(36.8219, -1.2921)
        )

        serializer = SubmissionSerializer(submission)

        geometry = serializer.data["geometry"]

        # Ensure geometry exists
        self.assertIsNotNone(geometry)

        # If geometry is returned as GeoJSON dict
        if isinstance(geometry, dict):

            coordinates = geometry["coordinates"]

            self.assertEqual(coordinates[0], 36.8219)
            self.assertEqual(coordinates[1], -1.2921)

        # If geometry is returned as WKT string
        elif isinstance(geometry, str):

            self.assertIn("POINT", geometry)
            self.assertIn("36.8219", geometry)
    # -----------------------------------------------------
    # Test: Submission creation using serializer
    # Ensures valid payloads are saved correctly
    # -----------------------------------------------------
    def test_submission_serializer_create(self):

        payload = {
            "form": self.form.id,
            "data": {
                "Site": "Road A"
            },
            "location": {
                "type": "Point",
                "coordinates": [36.8219, -1.2921]
            }
        }

        serializer = SubmissionSerializer(data=payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        submission = serializer.save()

        self.assertEqual(submission.form, self.form)
        self.assertEqual(submission.data["Site"], "Road A")

    # -----------------------------------------------------
    # Test: Read-only fields protection
    # Ensures clients cannot override auto-managed fields
    # -----------------------------------------------------
    def test_submission_read_only_fields(self):

        payload = {
            "id": 999,
            "created_at": "2020-01-01T00:00:00Z",
            "form": self.form.id,
            "data": {"Site": "Protected"},
            "location": {
                "type": "Point",
                "coordinates": [36.8219, -1.2921]
            }
        }

        serializer = SubmissionSerializer(data=payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        submission = serializer.save()

        self.assertNotEqual(submission.id, 999)

    # -----------------------------------------------------
    # Test: Missing form relationship
    # Ensures submissions cannot exist without parent form
    # -----------------------------------------------------
    def test_submission_missing_form(self):

        payload = {
            "data": {"Site": "No Form"},
            "location": {
                "type": "Point",
                "coordinates": [36.8219, -1.2921]
            }
        }

        serializer = SubmissionSerializer(data=payload)

        self.assertFalse(serializer.is_valid())
        self.assertIn("form", serializer.errors)

    # -----------------------------------------------------
    # Test: Invalid geometry payload
    # Ensures malformed GeoJSON is rejected
    # -----------------------------------------------------
    def test_submission_invalid_geometry(self):

        payload = {
            "form": self.form.id,
            "data": {"Site": "Invalid Geometry"},
            "location": {
                "type": "Point",
                "coordinates": ["bad", "data"]
            }
        }

        serializer = SubmissionSerializer(data=payload)

        self.assertFalse(serializer.is_valid())
        self.assertIn("location", serializer.errors)

    # -----------------------------------------------------
    # Test: Submission without location allowed
    # Ensures nullable PointField behaves correctly
    # -----------------------------------------------------
    def test_submission_without_location(self):

        payload = {
            "form": self.form.id,
            "data": {"Site": "No GPS"}
        }

        serializer = SubmissionSerializer(data=payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        submission = serializer.save()

        self.assertIsNone(submission.location)


# =========================================================
# TEST CASE: TEMPLATE VIEWS
# =========================================================
class TemplateViewsTestCase(TestCase):

    # -----------------------------------------------------
    # Setup reusable objects
    # -----------------------------------------------------
    def setUp(self):

        self.client = Client()

        self.form = Form.objects.create(
            name="GIS Survey",
            structure=[
                {"type": "text", "label": "Site Name"}
            ]
        )

    # -----------------------------------------------------
    # Test: Form builder page renders successfully
    # -----------------------------------------------------
    def test_form_builder_view(self):

        response = self.client.get("/builder/")

        self.assertEqual(response.status_code, 200)

    # -----------------------------------------------------
    # Test: Forms list page renders correctly
    # -----------------------------------------------------
    def test_forms_list_view(self):

        response = self.client.get("/forms/")

        self.assertEqual(response.status_code, 200)

        # Ensure form appears in template context
        self.assertContains(response, "GIS Survey")

    # -----------------------------------------------------
    # Test: Render specific form page
    # -----------------------------------------------------
    def test_render_form_view(self):

        response = self.client.get(f"/render-form/{self.form.id}/")

        self.assertEqual(response.status_code, 200)

        # Ensure form object is passed correctly
        self.assertContains(response, "GIS Survey")

    # -----------------------------------------------------
    # Test: Invalid form returns 404
    # -----------------------------------------------------
    def test_render_form_invalid_id(self):

        response = self.client.get("/render-form/9999/")

        self.assertEqual(response.status_code, 404)


# =========================================================
# TEST CASE: SAVE FORM VIEW
# =========================================================
class SaveFormViewTestCase(TestCase):

    # -----------------------------------------------------
    # Setup Django test client
    # -----------------------------------------------------
    def setUp(self):

        self.client = Client()

    # -----------------------------------------------------
    # Test: Save form successfully
    # -----------------------------------------------------
    def test_save_form_success(self):

        payload = {
            "name": "Inspection Form",
            "structure": [
                {"type": "text", "label": "Site"}
            ]
        }

        response = self.client.post(
            "/save-form/",
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(Form.objects.count(), 1)

        form = Form.objects.first()

        self.assertEqual(form.name, "Inspection Form")

    # -----------------------------------------------------
    # Test: GET request should fail or return None
    # -----------------------------------------------------
    def test_save_form_invalid_method(self):

        response = self.client.get("/save-form/")

        self.assertEqual(response.status_code, 405)


# =========================================================
# TEST CASE: SUBMIT DATA VIEW
# =========================================================
class SubmitDataViewTestCase(TestCase):

    # -----------------------------------------------------
    # Setup reusable form object
    # -----------------------------------------------------
    def setUp(self):

        self.client = Client()

        self.form = Form.objects.create(
            name="Field Survey",
            structure=[
                {"type": "text", "label": "Condition"}
            ]
        )

    # -----------------------------------------------------
    # Test: Submit data successfully with GPS
    # -----------------------------------------------------
    def test_submit_data_with_location(self):

        payload = {
            "form_id": self.form.id,
            "data": {
                "Condition": "Good"
            },
            "latitude": -1.2921,
            "longitude": 36.8219
        }

        response = self.client.post(
            "/submit-data/",
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(Submission.objects.count(), 1)

        submission = Submission.objects.first()

        # Ensure GIS Point saved correctly
        self.assertEqual(submission.location.x, 36.8219)
        self.assertEqual(submission.location.y, -1.2921)

    # -----------------------------------------------------
    # Test: Submit data without GPS
    # Ensures nullable PointField works correctly
    # -----------------------------------------------------
    def test_submit_data_without_location(self):

        payload = {
            "form_id": self.form.id,
            "data": {
                "Condition": "Fair"
            }
        }

        response = self.client.post(
            "/submit-data/",
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        submission = Submission.objects.first()

        self.assertIsNone(submission.location)

    # -----------------------------------------------------
    # Test: Invalid form ID returns 404
    # -----------------------------------------------------
    def test_submit_data_invalid_form(self):

        payload = {
            "form_id": 9999,
            "data": {
                "Condition": "Bad"
            }
        }

        response = self.client.post(
            "/submit-data/",
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 404)

    # -----------------------------------------------------
    # Test: Invalid request method
    # -----------------------------------------------------
    def test_submit_data_invalid_method(self):

        response = self.client.get("/submit-data/")

        self.assertNotEqual(response.status_code, 200)


# =========================================================
# TEST CASE: FORM VIEWSET API
# =========================================================
class FormViewSetTestCase(TestCase):

    # -----------------------------------------------------
    # Setup DRF API client
    # -----------------------------------------------------
    def setUp(self):

        self.client = APIClient()

        self.form = Form.objects.create(
            name="API Form",
            structure=[]
        )

    # -----------------------------------------------------
    # Test: List forms API
    # -----------------------------------------------------
    def test_list_forms(self):

        response = self.client.get("/api/forms/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 1)

    # -----------------------------------------------------
    # Test: Create form via API
    # -----------------------------------------------------
    def test_create_form(self):

        payload = {
            "name": "New GIS Form",
            "structure": [
                {"type": "text", "label": "Name"}
            ]
        }

        response = self.client.post(
            "/api/forms/",
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Form.objects.count(), 2)

    # -----------------------------------------------------
    # Test: Retrieve single form
    # -----------------------------------------------------
    def test_retrieve_form(self):

        response = self.client.get(f"/api/forms/{self.form.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["name"], "API Form")

    # -----------------------------------------------------
    # Test: Delete form
    # -----------------------------------------------------
    def test_delete_form(self):

        response = self.client.delete(f"/api/forms/{self.form.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(Form.objects.count(), 0)


# =========================================================
# TEST CASE: SUBMISSION VIEWSET API
# =========================================================
class SubmissionViewSetTestCase(TestCase):

    # -----------------------------------------------------
    # Setup reusable objects
    # -----------------------------------------------------
    def setUp(self):

        self.client = APIClient()

        self.form = Form.objects.create(
            name="Submission API Form",
            structure=[]
        )

        self.submission = Submission.objects.create(
            form=self.form,
            data={"Site": "Tower A"},
            location=Point(36.8219, -1.2921)
        )

    # -----------------------------------------------------
    # Test: List submissions API
    # -----------------------------------------------------
    def test_list_submissions(self):

        response = self.client.get("/api/submissions/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # -----------------------------------------------------
    # Test: Retrieve single submission
    # -----------------------------------------------------
    def test_retrieve_submission(self):

        response = self.client.get(
            f"/api/submissions/{self.submission.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # -----------------------------------------------------
    # Test: Delete submission
    # -----------------------------------------------------
    def test_delete_submission(self):

        response = self.client.delete(
            f"/api/submissions/{self.submission.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(Submission.objects.count(), 0)


