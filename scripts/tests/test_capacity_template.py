"""Offline capacity-mode checks using the installed cfn-lint development tooling."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from cfnlint.api import lint
from cfnlint.decode import decode_str
from cfnlint.template import Template


SOURCE = Path(__file__).resolve().parents[2] / "infra" / "template.yaml"
BUDGET_SOURCE = SOURCE.with_name("budget.yaml")


class CapacityTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.data, errors = decode_str(cls.source)
        if errors:
            raise AssertionError(errors)
        cls.template = Template(str(SOURCE), deepcopy(cls.data), regions=["eu-north-1"])

    def resolved(self, mode):
        """Resolve the actual capacity property expressions with cfn-lint's evaluator."""
        result = deepcopy(self.data)
        scenario = {"UseReservedCapacity": mode == "reserved"}
        for name in ("ApiFunction", "WorkerFunction"):
            properties = result["Resources"][name]["Properties"]
            result["Resources"][name]["Properties"] = self.template.get_value_from_scenario(properties, scenario)
        properties = result["Resources"]["HttpApi"]["Properties"]
        properties["DefaultRouteSettings"] = self.template.get_value_from_scenario(
            properties["DefaultRouteSettings"], scenario)
        result["Parameters"]["CapacityMode"]["Default"] = mode
        del result["Conditions"]
        return result

    def test_mode_contract_is_explicit_and_reserved_stays_default(self):
        parameter = self.data["Parameters"]["CapacityMode"]
        self.assertEqual(parameter["Default"], "reserved")
        self.assertEqual(set(parameter["AllowedValues"]), {"reserved", "shared-demo"})
        self.assertEqual(self.data["Conditions"]["UseReservedCapacity"],
                         {"Fn::Equals": [{"Ref": "CapacityMode"}, "reserved"]})
        self.assertEqual(self.data["Outputs"]["CapacityMode"]["Value"], {"Ref": "CapacityMode"})

    def test_shared_demo_omits_both_reservations_instead_of_disabling_functions(self):
        resources = self.resolved("shared-demo")["Resources"]
        for name in ("ApiFunction", "WorkerFunction"):
            with self.subTest(function=name):
                self.assertNotIn("ReservedConcurrentExecutions", resources[name]["Properties"])
                self.assertEqual(self.data["Resources"][name]["Properties"]["ReservedConcurrentExecutions"]["Fn::If"][2],
                                 {"Ref": "AWS::NoValue"})

    def test_reserved_mode_keeps_function_isolation_and_original_throttles(self):
        resources = self.resolved("reserved")["Resources"]
        self.assertEqual(resources["ApiFunction"]["Properties"]["ReservedConcurrentExecutions"], 5)
        self.assertEqual(resources["WorkerFunction"]["Properties"]["ReservedConcurrentExecutions"], 2)
        self.assertEqual(resources["HttpApi"]["Properties"]["DefaultRouteSettings"],
                         {"ThrottlingBurstLimit": 20, "ThrottlingRateLimit": 10})

    def test_shared_mode_only_changes_reservations_and_api_throttle(self):
        shared = self.resolved("shared-demo")
        reserved = self.resolved("reserved")
        self.assertEqual(shared["Resources"]["HttpApi"]["Properties"]["DefaultRouteSettings"],
                         {"ThrottlingBurstLimit": 5, "ThrottlingRateLimit": 5})
        queue = shared["Resources"]["WorkerFunction"]["Properties"]["Events"]["Queue"]["Properties"]
        self.assertEqual(queue["ScalingConfig"]["MaximumConcurrency"], 2)
        self.assertEqual(queue["BatchSize"], 1)
        for name in ("ApiFunction", "WorkerFunction"):
            del reserved["Resources"][name]["Properties"]["ReservedConcurrentExecutions"]
        reserved["Resources"]["HttpApi"]["Properties"]["DefaultRouteSettings"] = deepcopy(
            shared["Resources"]["HttpApi"]["Properties"]["DefaultRouteSettings"])
        reserved["Parameters"]["CapacityMode"]["Default"] = "shared-demo"
        # IAM, authorizer, job limits, storage and timeouts must not vary by mode.
        self.assertEqual(shared, reserved)

    def test_conditional_and_both_resolved_templates_pass_sam_schema_lint(self):
        for mode, source in [("conditional", self.source)] + [
            (mode, json.dumps(self.resolved(mode))) for mode in ("reserved", "shared-demo")
        ]:
            with self.subTest(mode=mode):
                self.assertEqual(lint(source, regions=["eu-north-1"]), [])

    def test_preflight_is_public_without_relaxing_application_authorization(self):
        for mode in ("reserved", "shared-demo"):
            with self.subTest(mode=mode):
                resources = self.resolved(mode)["Resources"]
                events = resources["ApiFunction"]["Properties"]["Events"]
                self.assertEqual(events["Preflight"], {"Type": "HttpApi", "Properties": {
                    "ApiId": {"Ref": "HttpApi"}, "Path": "/api/{proxy+}", "Method": "OPTIONS",
                    "Auth": {"Authorizer": "NONE"}}})
                self.assertEqual(events["ApiRoutes"], {"Type": "HttpApi", "Properties": {
                    "ApiId": {"Ref": "HttpApi"}, "Path": "/api/{proxy+}", "Method": "ANY"}})
                self.assertEqual({name for name, event in events.items()
                                  if event["Properties"].get("Auth", {}).get("Authorizer") == "NONE"},
                                 {"Health", "Preflight"})
                auth = resources["HttpApi"]["Properties"]["Auth"]
                self.assertEqual(auth["DefaultAuthorizer"], "CognitoAccess")
                self.assertEqual(auth["Authorizers"]["CognitoAccess"]["AuthorizationScopes"],
                                 ["grantthread/access"])

    def test_budget_is_separate_from_regional_application_in_both_modes(self):
        for mode in ("reserved", "shared-demo"):
            with self.subTest(mode=mode):
                data = self.resolved(mode)
                self.assertEqual(set(data["Parameters"]), {
                    "FrontendOrigin", "CallbackUrl", "CognitoDomainPrefix", "BedrockModelId", "CapacityMode"})
                self.assertFalse(any(resource["Type"] == "AWS::Budgets::Budget"
                                     for resource in data["Resources"].values()))

    def test_private_source_cors_allows_get_only_from_the_configured_frontend(self):
        for mode in ("reserved", "shared-demo"):
            with self.subTest(mode=mode):
                bucket = self.resolved(mode)["Resources"]["EvidenceBucket"]["Properties"]
                self.assertEqual(bucket["CorsConfiguration"]["CorsRules"], [{
                    "AllowedOrigins": [{"Ref": "FrontendOrigin"}], "AllowedMethods": ["PUT", "GET"],
                    "AllowedHeaders": ["content-type"], "MaxAge": 600}])
                self.assertTrue(all(bucket["PublicAccessBlockConfiguration"].values()))

    def test_budget_preserves_alerts_and_excludes_credits_and_refunds(self):
        source = BUDGET_SOURCE.read_text(encoding="utf-8")
        data, errors = decode_str(source)
        self.assertEqual(errors, [])
        self.assertNotIn("Transform", data)
        self.assertNotIn("Conditions", data)
        self.assertEqual(data["Parameters"]["BudgetName"]["Default"], "grantthread-demo-monthly")
        self.assertEqual(data["Parameters"]["MonthlyBudgetUsd"]["Default"], 25)
        self.assertNotIn("Default", data["Parameters"]["BudgetEmail"])
        properties = data["Resources"]["CostBudget"]["Properties"]
        self.assertEqual(properties["Budget"]["CostTypes"], {"IncludeCredit": False, "IncludeRefund": False})
        self.assertNotIn("CostFilters", properties["Budget"])
        alerts = properties["NotificationsWithSubscribers"]
        self.assertEqual([(item["Notification"]["NotificationType"], item["Notification"]["Threshold"])
                          for item in alerts], [("ACTUAL", 80), ("FORECASTED", 100)])
        for alert in alerts:
            self.assertEqual(alert["Notification"]["ComparisonOperator"], "GREATER_THAN")
            self.assertEqual(alert["Subscribers"], [{"SubscriptionType": "EMAIL", "Address": {"Ref": "BudgetEmail"}}])
        self.assertNotIn("BudgetEmail", data["Outputs"])
        self.assertEqual(lint(source, regions=["us-east-1"]), [])


if __name__ == "__main__":
    unittest.main()
