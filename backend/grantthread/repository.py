"""Bounded aggregate persistence with atomic conditional mutations.

Callbacks may retry under DynamoDB contention: they must have no external side effects.
The small demo uses an organisation aggregate; the size ceiling prevents DynamoDB's
400 KB item limit from being mistaken for a scalable unbounded ledger.
"""
import copy
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .errors import DomainError, require

MAX_AGGREGATE_BYTES = 340_000


def encode(value):
    result = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    require(len(result.encode("utf-8")) <= MAX_AGGREGATE_BYTES,
            "This synthetic workspace has reached its storage limit. Export your work before an operator reset.",
            "workspace_limit", 409)
    return result


class SQLiteRepository:
    def __init__(self, path=None):
        self.path = Path(path or Path(os.getenv("GRANTTHREAD_DATA_DIR", ".data")) / "grantthread.sqlite3")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS records (pk TEXT PRIMARY KEY, payload TEXT NOT NULL, version INTEGER NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, identity TEXT NOT NULL, expires INTEGER NOT NULL)")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def read_key(self, key):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM records WHERE pk=?", (key,)).fetchone()
        if row is None:
            raise DomainError("Record not found", "not_found", 404)
        return json.loads(row[0])

    def read(self, org_id):
        return self.read_key("ORG#" + org_id)

    def put_initial(self, org_id, data, overwrite=False):
        with self.connect() as db:
            sql = "INSERT OR REPLACE" if overwrite else "INSERT OR IGNORE"
            db.execute(f"{sql} INTO records VALUES (?,?,?)", ("ORG#" + org_id, encode(data), data["version"]))

    def mutate(self, org_id, callback):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload,version FROM records WHERE pk=?", ("ORG#" + org_id,)).fetchone()
            if row is None:
                raise DomainError("Workspace not found", "not_found", 404)
            data = json.loads(row[0])
            result = callback(data)
            data["version"] = row[1] + 1
            db.execute("UPDATE records SET payload=?,version=? WHERE pk=? AND version=?",
                       (encode(data), data["version"], "ORG#" + org_id, row[1]))
        return copy.deepcopy(result)


class DynamoRepository:
    def __init__(self):
        import boto3
        self.table = boto3.resource("dynamodb").Table(os.environ["GRANTTHREAD_TABLE"])

    def read_key(self, key):
        item = self.table.get_item(Key={"pk": key}, ConsistentRead=True).get("Item")
        if not item:
            raise DomainError("Record not found", "not_found", 404)
        payload = item["payload"]
        return json.loads(payload) if isinstance(payload, str) else payload

    def read(self, org_id):
        return self.read_key("ORG#" + org_id)

    def put_initial(self, org_id, data, overwrite=False):
        args = {"Item": {"pk": "ORG#" + org_id, "payload": encode(data), "version": data["version"]}}
        if not overwrite:
            args["ConditionExpression"] = "attribute_not_exists(pk)"
        try:
            self.table.put_item(**args)
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            if overwrite:
                raise

    def mutate(self, org_id, callback):
        for _ in range(4):
            data = self.read(org_id)
            previous = data["version"]
            result = callback(data)
            data["version"] = previous + 1
            try:
                self.table.put_item(Item={"pk": "ORG#" + org_id, "payload": encode(data), "version": data["version"]},
                                    ConditionExpression="#v = :previous", ExpressionAttributeNames={"#v": "version"},
                                    ExpressionAttributeValues={":previous": previous})
                return copy.deepcopy(result)
            except self.table.meta.client.exceptions.ConditionalCheckFailedException:
                continue
        raise DomainError("Workspace changed during this action. Refresh and try again.", "conflict", 409)


def get_repository():
    return DynamoRepository() if os.getenv("GRANTTHREAD_MODE") == "aws" else SQLiteRepository()
