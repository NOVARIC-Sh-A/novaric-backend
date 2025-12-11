from profile_advisor import ProfileAdvisor

# SCENARIO A: The "Lazy" MP (No work done)
lazy_mp = {
    "amendments_count": 0,
    "paragon_scores": {"vendosmeria": 40},
    "documents": [],
    "detailed_bio": "Short bio."
}

# SCENARIO B: The "Star" MP (Hard worker)
star_mp = {
    "amendments_count": 5,
    "paragon_scores": {"vendosmeria": 85},
    "documents": ["doc1", "doc2", "doc3"],
    "detailed_bio": "A very long detailed bio..." * 50
}

print("--- TESTING LAZY MP ---")
advisor_a = ProfileAdvisor(lazy_mp)
results_a = advisor_a.generate_checklist()
for item in results_a:
    status = "✅" if item['is_completed'] else "⚠️ WARNING"
    print(f"{status} [{item['category']}]: {item['academic_ref']}")

print("\n--- TESTING STAR MP ---")
advisor_b = ProfileAdvisor(star_mp)
results_b = advisor_b.generate_checklist()
for item in results_b:
    status = "✅" if item['is_completed'] else "⚠️ WARNING"
    print(f"{status} [{item['category']}")