from django.test import TestCase
from rest_framework.test import APIClient
from .models import Area, Category, Report
from accounts.models import User, AuthorityProfile

class ReportAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="citizen@example.com", password="GoodPassword123!", name="Citizen")
        self.other = User.objects.create_user(email="other@example.com", password="GoodPassword123!", name="Other")
        self.area = Area.objects.create(name="Central", location="Dhaka")
        self.category = Category.objects.create(name="Road damage", type="Infrastructure")
        self.client.force_authenticate(self.user)

    def test_citizen_can_create_and_list_own_report(self):
        response = self.client.post("/api/reports/", {"title": "Broken road", "description": "Large pothole", "area": self.area.id, "category": self.category.id, "location": "Main road"}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["status"], Report.Status.SUBMITTED)
        self.assertEqual(self.client.get("/api/reports/mine/").status_code, 200)
        self.assertEqual(len(self.client.get("/api/reports/mine/").data), 1)

    def test_citizen_cannot_manage_area_or_category(self):
        self.assertEqual(self.client.post("/api/reports/areas/", {"name": "Fake"}, format="json").status_code, 403)
        self.assertEqual(self.client.post("/api/reports/categories/", {"name": "Fake"}, format="json").status_code, 403)

    def test_citizen_can_read_community_report(self):
        report = Report.objects.create(reporter=self.other, title="Private", description="Issue", area=self.area, category=self.category, location="Elsewhere")
        self.assertEqual(self.client.get(f"/api/reports/{report.id}/").status_code, 200)

    def test_unauthenticated_user_cannot_list_reports(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/reports/").status_code, 401)
