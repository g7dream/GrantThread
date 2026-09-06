"""Authenticated operator setup. Never called from a browser or application Lambda.

Uses the operator's AWS credential chain; it does not read keys from the repository.
No email is sent and no Cognito account is created by this script.
"""
import argparse
import json
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stack", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--email", help="Existing Cognito account email to bind; resolved to its verified pool subject")
    parser.add_argument("--identity", choices=["brightpath", "harbour", "northstar"])
    parser.add_argument("--seed", action="store_true", help="Add missing synthetic organisation records")
    parser.add_argument("--reset-synthetic", action="store_true", help="Replace synthetic organisation records; source objects remain private")
    parser.add_argument("--confirm-stack", help="Required exact stack name for a reset")
    parser.add_argument("--replace-membership", action="store_true", help="Explicitly allow replacing this subject's membership")
    args = parser.parse_args()
    if bool(args.email) != bool(args.identity):
        parser.error("--email and --identity must be used together")
    if not (args.email or args.seed or args.reset_synthetic):
        parser.error("Choose --seed, --reset-synthetic, or --email with --identity")
    if args.reset_synthetic and args.confirm_stack != args.stack:
        parser.error("A reset requires --confirm-stack with the exact target stack name")

    import boto3
    session = boto3.Session(region_name=args.region)
    caller = session.client("sts").get_caller_identity()
    stack = session.client("cloudformation").describe_stacks(StackName=args.stack)["Stacks"][0]
    outputs = {entry["OutputKey"]: entry["OutputValue"] for entry in stack["Outputs"]}
    print(f"Authenticated operator account {caller['Account']}; target stack {args.stack} in {args.region}.")
    os.environ.update(GRANTTHREAD_MODE="aws", AWS_DEFAULT_REGION=args.region, AWS_REGION=args.region,
                      GRANTTHREAD_TABLE=outputs["TableName"], GRANTTHREAD_BUCKET=outputs["BucketName"])
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

    if args.seed or args.reset_synthetic:
        from grantthread.seed import seed_all
        seed_all(overwrite=args.reset_synthetic)
        print("Synthetic data seeded." if not args.reset_synthetic else "Synthetic data reset; memberships preserved.")

    if args.email:
        user = session.client("cognito-idp").admin_get_user(UserPoolId=outputs["CognitoUserPoolId"], Username=args.email)
        if not user.get("Enabled"):
            parser.error("The Cognito account is disabled")
        attributes = {item["Name"]: item["Value"] for item in user["UserAttributes"]}
        subject = attributes["sub"]
        names = {"brightpath": "Bright Path Lab", "harbour": "Harbour Collective", "northstar": "Northstar Foundation"}
        identity = {"id": subject, "name": attributes.get("name") or names[args.identity] + " demo user",
                    "role": "funder" if args.identity == "northstar" else "grantee",
                    "organisationId": args.identity, "organisationName": names[args.identity]}
        if args.identity == "northstar":
            identity["granteeOrgIds"] = ["brightpath", "harbour"]
        table = session.resource("dynamodb").Table(outputs["TableName"])
        key = "MEMBER#" + subject
        existing = table.get_item(Key={"pk": key}, ConsistentRead=True).get("Item")
        if existing and json.loads(existing["payload"]) == identity:
            print("Membership already matches; no write needed.")
            return
        if existing and not args.replace_membership:
            parser.error("This subject already has a different membership; inspect it before using --replace-membership")
        write = {"Item": {"pk": key, "payload": json.dumps(identity), "version": int(existing["version"]) + 1 if existing else 1}}
        if existing:
            write.update(ConditionExpression="#v = :previous", ExpressionAttributeNames={"#v": "version"},
                         ExpressionAttributeValues={":previous": existing["version"]})
        else:
            write["ConditionExpression"] = "attribute_not_exists(pk)"
        table.put_item(**write)
        print(f"Bound existing authenticated Cognito account to {names[args.identity]} ({identity['role']}).")


if __name__ == "__main__":
    main()
