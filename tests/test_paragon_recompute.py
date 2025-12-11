from unittest.mock import patch

def test_paragon_recompute(client):
    with patch("etl.metric_loader.load_metrics_for") as mock_loader:
        mock_loader.return_value = {
            "media_mentions": 3,
            "attendance": 90,
            "scandals": 0,
            "sentiment": 0.6
        }

        with patch("etl.scoring_engine.score_metrics") as mock_score:
            mock_score.return_value = {
                "overall_score": 75,
                "dimensions": [
                    {"dimension": "media", "score": 70},
                    {"dimension": "ethics", "score": 90},
                ]
            }

            r = client.post("/api/paragon/recompute/1")
            assert r.status_code == 200
            body = r.json()

            assert body["overall_score"] == 75
            assert len(body["dimensions"]) == 2
            assert body["message"] == "PARAGON score recomputed successfully"
