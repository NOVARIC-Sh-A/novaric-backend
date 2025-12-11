from unittest.mock import patch

def test_profile_enrichment(client):
    with patch("routers.profile_enrichment.ProfileAdvisor.generate_checklist") as mock_adv:
        mock_adv.return_value = [
            {"id": "1", "task": "Improve bio", "is_completed": False}
        ]

        with patch("supabase.Client.table") as mock_table:

            # fake DB response
            class MockQuery:
                def select(self, *a): return self
                def eq(self, *a): return self
                def single(self): return self
                def execute(self): return type("X", (), {"data": {"id": "1", "name": "Test"}})

            mock_table.return_value = MockQuery()

            r = client.get("/profile/1")
            assert r.status_code == 200
            assert "improvement_checklist" in r.json()
