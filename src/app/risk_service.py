"""
Risk Assessment Service for AutoWAR Platform
Calculates risks based on evaluation results and industry context
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .models import RiskAssessment, IndustryBenchmark, ClientProfile
from .client_service import ClientService


class RiskService:
    """Service for risk assessment and management"""

    def __init__(self, dynamodb_table=None, table_name: str = "autowar-risks"):
        self.dynamodb = dynamodb_table.meta.client if dynamodb_table else None
        self.table_name = table_name
        self.table = dynamodb_table
        self.client_service = ClientService(dynamodb_table)

    def calculate_bp_risk(
        self, bp_id: str, score: float, client_profile: Optional[ClientProfile] = None
    ) -> RiskAssessment:
        """Calculate risk for a specific best practice"""
        # Risk calculation logic based on BP score and client context
        severity = self._calculate_severity(bp_id, score)
        probability = self._calculate_probability(bp_id, score)
        impact_business = self._calculate_business_impact(bp_id, client_profile)
        impact_technical = self._calculate_technical_impact(bp_id)

        # Get affected resources (mock for now)
        affected_resources = self._get_affected_resources(bp_id)

        # Calculate mitigation priority
        mitigation_priority = self._calculate_mitigation_priority(
            severity, probability, impact_business
        )

        return RiskAssessment(
            bp_id=bp_id,
            severity=severity,
            probability=probability,
            impact_business=impact_business,
            impact_technical=impact_technical,
            description=self._get_risk_description(bp_id, severity),
            affected_resources=affected_resources,
            mitigation_priority=mitigation_priority,
            industry_context=client_profile.industry if client_profile else None,
        )

    def calculate_question_risks(
        self,
        question_id: str,
        bp_results: Dict[str, Any],
        client_profile: Optional[ClientProfile] = None,
    ) -> List[RiskAssessment]:
        """Calculate aggregated risks for a question"""
        risks = []
        for bp_id, bp_data in bp_results.items():
            if isinstance(bp_data, dict) and "score" in bp_data:
                risk = self.calculate_bp_risk(bp_id, bp_data["score"], client_profile)
                risks.append(risk)

        return risks

    def get_industry_benchmarks(
        self, industry: str, pillar: str
    ) -> List[IndustryBenchmark]:
        """Get industry-specific benchmarks"""
        # Mock benchmarks for now
        return [
            IndustryBenchmark(
                industry=industry,
                pillar=pillar,
                question_id="SEC01",
                average_score=75.0,
                recommended_threshold=80.0,
                risk_multipliers={
                    "critical": 1.5,
                    "high": 1.2,
                    "medium": 1.0,
                    "low": 0.8,
                },
                last_updated=datetime.utcnow().isoformat(),
            ),
            IndustryBenchmark(
                industry=industry,
                pillar=pillar,
                question_id="SEC02",
                average_score=65.0,
                recommended_threshold=70.0,
                risk_multipliers={
                    "critical": 1.3,
                    "high": 1.1,
                    "medium": 1.0,
                    "low": 0.9,
                },
                last_updated=datetime.utcnow().isoformat(),
            ),
        ]

    def _calculate_severity(self, bp_id: str, score: float) -> str:
        """Calculate risk severity based on BP score"""
        if score < 30:
            return "critical"
        elif score < 50:
            return "high"
        elif score < 70:
            return "medium"
        else:
            return "low"

    def _calculate_probability(self, bp_id: str, score: float) -> str:
        """Calculate risk probability"""
        if score < 40:
            return "high"
        elif score < 60:
            return "medium"
        else:
            return "low"

    def _calculate_business_impact(
        self, bp_id: str, client_profile: Optional[ClientProfile]
    ) -> str:
        """Calculate business impact considering client context"""
        base_impact = "medium"

        if client_profile:
            # Get industry risk multipliers
            multipliers = self.client_service.get_industry_risk_multipliers(
                client_profile.industry
            )

            # Adjust impact based on BP type and industry
            if bp_id.startswith("SEC01"):  # Identity and access
                base_impact = (
                    "high" if multipliers["security_multiplier"] > 1.3 else "medium"
                )
            elif bp_id.startswith("SEC02"):  # Monitoring
                base_impact = (
                    "high" if multipliers["compliance_multiplier"] > 1.5 else "medium"
                )
            elif bp_id.startswith("SEC03"):  # Data protection
                base_impact = (
                    "high"
                    if multipliers["data_protection_multiplier"] > 1.5
                    else "medium"
                )

            # Consider risk tolerance
            if client_profile.risk_tolerance == "low":
                base_impact = "high"

        return base_impact

    def _calculate_technical_impact(self, bp_id: str) -> str:
        """Calculate technical impact"""
        # Technical impact based on BP category
        if bp_id.startswith("SEC01"):  # Identity and access
            return "high"
        elif bp_id.startswith("SEC02"):  # Monitoring
            return "medium"
        else:
            return "medium"

    def _calculate_mitigation_priority(
        self, severity: str, probability: str, impact: str
    ) -> int:
        """Calculate mitigation priority (1-10)"""
        severity_score = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        probability_score = {"high": 3, "medium": 2, "low": 1}
        impact_score = {"high": 3, "medium": 2, "low": 1}

        total = (
            severity_score.get(severity, 2)
            + probability_score.get(probability, 2)
            + impact_score.get(impact, 2)
        )

        return min(total, 10)  # Cap at 10

    def _get_affected_resources(self, bp_id: str) -> List[str]:
        """Get list of affected resources for a BP"""
        # Mock affected resources
        resource_map = {
            "SEC01-BP01": ["IAM Users", "Root Account"],
            "SEC01-BP02": ["IAM Roles", "EC2 Instances"],
            "SEC02-BP01": ["CloudTrail", "CloudWatch Logs"],
            "SEC02-BP02": ["IAM Users", "Access Keys"],
        }
        return resource_map.get(bp_id, ["Various AWS Resources"])

    def _get_risk_description(self, bp_id: str, severity: str) -> str:
        """Get detailed risk description"""
        descriptions = {
            "SEC01-BP01": {
                "critical": "Root account exposed without MFA - immediate security breach risk",
                "high": "Weak root account protection - potential unauthorized access",
                "medium": "Inadequate root account security - monitoring required",
                "low": "Root account adequately protected",
            },
            "SEC01-BP02": {
                "critical": "Using long-term credentials everywhere - major security vulnerability",
                "high": "Excessive use of long-term credentials - increased attack surface",
                "medium": "Some long-term credentials still in use - gradual migration needed",
                "low": "Primarily using temporary credentials",
            },
        }

        bp_descriptions = descriptions.get(bp_id, {})
        return bp_descriptions.get(severity, f"Risk level: {severity} for {bp_id}")
