"""Deterministic money, scoped citations, readiness and report facts. No model arithmetic."""
import csv
import io
import re
from collections import defaultdict
from datetime import date

from .errors import DomainError, require


def minor_units(text):
    require(isinstance(text, str) and bool(re.fullmatch(r"(?:0|[1-9]\d{0,9})(?:\.\d{1,2})?", text.strip())),
            "Amounts must be non-negative decimals with at most two decimal places")
    whole, _, cents = text.strip().partition(".")
    return int(whole) * 100 + int((cents + "00")[:2])


def integer_amount(value):
    require(type(value) is int and 0 <= value <= 999_999_999_999,
            "Allocation must be a non-negative integer in minor units")
    return value


def validate_allocations(data, expense, allocations):
    require(isinstance(allocations, list) and len(allocations) <= 20, "Provide an allocation list")
    seen, total = set(), 0
    for allocation in allocations:
        require(isinstance(allocation, dict), "Invalid allocation")
        grant_id = allocation.get("grantId")
        require(grant_id in data["grants"], "Allocation grant is outside your workspace", "forbidden", 403)
        require(grant_id not in seen, "Each grant may appear only once in an allocation split")
        seen.add(grant_id)
        require(data["grants"][grant_id]["currency"] == expense["currency"],
                "Mixed-currency allocations are not supported", "currency_mismatch")
        total += integer_amount(allocation.get("amountMinor"))
    require(total <= expense["amountMinor"],
            "Allocations exceed the recorded allocatable amount", "over_allocation", 422)
    return total


def calculate(data, grant_id=None):
    currencies = {e["currency"] for e in data["expenses"].values()}
    currencies.update(g["currency"] for g in data["grants"].values())
    require(len(currencies) <= 1, "Mixed-currency aggregation is not supported", "currency_mismatch")
    by_grant = {key: 0 for key in data["grants"]}
    by_expense = {}
    for expense in data["expenses"].values():
        amount = validate_allocations(data, expense, expense["allocations"])
        by_expense[expense["id"]] = {"amountMinor": expense["amountMinor"], "allocatedMinor": amount,
                                    "unallocatedMinor": expense["amountMinor"] - amount}
        for allocation in expense["allocations"]:
            by_grant[allocation["grantId"]] += allocation["amountMinor"]
    if grant_id:
        require(grant_id in data["grants"], "Grant not found", "not_found", 404)
    return {"currency": next(iter(currencies), "EUR"), "byGrant": by_grant, "byExpense": by_expense,
            "expenseMinor": sum(e["amountMinor"] for e in data["expenses"].values()),
            "allocatedMinor": by_grant[grant_id] if grant_id else sum(by_grant.values())}


def readiness(data, grant_id):
    grant = data["grants"][grant_id]
    requirements, missing = [], []
    for requirement in data["requirements"]:
        if requirement["grantId"] != grant_id:
            continue
        evidence_ids = [e["id"] for e in data["evidence"].values()
                        if e.get("status") == "confirmed" and grant_id in e.get("grantIds", [])
                        and e.get("kind") == requirement["kind"]
                        and (not requirement.get("expenseId") or e.get("expenseId") == requirement["expenseId"])]
        row = {**requirement, "evidenceIds": evidence_ids, "status": "evidenced" if evidence_ids else "missing"}
        requirements.append(row)
        if not evidence_ids:
            missing.append(requirement["title"])
    if not grant.get("rulesConfirmed"):
        missing.append("Grant requirements need confirmation")
    for proposal in data["proposals"].values():
        if proposal["status"] == "pending" and proposal["kind"] == "allocation" and any(
                a["grantId"] == grant_id for a in proposal["after"]["allocations"]):
            missing.append("Resolve the proposed allocation split")
    return {"evidenced": sum(r["status"] == "evidenced" for r in requirements),
            "total": len(requirements), "ready": not missing, "missing": missing,
            "requirements": requirements}


def validate_source(data, ref):
    require(isinstance(ref, dict), "A source reference is required")
    evidence = data["evidence"].get(ref.get("evidenceId"))
    require(evidence is not None, "Source is outside your workspace", "invalid_source", 422)
    require(type(ref.get("version")) is int and ref["version"] == evidence["version"],
            "Source version does not exist", "invalid_source", 422)
    require(type(ref.get("page")) is int and 1 <= ref["page"] <= evidence["pageCount"],
            "Source page does not exist", "invalid_source", 422)
    return evidence


def parse_csv(text, data):
    require(isinstance(text, str) and len(text.encode("utf-8")) <= 1_000_000, "CSV exceeds the 1 MB limit")
    columns = {"expense_id", "description", "amount", "currency", "date", "grant_id", "allocation_amount"}
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    require(reader.fieldnames is not None and len(reader.fieldnames) == len(set(reader.fieldnames))
            and columns.issubset(reader.fieldnames), "CSV is missing required columns or has duplicate columns")
    groups, errors, warnings, rows = {}, [], [], []
    for number, row in enumerate(reader, 2):
        require(number <= 501, "CSV exceeds the 500-row limit")
        try:
            require(None not in row and all(row.get(key) is not None for key in columns), "Wrong number of columns")
            row = {key: value.strip() for key, value in row.items()}
            expense_id = row["expense_id"]
            require(bool(re.fullmatch(r"[A-Za-z0-9_-]{1,80}", expense_id)), "Invalid expense ID")
            require(0 < len(row["description"]) <= 180, "Description is required (up to 180 characters)")
            require(row["currency"] == "EUR", "Only EUR imports are supported in this synthetic workspace")
            require(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["date"])), "Date must be YYYY-MM-DD")
            date.fromisoformat(row["date"])
            expense = {"id": expense_id, "description": row["description"], "amountMinor": minor_units(row["amount"]),
                       "currency": row["currency"], "date": row["date"]}
            require(expense["amountMinor"] > 0, "Expense amount must be positive")
            previous = groups.get(expense_id) or data["expenses"].get(expense_id)
            if previous:
                require(all(previous[k] == expense[k] for k in expense),
                        "Expense ID has conflicting original facts; resolve this ambiguous row before import")
            grant_id = row["grant_id"]
            require(grant_id in data["grants"], "Grant is outside your workspace", "forbidden", 403)
            allocation = {"grantId": grant_id, "amountMinor": minor_units(row["allocation_amount"])}
            group = groups.setdefault(expense_id, {**expense, "allocations": [], "version": previous.get("version", 1) if previous else 1})
            require(not any(a["grantId"] == grant_id for a in group["allocations"]), "Duplicate allocation for the same grant")
            group["allocations"].append(allocation)
            rows.append({"row": number, **expense, "grantId": grant_id,
                         "expenseAmountMinor": expense["amountMinor"], "allocationMinor": allocation["amountMinor"]})
        except (DomainError, ValueError) as exc:
            errors.append({"row": number, "message": str(exc)})
    require(rows or errors, "CSV contains no expense rows")
    for expense in groups.values():
        excess = sum(a["amountMinor"] for a in expense["allocations"]) - expense["amountMinor"]
        if excess > 0:
            warnings.append({"expenseId": expense["id"], "excessMinor": excess,
                             "message": "Allocations exceed the recorded amount; this split will remain a proposal"})
    return {"rows": rows, "errors": errors, "warnings": warnings, "groups": groups}
