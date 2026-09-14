"""Private, editable fictional scenarios for authenticated public demo visitors.

Only gateway-validated subjects choose a namespace. No caller chooses an existing
organisation, membership or source object. Starting/restoring never reads the
operator's live demonstration records or copies uploaded private documents.
"""
import copy
import hashlib
import os
from datetime import datetime, timezone

from .errors import DomainError, require
from .seed import make_seed

ROLES = ("grantee", "funder")


def enabled():
    return os.getenv("GRANTTHREAD_PUBLIC_DEMO") == "true"


def identity_for_subject(subject, role="grantee"):
    require(enabled(), "Public demonstrations are unavailable", "membership_required", 403)
    require(isinstance(subject, str) and 0 < len(subject) <= 128,
            "A valid signed-in subject is required", "unauthorised", 401)
    require(role in ROLES, "Choose grantee or funder demo view", "invalid_demo_role", 400)
    namespace = "demo-" + hashlib.sha256(subject.encode("utf-8")).hexdigest()
    grantee = namespace + "-brightpath"
    identity = {"id": subject, "name": "Demo visitor", "role": role,
                "organisationId": grantee if role == "grantee" else namespace + "-northstar",
                "organisationName": "Bright Path Lab" if role == "grantee" else "Northstar Foundation",
                "publicDemo": True, "demoWorkspaceId": grantee}
    if role == "funder":
        identity["granteeOrgIds"] = [grantee]
    return identity


def _scope(identity):
    require(identity.get("publicDemo") is True, "This action is only for your personal demo copy", "forbidden", 403)
    expected = identity_for_subject(identity.get("id"), identity.get("role"))
    require(all(identity.get(key) == value for key, value in expected.items()),
            "Demo workspace scope is invalid", "forbidden", 403)
    return expected["demoWorkspaceId"]


def _existing(repository, org_id):
    try:
        return repository.read(org_id)
    except DomainError as exc:
        if exc.code == "not_found" and exc.status == 404:
            return None
        raise


def session(identity, repository):
    result = {"user": identity, "mode": os.getenv("GRANTTHREAD_MODE", "local")}
    if identity.get("publicDemo") is True:
        data = _existing(repository, _scope(identity))
        result["demo"] = {"available": True, "initialized": data is not None,
                          "version": data["version"] if data else None, "roles": list(ROLES)}
    return result


class _GenerationRepository:
    """Fence an in-flight API request when another tab restores this demo.

The underlying repository still owns atomicity/retries. Its callback checks the
generation before any user operation can modify a newer restored aggregate.
"""
    def __init__(self, repository, org_id, generation):
        self.repository, self.org_id, self.generation = repository, org_id, generation

    def _check(self, org_id, data):
        require(org_id == self.org_id, "Workspace is outside this demo", "forbidden", 403)
        require(data.get("demoGeneration") == self.generation,
                "Your demo was restored in another tab. Refresh before continuing.", "stale", 409)

    def read(self, org_id):
        require(org_id == self.org_id, "Workspace is outside this demo", "forbidden", 403)
        data = self.repository.read(org_id)
        self._check(org_id, data)
        return data

    def mutate(self, org_id, callback):
        require(org_id == self.org_id, "Workspace is outside this demo", "forbidden", 403)
        def guarded(data):
            self._check(org_id, data)
            return callback(data)
        return self.repository.mutate(org_id, guarded)


def request_repository(identity, repository):
    org_id = _scope(identity)
    data = _existing(repository, org_id)
    require(data is not None, "Start your personal demo before continuing", "demo_not_started", 409)
    return _GenerationRepository(repository, org_id, data["demoGeneration"])


def _fixture(org_id, generation):
    sources = {}

    class Capture:
        def put(self, key, raw, content_type):
            sources[key] = (raw, content_type)

    # Generate from checked-in fictional strings, never a deployed organisation.
    data = make_seed(Capture())["brightpath"]
    namespace = org_id.removesuffix("-brightpath")
    data["organisation"].update(id=org_id, publicDemo=True)
    data["factVersion"] = generation
    data["demoGeneration"] = generation
    for grant in data["grants"].values():
        grant["granteeOrgId"] = org_id
        # Explicit fixture metadata retains the labelled simulated history lookup.
        grant["demoResponseHistoryKey"] = grant["funderOrgId"]
        grant["funderOrgId"] = namespace + "-" + grant["funderOrgId"]
    objects = {}
    for evidence in data["evidence"].values():
        for field in ("objectKey", "parsedKey"):
            old_key = evidence[field]
            new_key = f"{org_id}/demo-seed/{generation}/" + old_key.split("/", 2)[2]
            objects[new_key] = sources[old_key]
            evidence[field] = new_key
    # Reused fixture IDs must not make old tabs' confirmations valid after reset.
    for collection in ("grants", "expenses", "evidence", "proposals"):
        for record in data[collection].values():
            record["version"] = generation
    for proposal in data["proposals"].values():
        proposal["inputVersion"] = generation
        for reference in proposal.get("sourceRefs", []):
            reference["version"] = generation
    # In-flight imports also recheck their target grant's existence, not its
    # aggregate revision. New IDs ensure they cannot enter a freshly reset demo.
    record_ids = set()
    for collection in ("grants", "expenses", "evidence", "proposals"):
        record_ids.update(data[collection])
    record_ids.update(record["id"] for collection in ("requirements", "activities") for record in data[collection])
    id_map = {key: f"demo{generation}-{key}" for key in record_ids}

    def remap(value):
        if isinstance(value, dict):
            return {id_map.get(key, key): remap(item) for key, item in value.items()}
        if isinstance(value, list):
            return [remap(item) for item in value]
        return id_map.get(value, value) if isinstance(value, str) else value

    return remap(data), objects


def _write_sources(storage, objects):
    # Publish the aggregate only after all its generated immutable sources exist.
    # Contending starts/reset preparations write identical bytes to generation keys.
    for key, (raw, content_type) in objects.items():
        storage.put(key, raw, content_type)


def start(identity, repository, storage, body):
    require(not body, "Starting your demo does not accept workspace or role fields")
    org_id = _scope(identity)
    if _existing(repository, org_id) is None:
        data, objects = _fixture(org_id, 1)
        _write_sources(storage, objects)
        repository.put_initial(org_id, data)  # Conditional creation never overwrites edits.
    return session(identity, repository)


def _reset_guard(data, expected_version):
    require(data["version"] == expected_version,
            "Your demo changed. Refresh before restoring it.", "stale", 409)
    require(not any(job.get("status") in {"queued", "running"} for job in data.get("jobs", {}).values()),
            "Wait for the current agent run to finish before restoring your demo.", "demo_busy", 409)


def reset(identity, repository, storage, body):
    org_id = _scope(identity)
    require(set(body) == {"version", "confirm"} and body.get("confirm") == "RESTORE DEMO"
            and type(body.get("version")) is int and body["version"] >= 1,
            "Confirm RESTORE DEMO with the current demo version", "demo_confirmation", 422)
    existing = repository.read(org_id)
    _reset_guard(existing, body["version"])
    generation = max(existing["version"], existing.get("factVersion", 1), existing.get("demoGeneration", 1)) + 1
    fresh, objects = _fixture(org_id, generation)
    _write_sources(storage, objects)

    def restore(data):
        _reset_guard(data, body["version"])
        # Preserve run accounting so Restore cannot bypass the daily model budget.
        jobs = copy.deepcopy(data.get("jobs", {}))
        previous_version = data["version"]
        data.clear()
        data.update(copy.deepcopy(fresh))
        data["version"] = previous_version
        data["jobs"] = jobs
        data["audit"] = [{"actorId": identity["id"], "actorName": identity["name"],
                          "action": "personal_demo_restored", "targetId": org_id,
                          "at": datetime.now(timezone.utc).isoformat()}]

    repository.mutate(org_id, restore)
    return session(identity, repository)
