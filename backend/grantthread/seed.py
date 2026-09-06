"""Entirely fictional demo records, seeded without any claimed model execution."""
import hashlib
import json

from .repository import get_repository
from .storage import get_storage

IDENTITIES = {
    "brightpath": {"id": "demo-brightpath", "name": "Alex Morgan", "role": "grantee", "organisationId": "brightpath", "organisationName": "Bright Path Lab"},
    "harbour": {"id": "demo-harbour", "name": "Sam Rivera", "role": "grantee", "organisationId": "harbour", "organisationName": "Harbour Collective"},
    "northstar": {"id": "demo-northstar", "name": "Jordan Lee", "role": "funder", "organisationId": "northstar", "organisationName": "Northstar Foundation", "granteeOrgIds": ["brightpath", "harbour"]},
}
STAMP = "2026-09-06T09:00:00+00:00"


def empty(org_id, name):
    return {"version": 1, "factVersion": 1, "organisation": {"id": org_id, "name": name, "synthetic": True},
            "grants": {}, "expenses": {}, "evidence": {}, "proposals": {}, "reports": {}, "jobs": {},
            "snapshots": {}, "clarifications": {}, "uploads": {}, "requirements": [], "activities": [], "audit": []}


def make_grant(key, name, org_id, funder, award, template, deadline):
    return {"id": key, "name": name, "granteeOrgId": org_id, "funderOrgId": funder,
            "funderName": "Northstar Foundation" if funder == "northstar" else "Riverbend Trust",
            "currency": "EUR", "awardMinor": award, "fundingMode": "Restricted actual-cost",
            "template": template, "deadline": deadline, "version": 1, "rulesConfirmed": True}


def seed_evidence(data, key, name, kind, grants, text, expense_id=None, storage=None):
    object_key = f"{data['organisation']['id']}/seed/{key}/original.txt"
    parsed_key = f"{data['organisation']['id']}/seed/{key}/parsed.json"
    raw = text.encode("utf-8")
    evidence = {"id": key, "name": name, "kind": kind, "version": 1, "sha256": hashlib.sha256(raw).hexdigest(),
                "pageCount": 1, "grantIds": grants, "expenseId": expense_id, "createdAt": STAMP, "status": "confirmed",
                "excerpt": text[:260], "objectKey": object_key, "parsedKey": parsed_key, "contentType": "text/plain", "size": len(raw)}
    data["evidence"][key] = evidence
    if storage:
        storage.put(object_key, raw, "text/plain")
        storage.put(parsed_key, json.dumps({"pages": [text]}).encode(), "application/json")
    return evidence


def make_seed(storage=None):
    bright = empty("brightpath", "Bright Path Lab")
    specifications = [("digital-belonging", "Digital Belonging", "northstar", 2_000_000, "northstar-outcomes", "2026-09-30"),
                      ("community-makers", "Community Makers", "riverbend", 1_500_000, "riverbend-financial", "2026-10-05"),
                      ("youth-skills", "Youth Skills", "northstar", 1_000_000, "northstar-outcomes", "2026-10-15")]
    for key, name, funder, award, template, deadline in specifications:
        bright["grants"][key] = make_grant(key, name, "brightpath", funder, award, template, deadline)
        seed_evidence(bright, "agreement-" + key, name + " agreement.txt", "agreement", [key],
                      f"SYNTHETIC DEMONSTRATION DATA. Fictional {name} agreement. Award EUR {award // 100}. "
                      f"Restricted actual-cost grant. Report due {deadline} (date only). Invoices and workshop records are required. "
                      + ("Printing must also have payment evidence. " if key == "digital-belonging" else "")
                      + "This fixture is not a real legal agreement.", storage=storage)
        bright["requirements"].append({"id": key + "-agreement", "grantId": key, "title": "Confirmed grant agreement", "kind": "agreement"})
    descriptions = [("venue", "Venue hire", 100000, "2026-08-12", []),
                    ("printing", "Printing", 60000, "2026-08-14", [("digital-belonging", 60000)]),
                    ("facilitator", "Workshop facilitator", 120000, "2026-08-18", [("digital-belonging", 60000), ("community-makers", 60000)]),
                    ("kits", "Maker kits", 200000, "2026-08-20", [("community-makers", 200000)]),
                    ("insurance", "Insurance", 40000, "2026-08-22", [("youth-skills", 40000)])]
    for key, description, amount, day, allocations in descriptions:
        grants = [g for g, _ in allocations] or ["digital-belonging", "community-makers"]
        bright["expenses"][key] = {"id": key, "description": description, "amountMinor": amount, "currency": "EUR", "date": day,
                                    "allocations": [{"grantId": g, "amountMinor": value} for g, value in allocations], "version": 1,
                                    "paidStatus": "not_provided"}
        seed_evidence(bright, "invoice-" + key, description + " invoice.txt", "invoice", grants,
                      f"SYNTHETIC DEMONSTRATION DATA\nInvoice: {key}\nDescription: {description}\n"
                      f"Amount: EUR {amount / 100:.2f}\nInvoice date: {day}\nPayment date: not provided.\n", key, storage)
        for grant_id in grants:
            bright["requirements"].append({"id": f"{grant_id}-{key}-invoice", "grantId": grant_id,
                                          "title": description + " invoice", "kind": "invoice", "expenseId": key})
    bright["requirements"].append({"id": "printing-payment", "grantId": "digital-belonging",
                                  "title": "Printing payment proof", "kind": "payment_proof", "expenseId": "printing"})
    bright["activities"] = [{"id": "workshop-01", "title": "Community digital workshop", "date": "2026-08-18",
                              "participants": 24, "grantIds": ["digital-belonging", "community-makers"], "evidenceId": "workshop-evidence", "confirmed": True}]
    seed_evidence(bright, "workshop-evidence", "Workshop attendance.txt", "activity", ["digital-belonging", "community-makers"],
                  "SYNTHETIC DEMONSTRATION DATA\nCommunity digital workshop, 2026-08-18. 24 participants. "
                  "One unique workshop supports Digital Belonging and Community Makers. No real participant identities.", storage=storage)
    for key in ["digital-belonging", "community-makers"]:
        bright["requirements"].append({"id": key + "-activity", "grantId": key, "title": "Workshop attendance evidence", "kind": "activity"})
    bright["proposals"]["venue-split"] = {
        "id": "venue-split", "kind": "allocation", "title": "Review the venue allocation", "reason": "The proposed EUR 700 + EUR 500 split exceeds the EUR 1,000 invoice by EUR 200. The split has not entered the ledger.",
        "status": "pending", "version": 1, "inputVersion": 1, "expenseId": "venue", "sourceRefs": [{"evidenceId": "invoice-venue", "version": 1, "page": 1, "excerpt": "Venue hire. EUR 1,000.00"}],
        "before": {"allocations": []}, "after": {"allocations": [{"grantId": "digital-belonging", "amountMinor": 70000}, {"grantId": "community-makers", "amountMinor": 50000}]},
        "excessMinor": 20000, "createdAt": STAMP, "origin": "synthetic-import-fixture"}
    harbour = empty("harbour", "Harbour Collective")
    harbour["grants"]["volunteer-support"] = make_grant("volunteer-support", "Volunteer Support", "harbour", "northstar", 1200000, "northstar-outcomes", "2026-10-10")
    seed_evidence(harbour, "harbour-agreement", "Volunteer Support agreement.txt", "agreement", ["volunteer-support"],
                  "SYNTHETIC DEMONSTRATION DATA. Harbour Collective. Volunteer Support award EUR 12,000 from Northstar. "
                  "Restricted actual-cost. Report due 2026-10-10. No expenses or outcomes recorded yet.", storage=storage)
    harbour["requirements"].append({"id": "volunteer-agreement", "grantId": "volunteer-support", "title": "Confirmed grant agreement", "kind": "agreement"})
    return {"brightpath": bright, "harbour": harbour}


def seed_all(repository=None, storage=None, overwrite=False):
    repository, storage = repository or get_repository(), storage or get_storage()
    for org_id, data in make_seed(storage).items():
        repository.put_initial(org_id, data, overwrite=overwrite)


if __name__ == "__main__":
    seed_all()
    print("Synthetic workspaces seeded; existing state preserved.")
