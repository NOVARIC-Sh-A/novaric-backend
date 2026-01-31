import time
import os
from services.forensic_service import run_analysis_for_case
from services.forensic_repo import db, get_case_by_vector

def run_worker():
    print("Forensic Worker Started. Monitoring Queue...")
    
    while True:
        # Atomic lock: Find 1 queued job and mark it as RUNNING
        job_res = db().rpc("claim_forensic_job", {"worker_name": "local_dev_1"}).execute()
        
        if not job_res.data:
            print("Queue empty. Sleeping...")
            time.sleep(10)
            continue
            
        job = job_res.data[0]
        # Get the vector_id for the case
        case_res = db().table("forensic_cases").select("vector_id").eq("id", job["case_id"]).single().execute()
        vector_id = case_res.data["vector_id"]
        
        print(f"[*] Processing Case: {vector_id}")
        
        try:
            # TRIGGER THE FULL CIDA AUDIT
            run_analysis_for_case(vector_id)
            
            # Mark job as completed
            db().table("forensic_jobs").update({"status": "COMPLETED"}).eq("id", job["id"]).execute()
            print(f"[+] Success: {vector_id}")
            
        except Exception as e:
            print(f"[!] Error processing {vector_id}: {str(e)}")
            db().table("forensic_jobs").update({
                "status": "FAILED",
                "error": str(e)
            }).eq("id", job["id"]).execute()

if __name__ == "__main__":
    run_worker()