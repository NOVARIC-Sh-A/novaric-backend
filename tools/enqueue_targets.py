from services.forensic_repo import db, upsert_case

# The 9 target articles you identified
target_articles = [
    {"id": "NOV_PMF_1", "url": "https://pamfleti.net/anti-mafia/ministri-igli-hasani-merr-ne-delegacion-alban-thiken-trafikant-i-afri-i215140"},
    {"id": "NOV_PMF_2", "url": "https://pamfleti.net/anti-mafia/trafikanti-i-afrikaneve-alban-thika-qe-hodhi-ne-gjyq-pamfleti-n-shpal-i180997"},
    {"id": "NOV_PMF_3", "url": "https://pamfleti.net/aktualitet/ku-jane-afrikanet-e-importuar-nga-trafikanti-alban-thika-i-novaric-si-i176519"},
    {"id": "NOV_PMF_4", "url": "https://pamfleti.net/anti-mafia/trafikanti-i-afrikaneve-alban-thika-i-novaric-gjyq-ndaj-pamfleti-t-du-i175572"},
    {"id": "NOV_PMF_5", "url": "https://pamfleti.net/anti-mafia/policia-fsheh-emrin-e-novaric-te-alban-thikes-si-trafikuese-e-klandes-i171132"},
    {"id": "NOV_PMF_6", "url": "https://pamfleti.net/aktualitet/skandal-panair-i-sklleverve-afrikane-ne-shkoder-me-22-26-maj-alban-th-i169974"},
    {"id": "NOV_PMF_7", "url": "https://pamfleti.net/anti-mafia/trafikanti-alban-thika-urithi-i-prodhim-mashtrimit-me-kriptovaluta-ne-i168828"},
    {"id": "NOV_PMF_8", "url": "https://pamfleti.net/anti-mafia/alban-thika-i-novaric-ka-trafikuar-drejt-be-2200-skllever-nga-afrika--i167536"},
    {"id": "NOV_PMF_9", "url": "https://pamfleti.net/anti-mafia/novaric-e-alban-thikes-baza-e-sklleverve-nga-bangladeshi-e-nepali-qe--i166795"}
]

def prepare_queue():
    for art in target_articles:
        print(f"Registering {art['id']}...")
        
        # 1. Create/Update the Case
        case = upsert_case(art['id'], art['url'], publisher="Pamfleti")
        
        # 2. Create the dummy snapshot record if it doesn't exist
        # This points the DB to your manual snap_0001 folder
        snap_res = db().table("forensic_snapshots").upsert({
            "case_id": case["id"],
            "snapshot_seq": 1,
            "html_archive_uri": f"forensic-snapshots/entity_{art['id']}/snap_0001/source.html",
            "is_active": True
        }, on_conflict="case_id, snapshot_seq").execute()
        
        # 3. Insert the Job into the new forensic_jobs table
        db().table("forensic_jobs").insert({
            "case_id": case["id"],
            "snapshot_id": snap_res.data[0]["id"],
            "job_type": "EXTRACT_ANALYZE",
            "status": "QUEUED"
        }).execute()

if __name__ == "__main__":
    prepare_queue()