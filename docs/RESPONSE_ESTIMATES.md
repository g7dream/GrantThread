# Funder response estimates

The grantee's **Response estimates** tool answers: if this report was submitted on the chosen date and the funder has not replied, how much longer might the wait be? The date is a scenario input. The tool does not infer a real submission, send a message, submit a report, change readiness or resolve a clarification.

All history is **simulated**, including the names of the funders. Northstar and Riverbend each have 12 fixed fictional completed-review durations in `backend/grantthread/response_estimates.py`. Digital Belonging and Youth Skills share Northstar's history. Unknown funders have no history; the tool does not borrow another funder's samples.

## Calculation

1. Compute elapsed whole calendar days between the submitted date and today's UTC date. Weekends and holidays count. Future dates and malformed dates are rejected.
2. Display the total sample count and the baseline median duration, rounded up to a whole day.
3. For the unanswered scenario, retain only durations strictly greater than the time already waited. Subtract elapsed days from each retained duration.
4. If at least three samples remain, show their median and nearest-rank 25th–75th percentile range. The date window adds these remaining days to today's date. This range describes the middle half of the comparable fictional samples; it is not a confidence interval, guaranteed bound or funder deadline.
5. If only one or two samples remain, show insufficient comparable history. If the wait equals or exceeds every sample, show that the scenario has reached or passed the simulated history. Neither case displays a zero-day promise. No history also produces no estimate.

For example, on 6 September 2026 a Northstar scenario submitted on 30 August has waited seven days. Its 12 fictional durations produce a median remaining wait of 11 days and an illustrative range of 5–15 more days, or 11–21 September. After 25 days, only two comparable samples remain, so the tool withholds a countdown.

## Boundaries and verification

The API enforces the server's grantee identity and organisation's grant scope. It reads existing records, uses no Bedrock calls and makes no database writes. Editing form inputs invalidates the old result and in-flight request, preventing a late reply from displaying an estimate for the wrong scenario.

This completed-review simulation is not a production prediction model. Live forecasting would require permission to use response events, a consistent definition of first reply, relevant cohorts and treatment of still-unanswered reviews. There is no measured accuracy, probability or confidence claim.

`backend/tests/test_response_estimates.py` covers the numerical examples, conditioning after long waits, sparse and missing history, longest-history boundary, strict/future dates, leap-day calendar arithmetic, grant/funder scope and unchanged stored records.
