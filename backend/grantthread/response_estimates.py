"""Illustrative response estimates from fictional completed-review durations.

These samples are not observations of the named demonstration funders. A future
live implementation needs consented, scoped event history including unanswered
reviews; this completed-only simulation is not a calibrated prediction model.
"""
import math
import re
from datetime import date, datetime, timedelta, timezone
from statistics import median

from .errors import require


SIMULATED_HISTORY = {
    "northstar": (8, 10, 12, 14, 15, 17, 18, 20, 22, 25, 28, 35),
    "riverbend": (12, 15, 18, 20, 22, 24, 26, 28, 30, 34, 38, 45),
}
MIN_COMPARABLE_SAMPLES = 3


def quartile_range(days):
    """Nearest-rank quartiles, in whole calendar days, for sorted samples."""
    return {"low": days[math.ceil(len(days) * .25) - 1],
            "high": days[math.ceil(len(days) * .75) - 1]}


def estimate_response_time(history, submitted_date, as_of=None):
    require(isinstance(submitted_date, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", submitted_date),
            "Enter a submission date in YYYY-MM-DD format")
    try:
        submitted = date.fromisoformat(submitted_date)
    except ValueError:
        require(False, "Enter a valid submission date")
    today = as_of if as_of is not None else datetime.now(timezone.utc).date()
    require(submitted <= today, "Submission date cannot be in the future")
    # This internal contract excludes missing, negative and partial-day samples.
    require(all(type(day) is int and day >= 0 for day in history), "Invalid response history")
    samples = sorted(history)
    elapsed = (today - submitted).days
    remaining = [day - elapsed for day in samples if day > elapsed]
    result = {
        "simulated": True, "asOfDate": today.isoformat(), "submittedDate": submitted_date,
        "elapsedDays": elapsed, "sampleCount": len(samples), "comparableSampleCount": len(remaining),
        "typicalTotalDays": math.ceil(median(samples)) if samples else None,
        "historicalRangeDays": quartile_range(samples) if samples else None,
        "historyDays": samples, "remainingDays": None, "expectedDates": None,
        "status": "beyond_history" if samples and not remaining else "insufficient_history",
        "method": "conditional-empirical-quartiles", "unit": "calendar_days",
    }
    if len(remaining) >= MIN_COMPARABLE_SAMPLES:
        window = {**quartile_range(remaining), "typical": math.ceil(median(remaining))}
        result.update(status="estimated", remainingDays=window, expectedDates={
            key: (today + timedelta(days=window[value])).isoformat()
            for key, value in (("earliest", "low"), ("typical", "typical"), ("latest", "high"))
        })
    return result
