import io
import unittest

from fastapi.testclient import TestClient

from main import app


class OcularApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_register_and_verify_person(self):
        image_bytes = b"fake-image-bytes"
        register_response = self.client.post(
            "/persons/register",
            data={
                "external_id": "EMP-001",
                "display_name": "Alicia Brooks",
                "email": "alicia@example.com",
                "department": "Engineering",
                "role": "Engineer",
            },
            files={"face_image": ("face.jpg", io.BytesIO(image_bytes), "image/jpeg")},
        )

        self.assertEqual(register_response.status_code, 200)
        payload = register_response.json()
        self.assertEqual(payload["status"], "registered")
        self.assertIn("person_id", payload)

        verify_response = self.client.post(
            "/persons/verify",
            files={"face_image": ("face.jpg", io.BytesIO(image_bytes), "image/jpeg")},
        )

        self.assertEqual(verify_response.status_code, 200)
        verify_payload = verify_response.json()
        self.assertTrue(verify_payload["matched"])
        self.assertEqual(verify_payload["person"]["person_id"], payload["person_id"])


if __name__ == "__main__":
    unittest.main()
