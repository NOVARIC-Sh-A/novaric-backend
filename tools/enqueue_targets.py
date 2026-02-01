from __future__ import annotations

from typing import Any, Dict, List

from services.forensic_repo import db, upsert_case


# The 9 target URLs (canonical)
target_articles: List[Dict[str, str]] = [
    {"id": "NOV_PMF_1", "url": "https://pamfleti.net/anti-mafia/ministri-igli-hasani-merr-ne-delegacion-alban-thiken-trafikant-i-afri-i215140"},
    {"id": "NOV_PMF_2", "url": "https://pamfleti.net/anti-mafia/trafikanti-i-afrikaneve-alban-thika-qe-hodhi-ne-gjyq-pamfleti-n-shpal-i180997"},
    {"id": "NOV_PMF_3", "url": "https://pamfleti.net/aktualitet/ku-jane-afrikanet-e-importuar-nga-trafikanti-alban-thika-i-novaric-si-i176519"},
    {"id": "NOV_PMF_4", "url": "https://pamfleti.net/anti-mafia/trafikanti-i-afrikaneve-alban-thika-i-novaric-gjyq-ndaj-pamfleti-t-du-i175572"},
    {"id": "NOV_PMF_5", "url": "https://pamfleti.net/anti-mafia/policia-fsheh-emrin-e-novaric-te-alban-thikes-si-trafikuese-e-klandes-i171132"},
    {"id": "NOV_PMF_6", "url": "https://pamfleti.net/aktualitet/skandal-panair-i-sklleverve-afrikane-ne-shkoder-me-22-26-maj-alban-th-i169974"},
    {"id": "NOV_PMF_7", "url": "https://pamfleti.net/anti-mafia/trafikanti-alban-thika-urithi-i-prodhim-mashtrimit-me-kriptovaluta-ne-i168828"},
    {"id": "NOV_PMF_8", "url": "https://pamfleti.net/anti-mafia/alban-thika-i-novaric-ka-trafikuar-drejt-be-2200-skllever-nga-afrika--i167536"},
    {"id": "NOV_PMF_9", "url": "https://pamfleti.net/anti-mafia/novaric-e-alban-thikes-baza-e-sklleverve-nga-bangladeshi-e-nepali-qe--i166795"},
]


PUBLISHER = "Pamfleti"

# IMPORTANT:
# If case_modules has FK -> case_studies.id, you want this True so the parent row always exists.
ENSURE_CASE_STUDIES_PARENT = True


def _ensure_case_studies_parent(vector_id: str, url: str) -> None:
    """
    Creates a minimal placeholder row in case_studies so FK-dependent tables (case_modules)
    can reference it even before analysis completes.

    This respects:
    - NOT NULL integrity_score (set to 0)
    - NOT NULL blackmail_probability (set to 0)
    - UNIQUE slug (set to vector_id.lower())
    """
    sb = db()
    sb.table("case_studies").upsert(
        {
            "id": vector_id,
            "source": PUBLISHER,
            "headline": "Pending Forensic Analysis",
            "article_url": url,
            "verdict": "PENDING",
            "verdict_summary": "",
            "key_tactics": [],
            "integrity_score": 0,
            "blackmail_probability": 0,
            "weaponization_index": 0,
            "truth_to_slant_ratio": 0,
            "forensic_findings": [],
            "strategic_rebuttals": [],
            "conclusion": "",
            "is_published": True,
            "slug": vector_id.lower(),
            "audited_at": "now()",
        },
        on_conflict="id",
    ).execute()


def _job_exists(case_id: Any, snapshot_id: Any) -> bool:
    """
    Avoid duplicate jobs if you re-run this script.
    Treat QUEUED or RUNNING as existing.
    """
    sb = db()
    res = (
        sb.table("forensic_jobs")
        .select("id,status")
        .eq("case_id", case_id)
        .eq("snapshot_id", snapshot_id)
        .in_("status", ["QUEUED", "RUNNING"])
        .limit(1)
        .execute()
    )
    return bool(res.data)


def prepare_queue() -> None:
    sb = db()

    for art in target_articles:
        vector_id = art["id"]
        url = art["url"]

        print(f"Registering {vector_id}...")

        # 1) Create/Update the Case
        case = upsert_case(vector_id, url, publisher=PUBLISHER)

        # 2) Create the dummy snapshot record if it doesn't exist
        # Points DB to your manual snap_0001 folder
        snap_res = (
            sb.table("forensic_snapshots")
            .upsert(
                {
                    "case_id": case["id"],
                    "snapshot_seq": 1,
                    "canonical_url": url,
                    "html_archive_uri": f"forensic-snapshots/entity_{vector_id}/snap_0001/source.html",
                    "is_active": True,
                },
                on_conflict="case_id, snapshot_seq",
            )
            .execute()
        )

        if not snap_res.data:
            raise RuntimeError(f"Snapshot upsert failed for {vector_id}")

        snapshot_id = snap_res.data[0]["id"]

        # 3) Ensure parent dashboard row exists (optional but recommended)
        if ENSURE_CASE_STUDIES_PARENT:
            _ensure_case_studies_parent(vector_id, url)

        # 4) Insert a job only if not already queued/running
        if _job_exists(case["id"], snapshot_id):
            print(f" - Job already exists for {vector_id} (QUEUED/RUNNING). Skipping.")
            continue

        sb.table("forensic_jobs").insert(
            {
                "case_id": case["id"],
                "snapshot_id": snapshot_id,
                "job_type": "EXTRACT_ANALYZE",
                "status": "QUEUED",
            }
        ).execute()

        print(f" - QUEUED job for {vector_id}")

    print("DONE: All targets registered.")


if __name__ == "__main__":
    prepare_queue()
