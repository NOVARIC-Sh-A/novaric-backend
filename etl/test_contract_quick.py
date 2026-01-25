from etl.metrics_contract import scraper_to_canonical, canonical_to_db_paragon_metrics, db_paragon_metrics_to_canonical

scraper_payload = {
    "mentions": 120,
    "positive_events": 4,
    "negative_events": 1,
    "scandals_flagged": 2,
    "sentiment_score": 0.37,
}

canon = scraper_to_canonical(scraper_payload)
dbrow = canonical_to_db_paragon_metrics(canon)
canon2 = db_paragon_metrics_to_canonical(dbrow)

print("CANON:", canon)
print("DBROW:", dbrow)
print("CANON2:", canon2)
