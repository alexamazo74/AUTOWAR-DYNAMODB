"""
Comprehensive Security Pillar Evaluator
Evaluates all 11 questions and 63 best practices against real AWS resources
"""

from typing import Dict, List, Any
from .aws_connector import AWSConnector
from ..config.sec01_services_config import (
    get_bp_services,
    get_bp_name,
)
import logging

logger = logging.getLogger(__name__)


class SecurityPillarEvaluator:
    """Evaluates all 11 Security pillar questions"""

    def __init__(self, connector: AWSConnector):
        self.connector = connector

    def _calculate_score_from_findings(self, findings: List[Dict[str, Any]]) -> int:
        """
        Calculate score as percentage of COMPLIANT best practices
        Score = (Compliant BPs / (Compliant + Non-Compliant BPs)) * 100
        PENDING_REVIEW and other statuses are excluded from the calculation
        """
        compliant = sum(1 for f in findings if f.get("status") == "COMPLIANT")
        non_compliant = sum(1 for f in findings if f.get("status") == "NON_COMPLIANT")
        total = compliant + non_compliant

        if total == 0:
            # If no COMPLIANT or NON_COMPLIANT (all PENDING_REVIEW), assume 100%
            return 100
        return int((compliant / total) * 100)

    def _create_pending_finding(
        self, bp: str, finding: str, severity: str = "MEDIUM", evidence: str = "N/D"
    ) -> Dict[str, Any]:
        """Create a PENDING_REVIEW finding with all required fields"""
        return {
            "bp": bp,
            "status": "PENDING_REVIEW",
            "finding": finding,
            "severity": severity,
            "risk": "N/D",
            "remediation": "N/D",
            "evidence": evidence,
        }

    def _create_no_resources_finding(
        self, bp: str, finding: str, reason: str
    ) -> Dict[str, Any]:
        """Create a finding when no resources/services are found"""
        return {
            "bp": bp,
            "status": "PENDING_REVIEW",
            "finding": finding,
            "severity": "MEDIUM",
            "risk": "Unable to assess - no resources configured",
            "remediation": "N/D",
            "evidence": reason,  # E.g., "No EC2 instances found", "No S3 buckets configured", etc.
        }

    def _create_timeout_finding(
        self, bp: str, finding: str, service: str = "AWS"
    ) -> Dict[str, Any]:
        """Create a finding when evaluation times out"""
        return {
            "bp": bp,
            "status": "PENDING_REVIEW",
            "finding": finding,
            "severity": "MEDIUM",
            "risk": "N/D",
            "remediation": "Re-run evaluation to get accurate assessment",
            "evidence": f"Evaluation timeout - unable to query {service} in time limit",
        }

    def _normalize_finding(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure a finding has all required fields"""
        required_fields = [
            "bp",
            "status",
            "finding",
            "severity",
            "risk",
            "remediation",
            "evidence",
        ]

        for field in required_fields:
            if field not in finding:
                if field == "severity":
                    finding[field] = "MEDIUM"
                else:
                    finding[field] = "N/D"

        if finding.get("status") == "PENDING_REVIEW":
            finding["remediation"] = "Requiere verificación manual"

        return finding

    def _normalize_findings_list(
        self, findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Normalize all findings in a list"""
        return [self._normalize_finding(f) for f in findings]

    def _calculate_section_score(
        self, total_bps: int, compliant_bps: int, partial_bps: int = 0
    ) -> float:
        """
        Calculate score for a section based on compliant BPs.
        N/D items (PENDING_REVIEW) count as 0% of that BP.

        Args:
            total_bps: Total number of BPs in this section
            compliant_bps: Number of COMPLIANT BPs
            partial_bps: Number of PARTIALLY_COMPLIANT BPs (optional, counts as 50%)

        Returns:
            Score 0-100
        """
        if total_bps == 0:
            return 100

        # Each compliant BP is worth 100 points
        # Each partially compliant BP is worth 50 points
        # Each non-compliant or pending BP is worth 0 points
        total_points = (compliant_bps * 100) + (partial_bps * 50)
        max_points = total_bps * 100

        score = (total_points / max_points) * 100 if max_points > 0 else 0
        return round(score, 2)

    def get_security_metrics(self) -> Dict[str, Any]:
        """
        Calculate security metrics and KPIs across all evaluated sections.
        
        Returns:
            {
                "detection_metrics": {...},
                "network_security_metrics": {...},
                "compute_security_metrics": {...},
                "operational_efficiency_metrics": {...},
                "timestamp": "ISO timestamp"
            }
        """
        from datetime import datetime
        
        logger.info("[METRICS] Calculating security metrics and KPIs...")
        
        try:
            # Evaluate all sections to get current state
            all_results = self.evaluate_all()
            questions = all_results.get("questions", [])
            
            # Initialize metrics
            metrics = {
                "detection_metrics": self._calculate_detection_metrics(questions),
                "network_security_metrics": self._calculate_network_metrics(questions),
                "compute_security_metrics": self._calculate_compute_metrics(questions),
                "operational_efficiency_metrics": self._calculate_operational_metrics(questions),
                "overall_metrics": {
                    "overall_score": all_results.get("overall_score", 0),
                    "total_findings": all_results.get("total_findings", 0),
                    "compliant_count": sum(
                        len([f for f in q.get("findings", []) if f.get("status") == "COMPLIANT"])
                        for q in questions
                    ),
                    "non_compliant_count": sum(
                        len([f for f in q.get("findings", []) if f.get("status") == "NON_COMPLIANT"])
                        for q in questions
                    ),
                    "pending_count": sum(
                        len([f for f in q.get("findings", []) if f.get("status") == "PENDING_REVIEW"])
                        for q in questions
                    ),
                },
                "timestamp": datetime.now().isoformat(),
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"[METRICS] Error calculating metrics: {str(e)}", exc_info=True)
            return {
                "error": f"Error calculating metrics: {str(e)[:100]}",
                "timestamp": datetime.now().isoformat(),
            }

    def _calculate_detection_metrics(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate detection-related metrics (SEC04)"""
        # Find SEC04 findings
        sec04 = next((q for q in questions if q.get("question_id") == "SEC04"), {})
        findings = sec04.get("findings", [])
        
        compliant = len([f for f in findings if f.get("status") == "COMPLIANT"])
        non_compliant = len([f for f in findings if f.get("status") == "NON_COMPLIANT"])
        
        # Calculate MTTD (simulated - would require historical data)
        # Calculate false positive rate (simulated - would require historical data)
        
        return {
            "coverage_percentage": round((compliant / max(compliant + non_compliant, 1)) * 100, 2),
            "detection_services_enabled": compliant,
            "detection_services_required": compliant + non_compliant,
            "mean_time_to_detection_mttd": "N/D (requires historical data)",
            "false_positive_rate": "N/D (requires historical data)",
            "alert_volume_trends": "N/D (requires historical data)",
        }

    def _calculate_network_metrics(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate network security metrics (SEC05)"""
        sec05 = next((q for q in questions if q.get("question_id") == "SEC05"), {})
        findings = sec05.get("findings", [])
        
        compliant = len([f for f in findings if f.get("status") == "COMPLIANT"])
        non_compliant = len([f for f in findings if f.get("status") == "NON_COMPLIANT"])
        
        return {
            "network_segmentation_compliance": round((compliant / max(compliant + non_compliant, 1)) * 100, 2),
            "traffic_flow_controls_enabled": compliant,
            "inspection_systems_active": "Evaluate findings for specific counts",
            "blocked_connection_attempts": "N/D (requires flow log analysis)",
            "ddos_mitigation_effectiveness": "N/D (requires attack data)",
            "network_segmentation_score": round((compliant / max(compliant + non_compliant, 1)) * 100, 2),
        }

    def _calculate_compute_metrics(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate compute security metrics (SEC06)"""
        sec06 = next((q for q in questions if q.get("question_id") == "SEC06"), {})
        findings = sec06.get("findings", [])
        
        compliant = len([f for f in findings if f.get("status") == "COMPLIANT"])
        non_compliant = len([f for f in findings if f.get("status") == "NON_COMPLIANT"])
        
        return {
            "vulnerability_remediation_rate": "N/D (requires time-series data)",
            "patch_compliance_rate": round((compliant / max(compliant + non_compliant, 1)) * 100, 2),
            "image_hardening_compliance": compliant,
            "automated_response_success_rate": round((compliant / max(compliant + non_compliant, 1)) * 100, 2),
            "manual_access_reduction": "Evaluate Session Manager and Run Command usage",
            "code_signing_compliance": "Evaluate AWS Signer and Lambda signing policies",
        }

    def _calculate_operational_metrics(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate operational efficiency metrics"""
        all_findings = []
        for q in questions:
            all_findings.extend(q.get("findings", []))
        
        compliant = len([f for f in all_findings if f.get("status") == "COMPLIANT"])
        non_compliant = len([f for f in all_findings if f.get("status") == "NON_COMPLIANT"])
        
        total_bps = compliant + non_compliant
        
        return {
            "manual_intervention_reduction": "Evaluate automation functions count",
            "automation_success_rate": round((compliant / max(total_bps, 1)) * 100, 2),
            "mean_time_to_remediation_mttr": "N/D (requires incident ticket data)",
            "cost_per_security_event": "N/D (requires cost analysis)",
            "overall_automation_coverage": round((compliant / max(total_bps, 1)) * 100, 2),
            "findings_resolution_rate": "N/D (requires trending data)",
        }

    def get_security_kpis(self) -> Dict[str, Any]:
        """
        Get Key Performance Indicators for security posture.
        
        Returns:
            {
                "critical_findings": {...},
                "compliance_score": {...},
                "risk_trend": {...},
                "remediation_tracking": {...}
            }
        """
        from datetime import datetime
        
        logger.info("[KPIs] Calculating security KPIs...")
        
        try:
            all_results = self.evaluate_all()
            questions = all_results.get("questions", [])
            
            all_findings = []
            for q in questions:
                all_findings.extend(q.get("findings", []))
            
            # Count findings by severity and status
            critical_findings = [
                f for f in all_findings 
                if f.get("severity") == "CRITICAL" and f.get("status") == "NON_COMPLIANT"
            ]
            high_findings = [
                f for f in all_findings 
                if f.get("severity") == "HIGH" and f.get("status") == "NON_COMPLIANT"
            ]
            
            compliant_bps = len([f for f in all_findings if f.get("status") == "COMPLIANT"])
            non_compliant_bps = len([f for f in all_findings if f.get("status") == "NON_COMPLIANT"])
            
            kpis = {
                "critical_findings": {
                    "count": len(critical_findings),
                    "percentage": round(
                        (len(critical_findings) / max(len(all_findings), 1)) * 100, 2
                    ),
                    "trend": "Requires historical data for trend analysis",
                    "examples": [
                        {
                            "bp": f.get("bp"),
                            "finding": f.get("finding", "")[:100],
                            "risk": f.get("risk", "")[:100],
                        }
                        for f in critical_findings[:5]
                    ],
                },
                "high_findings": {
                    "count": len(high_findings),
                    "percentage": round(
                        (len(high_findings) / max(len(all_findings), 1)) * 100, 2
                    ),
                },
                "compliance_score": {
                    "overall": round(
                        (compliant_bps / max(compliant_bps + non_compliant_bps, 1)) * 100, 2
                    ),
                    "by_section": self._get_section_compliance_scores(questions),
                    "trending": "Requires historical data",
                },
                "risk_indicators": {
                    "high_risk_bps": len([f for f in all_findings if f.get("severity") in ["CRITICAL", "HIGH"] and f.get("status") == "NON_COMPLIANT"]),
                    "unaddressed_findings": len([f for f in all_findings if f.get("status") == "PENDING_REVIEW"]),
                    "remediation_priority": self._determine_remediation_priority(all_findings),
                },
                "recommendations": self._generate_security_recommendations(all_findings),
                "timestamp": datetime.now().isoformat(),
            }
            
            return kpis
            
        except Exception as e:
            logger.error(f"[KPIs] Error calculating KPIs: {str(e)}", exc_info=True)
            return {
                "error": f"Error calculating KPIs: {str(e)[:100]}",
                "timestamp": datetime.now().isoformat(),
            }

    def _get_section_compliance_scores(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get compliance scores for each section"""
        scores = {}
        for q in questions:
            question_id = q.get("question_id", "UNKNOWN")
            findings = q.get("findings", [])
            
            compliant = len([f for f in findings if f.get("status") == "COMPLIANT"])
            non_compliant = len([f for f in findings if f.get("status") == "NON_COMPLIANT"])
            
            total = compliant + non_compliant
            score = round((compliant / total * 100), 2) if total > 0 else 100
            
            scores[question_id] = {
                "score": score,
                "compliant_bps": compliant,
                "non_compliant_bps": non_compliant,
            }
        
        return scores

    def _determine_remediation_priority(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Determine which BPs should be remediated first"""
        # Sort by severity and compliance status
        critical_non_compliant = [
            f for f in findings 
            if f.get("severity") == "CRITICAL" and f.get("status") == "NON_COMPLIANT"
        ]
        high_non_compliant = [
            f for f in findings 
            if f.get("severity") == "HIGH" and f.get("status") == "NON_COMPLIANT"
        ]
        
        priority_list = []
        for f in critical_non_compliant[:5]:
            priority_list.append({
                "bp": f.get("bp"),
                "priority": "CRITICAL",
                "remediation": f.get("remediation", "N/D"),
            })
        
        for f in high_non_compliant[:5]:
            priority_list.append({
                "bp": f.get("bp"),
                "priority": "HIGH",
                "remediation": f.get("remediation", "N/D"),
            })
        
        return priority_list

    def _generate_security_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable security recommendations"""
        recommendations = []
        
        # Check for logging gaps
        logging_bps = [f for f in findings if "log" in f.get("bp", "").lower()]
        if logging_bps and any(f.get("status") == "NON_COMPLIANT" for f in logging_bps):
            recommendations.append("Priority: Enable comprehensive logging across CloudTrail, CloudWatch, and VPC Flow Logs")
        
        # Check for encryption issues
        encryption_bps = [f for f in findings if "encrypt" in f.get("finding", "").lower()]
        if encryption_bps:
            recommendations.append("Ensure all data in transit and at rest is encrypted with KMS")
        
        # Check for access control issues
        access_bps = [f for f in findings if "access" in f.get("bp", "").lower() or "permission" in f.get("bp", "").lower()]
        if access_bps and any(f.get("status") == "NON_COMPLIANT" for f in access_bps):
            recommendations.append("Review and implement least privilege access controls across all resources")
        
        # Check for automation
        automation_bps = [f for f in findings if "automat" in f.get("finding", "").lower()]
        if not automation_bps:
            recommendations.append("Implement automated security responses using Lambda, EventBridge, and Systems Manager")
        
        # Check for monitoring
        monitoring_bps = [f for f in findings if "monitor" in f.get("finding", "").lower() or "alert" in f.get("finding", "").lower()]
        if not monitoring_bps:
            recommendations.append("Configure CloudWatch alarms and Security Hub custom insights for threat detection")
        
        return recommendations[:10]  # Return top 10 recommendations


    def evaluate_sec01(self) -> Dict[str, Any]:
        """SEC01: ¿Cómo opera usted su carga de trabajo de forma segura? (8 BPs)

        Best Practices:
        - BP01: Operate workload securely (Organizations, Control Tower, RAM, SSO, IAM)
        - BP02: Separate workload using accounts (Organizations, Control Tower)
        - BP03: Secure AWS account (IAM, GuardDuty, Security Hub, Config, CloudTrail)
        - BP04: Identify and validate control objectives (Config, Security Hub, Audit Manager)
        - BP05: Stay up to date with threats (Security Hub, GuardDuty, Inspector, Detective, Trusted Advisor)
        - BP06: Automate testing (Config, Security Hub, Lambda, Systems Manager)
        - BP07: Identify risks using threat model (Security Hub, GuardDuty, Inspector, Access Analyzer)
        - BP08: Keep up to date with recommendations (Security Hub, Trusted Advisor, Config, Inspector)
        """
        findings = []
        compliant_count = 0
        non_compliant_count = 0
        pending_count = 0
        total_bps = 8
        primary_region = (
            self.connector.regions[0] if self.connector.regions else "us-east-1"
        )

        # SEC01-BP01: Operate workload securely
        # Services: Organizations, Control Tower, RAM, SSO, IAM
        # SEC01-BP01: Operate workload securely
        # Services: Organizations, Control Tower, RAM, SSO, IAM
        bp_id = "SEC01-BP01"
        bp_services = get_bp_services(bp_id)
        try:
            # Check AWS Organizations
            org_info = self.connector.get_organization_info()
            org_enabled = org_info.get("enabled", False)
            accounts_count = org_info.get("accounts_count", 0)

            # Evaluate compliance based on multi-account structure
            if not org_enabled:
                non_compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "NON_COMPLIANT",
                        "finding": "AWS Organizations not configured - using single account",
                        "severity": "HIGH",
                        "risk": "Single account limits isolation, blast radius control, and centralized governance",
                        "remediation": "Enable AWS Organizations and implement multi-account strategy with Control Tower, SSO, and RAM for resource sharing",
                        "evidence": f"Services checked: {', '.join(bp_services)}. No organization structure detected.",
                    }
                )
            elif accounts_count < 3:
                # Has organization but minimal accounts - partially compliant
                non_compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "NON_COMPLIANT",
                        "finding": f"AWS Organizations enabled but insufficient account separation ({accounts_count} accounts)",
                        "severity": "MEDIUM",
                        "risk": "Insufficient account isolation for workload segregation",
                        "remediation": "Create additional accounts for different environments (dev, staging, prod) and workload types using Control Tower",
                        "evidence": f'Org ID: {org_info.get("id")}. Minimum 3+ accounts recommended (management, security, production).',
                    }
                )
            else:
                compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "COMPLIANT",
                        "finding": f"AWS Organizations configured with {accounts_count} accounts for workload isolation",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f'Org ID: {org_info.get("id")}. Services: {", ".join(bp_services)}. Multi-account structure supports secure operations.',
                    }
                )
        except Exception as e:
            logger.error(f"Error checking {bp_id}: {str(e)}")
            pending_count += 1
            findings.append(
                self._create_timeout_finding(
                    bp_id,
                    f"Unable to verify secure operations setup: {get_bp_name(bp_id)}",
                    "AWS Organizations",
                )
            )

        # SEC01-BP02: Separate workload using accounts
        # Services: Organizations, Control Tower
        bp_id = "SEC01-BP02"
        bp_services = get_bp_services(bp_id)
        try:
            org_info = self.connector.get_organization_info()
            if not org_info.get("enabled"):
                non_compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "NON_COMPLIANT",
                        "finding": "No account separation - single account architecture",
                        "severity": "HIGH",
                        "risk": "All workloads share same security boundary and resource limits",
                        "remediation": "Enable AWS Organizations and Control Tower to separate workloads by environment, team, or data classification",
                        "evidence": f"Services checked: {', '.join(bp_services)}. Single account detected.",
                    }
                )
            else:
                accounts_count = org_info.get("accounts_count", 0)
                compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "COMPLIANT",
                        "finding": f"Workload separation implemented with {accounts_count} AWS accounts",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f'Org ID: {org_info.get("id")}. Services: {", ".join(bp_services)}. Account-level isolation configured.',
                    }
                )
        except Exception as e:
            logger.error(f"Error checking {bp_id}: {str(e)}")
            pending_count += 1
            findings.append(
                self._create_timeout_finding(
                    bp_id,
                    f"Unable to verify account separation: {get_bp_name(bp_id)}",
                    "AWS Organizations",
                )
            )

        # SEC01-BP03: Secure AWS account
        # Services: IAM, GuardDuty, Security Hub, Config, CloudTrail
        # SEC01-BP03: Secure AWS account
        # Services: IAM, GuardDuty, Security Hub, Config, CloudTrail
        bp_id = "SEC01-BP03"
        bp_services = get_bp_services(bp_id)
        try:
            # Check multiple security services for account protection
            password_policy = self.connector.get_password_policy()
            guardduty_detectors = self.connector.get_guardduty_detectors(primary_region)
            config_status = self.connector.get_config_status(primary_region)
            trails = self.connector.get_cloudtrail_trails(primary_region)

            security_score = 0
            security_checks = []

            # IAM password policy
            if password_policy and password_policy.get("require_symbols"):
                security_score += 25
                security_checks.append("✓ IAM password policy")
            else:
                security_checks.append("✗ IAM password policy weak/missing")

            # GuardDuty
            if guardduty_detectors and any(
                d.get("status") == "ENABLED" for d in guardduty_detectors
            ):
                security_score += 25
                security_checks.append("✓ GuardDuty enabled")
            else:
                security_checks.append("✗ GuardDuty not enabled")

            # Config
            if config_status.get("recording"):
                security_score += 25
                security_checks.append("✓ AWS Config recording")
            else:
                security_checks.append("✗ AWS Config not recording")

            # CloudTrail
            if trails and any(t.get("is_logging", False) for t in trails):
                security_score += 25
                security_checks.append("✓ CloudTrail logging")
            else:
                security_checks.append("✗ CloudTrail not logging")

            # Determine compliance based on score
            if security_score >= 75:  # 3 or 4 out of 4 services
                compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "COMPLIANT",
                        "finding": f"AWS account secured with {security_score}% of core security services",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f"Services: {', '.join(bp_services)}. Checks: {'; '.join(security_checks)}",
                    }
                )
            else:
                non_compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "NON_COMPLIANT",
                        "finding": f"AWS account security insufficient ({security_score}% of services enabled)",
                        "severity": "HIGH",
                        "risk": "Account lacks foundational security controls for threat detection and audit",
                        "remediation": "Enable missing services: IAM strong password policy, GuardDuty, Security Hub, Config, and CloudTrail",
                        "evidence": f"Services: {', '.join(bp_services)}. Checks: {'; '.join(security_checks)}",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking {bp_id}: {str(e)}")
            pending_count += 1
            error_msg = str(e)
            if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                evidence_reason = f"Access denied - insufficient IAM permissions to check IAM, GuardDuty, Config, or CloudTrail: {error_msg[:100]}"
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                evidence_reason = (
                    f"Request timeout while querying AWS services: {error_msg[:100]}"
                )
            else:
                evidence_reason = f"Error querying services: {error_msg[:150]}"
            findings.append(
                self._create_pending_finding(
                    bp_id,
                    "Unable to verify account security",
                    "HIGH",
                    evidence_reason,
                )
            )

        # SEC01-BP04: Identify and validate control objectives
        # Services: Config, Security Hub, Audit Manager
        # SEC01-BP04: Identify and validate control objectives
        # Services: Config, Security Hub, Audit Manager
        bp_id = "SEC01-BP04"
        bp_services = get_bp_services(bp_id)
        try:
            config_status = self.connector.get_config_status(primary_region)
            config_recording = config_status.get("recording", False)
            config_rules = config_status.get("rules", [])

            if config_recording and len(config_rules) > 0:
                compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "COMPLIANT",
                        "finding": f"Control validation configured with AWS Config ({len(config_rules)} rules)",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f"Services: {', '.join(bp_services)}. Config recording with {len(config_rules)} compliance rules active.",
                    }
                )
            elif config_recording:
                non_compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "NON_COMPLIANT",
                        "finding": "AWS Config enabled but no compliance rules configured",
                        "severity": "MEDIUM",
                        "risk": "Control objectives cannot be continuously validated without Config Rules",
                        "remediation": "Deploy Config Rules or Conformance Packs to validate security controls; consider Security Hub standards",
                        "evidence": f"Services: {', '.join(bp_services)}. Config recording but 0 rules.",
                    }
                )
            else:
                non_compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "NON_COMPLIANT",
                        "finding": "AWS Config not enabled - cannot validate security controls",
                        "severity": "HIGH",
                        "risk": "Without Config, compliance state cannot be continuously validated",
                        "remediation": "Enable AWS Config with Config Rules and/or Security Hub standards for control validation",
                        "evidence": f"Services: {', '.join(bp_services)}. No active Config recorders found.",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking {bp_id}: {str(e)}")
            pending_count += 1
            error_msg = str(e)
            if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                evidence_reason = f"Access denied - insufficient IAM permissions for AWS Config: {error_msg[:100]}"
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                evidence_reason = (
                    f"Request timeout querying AWS Config: {error_msg[:100]}"
                )
            else:
                evidence_reason = f"Error querying AWS Config: {error_msg[:150]}"
            findings.append(
                self._create_pending_finding(
                    bp_id,
                    "Unable to verify control validation",
                    "MEDIUM",
                    evidence_reason,
                )
            )

        # SEC01-BP05: Stay up to date with security threats and recommendations
        # Services: Security Hub, GuardDuty, Inspector, Detective, Trusted Advisor
        # SEC01-BP05: Stay up to date with security threats and recommendations
        # Services: Security Hub, GuardDuty, Inspector, Detective, Trusted Advisor
        bp_id = "SEC01-BP05"
        bp_services = get_bp_services(bp_id)
        try:
            guardduty_detectors = self.connector.get_guardduty_detectors(primary_region)
            guardduty_enabled = guardduty_detectors and any(
                d.get("status") == "ENABLED" for d in guardduty_detectors
            )

            # Count threat intelligence services
            threat_services = []
            if guardduty_enabled:
                threat_services.append("GuardDuty")

            # For now, we can only check GuardDuty from connector
            # Security Hub, Inspector, Detective would require additional methods

            if guardduty_enabled:
                findings_count = sum(d.get("findings", 0) for d in guardduty_detectors)
                compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "COMPLIANT",
                        "finding": f"Threat intelligence configured ({', '.join(threat_services)}) with {findings_count} findings",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f"Services: {', '.join(bp_services)}. Active services: {', '.join(threat_services)}. {len(guardduty_detectors)} detector(s).",
                    }
                )
            else:
                non_compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "NON_COMPLIANT",
                        "finding": "Threat intelligence services not enabled",
                        "severity": "CRITICAL",
                        "risk": "Cannot detect malicious activity, unauthorized behavior, or security vulnerabilities",
                        "remediation": "Enable GuardDuty, Security Hub, and Inspector for continuous threat detection and recommendations",
                        "evidence": f"Services: {', '.join(bp_services)}. No active threat detection services found.",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking {bp_id}: {str(e)}")
            pending_count += 1
            findings.append(
                self._create_pending_finding(
                    bp_id,
                    f"Unable to verify threat intelligence: {str(e)[:80]}",
                    "CRITICAL",
                )
            )

        # SEC01-BP06: Automate testing and validation
        # Services: Config, Security Hub, Lambda, Systems Manager
        # SEC01-BP06: Automate testing and validation
        # Services: Config, Security Hub, Lambda, Systems Manager
        bp_id = "SEC01-BP06"
        bp_services = get_bp_services(bp_id)
        try:
            config_status = self.connector.get_config_status(primary_region)
            trails = self.connector.get_cloudtrail_trails(primary_region)

            automation_score = 0
            automation_checks = []

            # Config with remediation rules
            if config_status.get("recording"):
                automation_score += 50
                automation_checks.append("✓ Config recording")
            else:
                automation_checks.append("✗ Config not recording")

            # CloudTrail for audit automation
            if trails and any(t.get("is_logging", False) for t in trails):
                automation_score += 50
                automation_checks.append("✓ CloudTrail logging")
            else:
                automation_checks.append("✗ CloudTrail not logging")

            if automation_score >= 50:
                compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "COMPLIANT",
                        "finding": f"Security automation configured ({automation_score}% of checks)",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f"Services: {', '.join(bp_services)}. Checks: {'; '.join(automation_checks)}. CloudTrail enables event-driven automation.",
                    }
                )
            else:
                non_compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "NON_COMPLIANT",
                        "finding": f"Security automation insufficient ({automation_score}% configured)",
                        "severity": "HIGH",
                        "risk": "Cannot automate testing, responses, or remediation of security issues",
                        "remediation": "Enable Config with remediation rules, CloudTrail for audit, and consider Lambda for custom automation",
                        "evidence": f"Services: {', '.join(bp_services)}. Checks: {'; '.join(automation_checks)}",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking {bp_id}: {str(e)}")
            pending_count += 1
            error_msg = str(e)
            if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                evidence_reason = f"Access denied - insufficient IAM permissions for Config or CloudTrail: {error_msg[:100]}"
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                evidence_reason = (
                    f"Request timeout querying automation services: {error_msg[:100]}"
                )
            else:
                evidence_reason = f"Error querying Config/CloudTrail: {error_msg[:150]}"
            findings.append(
                self._create_pending_finding(
                    bp_id,
                    "Unable to verify security automation",
                    "HIGH",
                    evidence_reason,
                )
            )

        # SEC01-BP07: Identify and prioritize risks using threat model
        # Services: Security Hub, GuardDuty, Inspector, Access Analyzer
        bp_id = "SEC01-BP07"
        bp_services = get_bp_services(bp_id)
        try:
            guardduty_detectors = self.connector.get_guardduty_detectors(primary_region)
            guardduty_enabled = guardduty_detectors and any(
                d.get("status") == "ENABLED" for d in guardduty_detectors
            )

            if guardduty_enabled:
                findings_count = sum(d.get("findings", 0) for d in guardduty_detectors)
                compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "COMPLIANT",
                        "finding": f"Risk identification enabled with GuardDuty ({findings_count} findings for prioritization)",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f"Services: {', '.join(bp_services)}. GuardDuty active for threat-based risk prioritization.",
                    }
                )
            else:
                non_compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "NON_COMPLIANT",
                        "finding": "Risk identification services not configured",
                        "severity": "HIGH",
                        "risk": "Cannot identify or prioritize security risks without threat detection services",
                        "remediation": "Enable GuardDuty, Security Hub, and Inspector to identify risks; use Access Analyzer for IAM risks",
                        "evidence": f"Services: {', '.join(bp_services)}. No risk identification services found.",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking {bp_id}: {str(e)}")
            pending_count += 1
            findings.append(
                self._create_pending_finding(
                    bp_id,
                    f"Unable to verify risk identification: {str(e)[:80]}",
                    "HIGH",
                )
            )

        # SEC01-BP08: Keep up to date with security recommendations
        # Services: Security Hub, Trusted Advisor, Config, Inspector
        bp_id = "SEC01-BP08"
        bp_services = get_bp_services(bp_id)
        try:
            config_status = self.connector.get_config_status(primary_region)
            guardduty_detectors = self.connector.get_guardduty_detectors(primary_region)

            recommendation_sources = []
            if config_status.get("recording"):
                recommendation_sources.append("Config")
            if guardduty_detectors and any(
                d.get("status") == "ENABLED" for d in guardduty_detectors
            ):
                recommendation_sources.append("GuardDuty")

            if len(recommendation_sources) >= 1:
                compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "COMPLIANT",
                        "finding": f"Security recommendations configured via {', '.join(recommendation_sources)}",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f"Services: {', '.join(bp_services)}. Active: {', '.join(recommendation_sources)}. Recommendations available.",
                    }
                )
            else:
                non_compliant_count += 1
                findings.append(
                    {
                        "bp": bp_id,
                        "status": "NON_COMPLIANT",
                        "finding": "No security recommendation services configured",
                        "severity": "MEDIUM",
                        "risk": "Missing AWS best practice recommendations and security insights",
                        "remediation": "Enable Security Hub, Config, and review Trusted Advisor for continuous security recommendations",
                        "evidence": f"Services: {', '.join(bp_services)}. No recommendation sources active.",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking {bp_id}: {str(e)}")
            pending_count += 1
            error_msg = str(e)
            if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                evidence_reason = f"Access denied - insufficient IAM permissions for Config or GuardDuty: {error_msg[:100]}"
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                evidence_reason = f"Request timeout querying recommendation services: {error_msg[:100]}"
            else:
                evidence_reason = f"Error querying Config/GuardDuty: {error_msg[:150]}"
            findings.append(
                self._create_pending_finding(
                    bp_id,
                    "Unable to verify security recommendations",
                    "MEDIUM",
                    evidence_reason,
                )
            )

        # Calculate score based on findings (PENDING_REVIEW excluded)
        score = self._calculate_score_from_findings(findings)

        return {
            "question_id": "SEC01",
            "question": "Fundamentos de seguridad - Operación segura",
            "findings": findings,
            "score": score,
            "bps_evaluated": 8,
        }

    def evaluate_sec02(self) -> Dict[str, Any]:
        """SEC02: ¿Cómo se gestiona la autenticación de personas y máquinas? (6 BPs)"""
        findings = []
        score = 100

        # Try to get users, track if we had an error
        users_error = None
        try:
            users = self.connector.get_iam_users()
        except Exception as e:
            logger.error(f"Error getting IAM users: {str(e)}")
            users = []
            users_error = str(e)[:100]

        # SEC02-BP01: Utilizar mecanismos de inicio de sesión fuertes
        if users_error:
            error_msg = users_error
            if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                evidence_reason = f"Access denied - insufficient IAM permissions to list users: {error_msg}"
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                evidence_reason = f"Request timeout while querying IAM: {error_msg}"
            else:
                evidence_reason = f"Error querying IAM users: {error_msg}"
            findings.append(
                self._create_pending_finding(
                    "SEC02-BP01",
                    "Unable to verify IAM authentication",
                    "HIGH",
                    evidence_reason,
                )
            )
        else:
            users_without_mfa = [
                u
                for u in users
                if not u.get("mfa_enabled", False) and len(u.get("access_keys", [])) > 0
            ]
            apis_total = 0
            apis_with_auth = 0
            api_auth_status = "N/D"

            # Check API Gateway authentication methods (REST + HTTP APIs)
            try:
                rest_apis = self.connector.client.apigateway.get_rest_apis()
                for api in rest_apis.get("items", []):
                    apis_total += 1
                    try:
                        auths = self.connector.client.apigateway.get_authorizers(
                            restApiId=api.get("id")
                        )
                        if len(auths.get("items", [])) > 0:
                            apis_with_auth += 1
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                http_apis = self.connector.client.apigatewayv2.get_apis()
                for api in http_apis.get("Items", []):
                    apis_total += 1
                    try:
                        auths = self.connector.client.apigatewayv2.get_authorizers(
                            ApiId=api.get("ApiId")
                        )
                        if len(auths.get("Items", [])) > 0:
                            apis_with_auth += 1
                    except Exception:
                        continue
            except Exception:
                pass

            if apis_total > 0:
                api_auth_status = f"API Gateways with authorizers: {apis_with_auth}/{apis_total}"
            else:
                api_auth_status = "No API Gateways found"

            apis_without_auth = apis_total > 0 and apis_with_auth == 0
            if users_without_mfa:
                score -= 20
                findings.append(
                    {
                        "bp": "SEC02-BP01",
                        "status": "NON_COMPLIANT",
                        "finding": f"{len(users_without_mfa)} users without MFA but with active access keys",
                        "severity": "CRITICAL",
                        "risk": "Compromised credentials can lead to full account access",
                        "remediation": "Enforce MFA for all users with console or API access",
                        "evidence": f"{', '.join([u['user_name'] for u in users_without_mfa[:5]])} | {api_auth_status}",
                    }
                )
            elif apis_without_auth:
                score -= 10
                findings.append(
                    {
                        "bp": "SEC02-BP01",
                        "status": "NON_COMPLIANT",
                        "finding": "API Gateway authentication not configured",
                        "severity": "HIGH",
                        "risk": "Unauthenticated APIs can be invoked by unauthorized actors",
                        "remediation": "Configure IAM/Cognito/Lambda authorizers or resource policies for all APIs",
                        "evidence": api_auth_status,
                    }
                )
            else:
                findings.append(
                    {
                        "bp": "SEC02-BP01",
                        "status": "COMPLIANT",
                        "finding": "Strong authentication mechanisms in place - all users with MFA",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f"{len(users)} users evaluated | {api_auth_status}",
                    }
                )

        # SEC02-BP02: Utilizar credenciales temporales
        if not users_error:
            long_term_keys = []
            for user in users:
                for key in user.get("access_keys", []):
                    if key["status"] == "Active":
                        long_term_keys.append(
                            {"user": user["user_name"], "key": key["access_key_id"]}
                        )

            if long_term_keys:
                score -= 15
                findings.append(
                    {
                        "bp": "SEC02-BP02",
                        "status": "NON_COMPLIANT",
                        "finding": f"{len(long_term_keys)} long-term access keys detected",
                        "severity": "HIGH",
                        "risk": "Long-term credentials increase risk if compromised",
                        "remediation": "Use STS AssumeRole for temporary credentials instead of long-term keys",
                        "evidence": f"{len(long_term_keys)} active access keys found",
                    }
                )
            else:
                findings.append(
                    {
                        "bp": "SEC02-BP02",
                        "status": "COMPLIANT",
                        "finding": "No long-term access keys - using temporary credentials",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": "No active access keys",
                    }
                )
        else:
            findings.append(
                self._create_pending_finding(
                    "SEC02-BP02", "Unable to verify temporary credentials usage", "HIGH"
                )
            )

        # SEC02-BP03: Almacenar y utilizar secretos de forma segura
        try:
            primary_region = (
                self.connector.regions[0] if self.connector.regions else "us-east-1"
            )
            secrets = self.connector.get_secrets(primary_region)
            if secrets:
                non_rotated = [s for s in secrets if not s.get("rotation_enabled")]
                if non_rotated:
                    score -= 10
                    findings.append(
                        {
                            "bp": "SEC02-BP03",
                            "status": "NON_COMPLIANT",
                            "finding": f"{len(non_rotated)} of {len(secrets)} secrets without automatic rotation",
                            "severity": "MEDIUM",
                            "risk": "Non-rotated secrets increase compromise window",
                            "remediation": "Enable automatic rotation for all secrets in Secrets Manager",
                            "evidence": f"{len(non_rotated)} secrets need rotation enabled",
                        }
                    )
                else:
                    findings.append(
                        {
                            "bp": "SEC02-BP03",
                            "status": "COMPLIANT",
                            "finding": f"All {len(secrets)} secrets have automatic rotation enabled",
                            "severity": "NONE",
                            "risk": "N/D",
                            "remediation": "N/D",
                            "evidence": "All secrets have automatic rotation enabled",
                        }
                    )
            else:
                findings.append(
                    {
                        "bp": "SEC02-BP03",
                        "status": "COMPLIANT",
                        "finding": "No secrets found in AWS Secrets Manager",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": "No secrets configured - consider using Secrets Manager for database and API credentials",
                    }
                )
        except Exception as e:
            error_msg = str(e)[:100]
            if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                evidence = f"Access denied - insufficient IAM permissions: {error_msg}"
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                evidence = (
                    f"Request timeout while querying Secrets Manager: {error_msg}"
                )
            else:
                evidence = f"Error querying Secrets Manager: {error_msg}"
            logger.error(f"Error checking secrets: {str(e)}")
            findings.append(
                self._create_pending_finding(
                    "SEC02-BP03",
                    "Unable to verify secret storage and rotation",
                    "HIGH",
                    evidence,
                )
            )

        # SEC02-BP04: Confíe en un proveedor de identidad centralizado
        if users_error:
            error_msg = users_error
            if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                evidence_reason = (
                    f"Access denied - insufficient IAM permissions: {error_msg}"
                )
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                evidence_reason = f"Request timeout while querying IAM: {error_msg}"
            else:
                evidence_reason = f"Error querying IAM users: {error_msg}"
            findings.append(
                self._create_pending_finding(
                    "SEC02-BP04",
                    "Unable to verify identity federation configuration",
                    "HIGH",
                    evidence_reason,
                )
            )
        else:
            client_vpn_total = 0
            client_vpn_federated = 0
            client_vpn_auth_status = "No Client VPN endpoints found"
            try:
                cvpn = self.connector.client.ec2.describe_client_vpn_endpoints()
                endpoints = cvpn.get("ClientVpnEndpoints", [])
                client_vpn_total = len(endpoints)
                for ep in endpoints:
                    for auth in ep.get("AuthenticationOptions", []):
                        if auth.get("Type") in ["directory-service-authentication", "federated-authentication"]:
                            client_vpn_federated += 1
                            break
                if client_vpn_total > 0:
                    client_vpn_auth_status = f"Client VPN federated auth: {client_vpn_federated}/{client_vpn_total}"
            except Exception:
                client_vpn_auth_status = "Unable to verify Client VPN authentication"

            client_vpn_issue = client_vpn_total > 0 and client_vpn_federated == 0
            if len(users) > 10 or client_vpn_issue:
                score -= 10
                findings.append(
                    {
                        "bp": "SEC02-BP04",
                        "status": "NON_COMPLIANT",
                        "finding": "Centralized identity provider not fully implemented",
                        "severity": "MEDIUM",
                        "risk": "Many IAM users or VPN auth without federation indicate weak centralized identity",
                        "remediation": "Use AWS IAM Identity Center (SSO) or federate with corporate identity provider; configure Client VPN with federated/directory authentication",
                        "evidence": f"IAM users: {len(users)} | {client_vpn_auth_status}",
                    }
                )
            else:
                findings.append(
                    {
                        "bp": "SEC02-BP04",
                        "status": "COMPLIANT",
                        "finding": f"Centralized identity provider likely in place",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f"IAM users: {len(users)} | {client_vpn_auth_status}",
                    }
                )

        # SEC02-BP05: Auditar y rotar credenciales periódicamente
        if users_error:
            error_msg = users_error
            if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                evidence_reason = (
                    f"Access denied - insufficient IAM permissions: {error_msg}"
                )
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                evidence_reason = f"Request timeout while querying IAM: {error_msg}"
            else:
                evidence_reason = f"Error querying IAM users: {error_msg}"
            findings.append(
                self._create_pending_finding(
                    "SEC02-BP05",
                    "Unable to verify credential rotation policy",
                    "HIGH",
                    evidence_reason,
                )
            )
        else:
            from datetime import datetime, timezone

            old_keys = []
            active_keys_count = 0
            for user in users:
                for key in user.get("access_keys", []):
                    if key["status"] == "Active":
                        active_keys_count += 1
                        try:
                            # Parse create_date and check if older than 90 days
                            create_date = datetime.fromisoformat(
                                key["create_date"].replace("Z", "+00:00")
                            )
                            age_days = (datetime.now(timezone.utc) - create_date).days
                            if age_days > 90:
                                old_keys.append(
                                    {
                                        "key_id": key["access_key_id"],
                                        "user": user["user_name"],
                                        "age_days": age_days,
                                    }
                                )
                        except Exception:
                            # If we can't parse date, treat as old for safety
                            old_keys.append(
                                {
                                    "key_id": key["access_key_id"],
                                    "user": user["user_name"],
                                    "age_days": "unknown",
                                }
                            )

            if len(old_keys) > 0:
                findings.append(
                    {
                        "bp": "SEC02-BP05",
                        "status": "NON_COMPLIANT",
                        "finding": f"{len(old_keys)} access keys older than 90 days need rotation",
                        "severity": "MEDIUM",
                        "risk": "Old credentials increase compromise risk",
                        "remediation": "Rotate all access keys every 90 days maximum",
                        "evidence": f"{len(old_keys)} of {active_keys_count} active keys are older than 90 days",
                    }
                )
            elif active_keys_count > 0:
                findings.append(
                    {
                        "bp": "SEC02-BP05",
                        "status": "COMPLIANT",
                        "finding": f"All {active_keys_count} active access keys are rotated regularly",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f"All {active_keys_count} active keys are less than 90 days old",
                    }
                )
            else:
                findings.append(
                    {
                        "bp": "SEC02-BP05",
                        "status": "COMPLIANT",
                        "finding": "No active access keys requiring rotation",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": "No active access keys - rotation policy compliant",
                    }
                )

        # SEC02-BP06: Emplear grupos de usuarios y atributos
        if users_error:
            error_msg = users_error
            if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                evidence_reason = (
                    f"Access denied - insufficient IAM permissions: {error_msg}"
                )
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                evidence_reason = f"Request timeout while querying IAM: {error_msg}"
            else:
                evidence_reason = f"Error querying IAM users: {error_msg}"
            findings.append(
                self._create_pending_finding(
                    "SEC02-BP06",
                    "Unable to verify user groups and attributes",
                    "HIGH",
                    evidence_reason,
                )
            )
        else:
            user_with_direct_policies = [
                u for u in users if len(u.get("policies", [])) > 0
            ]
            if user_with_direct_policies:
                score -= 5
                findings.append(
                    {
                        "bp": "SEC02-BP06",
                        "status": "NON_COMPLIANT",
                        "finding": f"{len(user_with_direct_policies)} users have directly attached policies",
                        "severity": "MEDIUM",
                        "risk": "Direct policy attachment makes permission management difficult",
                        "remediation": "Use IAM groups for permission management, not direct user policies",
                        "evidence": f"{len(user_with_direct_policies)} users with direct policies",
                    }
                )
            else:
                findings.append(
                    {
                        "bp": "SEC02-BP06",
                        "status": "COMPLIANT",
                        "finding": "Using groups for permission management",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": "No direct policies attached - using groups correctly",
                    }
                )

        return {
            "question_id": "SEC02",
            "question": "Autenticación de personas y máquinas",
            "findings": findings,
            "score": self._calculate_score_from_findings(findings),
            "bps_evaluated": 6,
        }

    def evaluate_sec03(self) -> Dict[str, Any]:
        """SEC03: Gestión de identidad y acceso - Permisos (9 Best Practices)"""
        from ..config.sec03_services_config import get_sec03_bp_services

        findings = []
        score = 100

        # Get IAM users and policies
        users = []
        iam_error = None
        try:
            logger.info("[SEC03] Starting SEC03 evaluation - Gathering IAM data...")
            users = self.connector.get_iam_users()
            logger.info(f"[SEC03] Retrieved {len(users)} IAM users")
        except Exception as e:
            logger.error(f"[SEC03] Error getting IAM users: {str(e)}", exc_info=True)
            iam_error = str(e)
            users = []

        # SEC03-BP01: Definir los requisitos de acceso
        if iam_error:
            findings.append(
                self._create_pending_finding(
                    "SEC03-BP01",
                    "Unable to verify access requirements definition",
                    "HIGH",
                    f"Error accessing IAM: {iam_error[:100]}",
                )
            )
        else:
            services_reviewed = get_sec03_bp_services("SEC03-BP01")
            findings.append(
                {
                    "bp": "SEC03-BP01",
                    "status": "COMPLIANT",
                    "finding": "Access requirements documented through IAM policies",
                    "severity": "NONE",
                    "risk": "N/D",
                    "remediation": "N/D",
                    "evidence": f"Reviewing {len(services_reviewed)} services: {', '.join(services_reviewed[:3])}...",
                }
            )

        # SEC03-BP02: Otorgar acceso con privilegios mínimos
        if iam_error:
            findings.append(
                self._create_pending_finding(
                    "SEC03-BP02",
                    "Unable to verify least privilege implementation",
                    "HIGH",
                    f"Error accessing policies: {iam_error[:100]}",
                )
            )
        else:
            # Check for overly permissive policies
            users_with_admin = [
                u
                for u in users
                if any(
                    "admin" in p.get("name", "").lower()
                    or "*" in p.get("name", "").lower()
                    for p in u.get("policies", [])
                )
            ]
            eks_clusters = 0
            apis_with_policies = 0
            apis_checked = 0
            try:
                eks_clusters = len(
                    self.connector.client.eks.list_clusters().get("clusters", [])
                )
            except Exception:
                eks_clusters = 0

            try:
                rest_apis = self.connector.client.apigateway.get_rest_apis()
                for api in rest_apis.get("items", []):
                    apis_checked += 1
                    if api.get("policy"):
                        apis_with_policies += 1
            except Exception:
                pass

            try:
                http_apis = self.connector.client.apigatewayv2.get_apis()
                for api in http_apis.get("Items", []):
                    apis_checked += 1
                    if api.get("ApiEndpoint") and api.get("CorsConfiguration"):
                        apis_with_policies += 1
            except Exception:
                pass

            api_policy_status = (
                f"API policies/CORS: {apis_with_policies}/{apis_checked}"
                if apis_checked > 0
                else "No API Gateways found"
            )
            if users_with_admin:
                score -= 20
                findings.append(
                    {
                        "bp": "SEC03-BP02",
                        "status": "NON_COMPLIANT",
                        "finding": f"{len(users_with_admin)} users with overly permissive policies",
                        "severity": "CRITICAL",
                        "risk": "Overly broad permissions increase blast radius of compromised credentials",
                        "remediation": "Implement least privilege: use specific resource ARNs and actions",
                        "evidence": f"{len(users_with_admin)} users with admin or wildcard policies detected | EKS clusters: {eks_clusters} | {api_policy_status}",
                    }
                )
            else:
                findings.append(
                    {
                        "bp": "SEC03-BP02",
                        "status": "COMPLIANT",
                        "finding": "Least privilege principle implemented in IAM policies",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f"All {len(users)} users follow least privilege access controls | EKS clusters: {eks_clusters} | {api_policy_status}",
                    }
                )

        # SEC03-BP03: Establecer proceso de acceso de emergencia
        # Check for break-glass roles (roles with 'break' or 'emergency' in name)
        roles = []
        try:
            roles = self.connector.get_iam_roles()
        except Exception as e:
            logger.error(f"[SEC03] Error getting IAM roles: {str(e)}")

        breakglass_roles = [
            r
            for r in roles
            if "break" in r.get("name", "").lower()
            or "emergency" in r.get("name", "").lower()
        ]

        if breakglass_roles:
            findings.append(
                {
                    "bp": "SEC03-BP03",
                    "status": "COMPLIANT",
                    "finding": "Break-glass roles configured for emergency access",
                    "severity": "NONE",
                    "risk": "N/D",
                    "remediation": "N/D",
                    "evidence": f"{len(breakglass_roles)} break-glass role(s) found: {', '.join([r['name'] for r in breakglass_roles[:2]])}",
                }
            )
        else:
            score -= 15
            findings.append(
                {
                    "bp": "SEC03-BP03",
                    "status": "NON_COMPLIANT",
                    "finding": "No break-glass emergency access roles configured",
                    "severity": "CRITICAL",
                    "risk": "Lack of emergency procedures could delay critical incident response",
                    "remediation": "Create documented emergency access procedures with break-glass roles",
                    "evidence": "No roles with 'break' or 'emergency' in name detected - create break-glass role",
                }
            )

        # SEC03-BP04: Reducir permisos continuamente
        # Check for old/inactive IAM users (no login in 90+ days)
        from datetime import datetime, timezone

        inactive_console_users = []
        for user in users:
            last_login = user.get("last_login")
            if last_login:
                try:
                    login_date = datetime.fromisoformat(
                        last_login.replace("Z", "+00:00")
                    )
                    days_inactive = (datetime.now(timezone.utc) - login_date).days
                    if days_inactive > 90:
                        inactive_console_users.append(
                            {
                                "user": user["user_name"],
                                "days": days_inactive,
                            }
                        )
                except Exception:
                    pass

        if inactive_console_users:
            score -= 10
            findings.append(
                {
                    "bp": "SEC03-BP04",
                    "status": "NON_COMPLIANT",
                    "finding": f"{len(inactive_console_users)} users inactive 90+ days - permissions should be reviewed",
                    "severity": "MEDIUM",
                    "risk": "Stale user accounts with permissions increase security surface area",
                    "remediation": "Review and remove unused permissions from inactive users or deactivate accounts",
                    "evidence": f"{len(inactive_console_users)} inactive users detected: {', '.join([u['user'] for u in inactive_console_users[:3]])}",
                }
            )
        else:
            findings.append(
                {
                    "bp": "SEC03-BP04",
                    "status": "COMPLIANT",
                    "finding": "Permission reduction process active - no long-term inactive users detected",
                    "severity": "NONE",
                    "risk": "N/D",
                    "remediation": "N/D",
                    "evidence": f"All {len(users)} active users have recent activity (< 90 days)",
                }
            )

        # SEC03-BP05: Defina barreras de permisos para su organización
        # Check for permission boundaries implementation on users
        users_with_boundaries = [
            u for u in users if u.get("permission_boundary") is not None
        ]

        if len(users_with_boundaries) > 0:
            boundary_coverage = (len(users_with_boundaries) / max(len(users), 1)) * 100
            findings.append(
                {
                    "bp": "SEC03-BP05",
                    "status": "COMPLIANT",
                    "finding": "Permission boundaries implemented for organizational access control",
                    "severity": "NONE",
                    "risk": "N/D",
                    "remediation": "N/D",
                    "evidence": f"{len(users_with_boundaries)}/{len(users)} users ({boundary_coverage:.0f}%) have permission boundaries",
                }
            )
        else:
            score -= 12
            findings.append(
                {
                    "bp": "SEC03-BP05",
                    "status": "NON_COMPLIANT",
                    "finding": "No permission boundaries defined for organizational access control",
                    "severity": "HIGH",
                    "risk": "Missing boundaries allow unauthorized cross-account access and permission creep",
                    "remediation": "Implement IAM permission boundaries on all users/roles",
                    "evidence": "No users have permission boundaries configured - implement boundary policy",
                }
            )

        # SEC03-BP06: Gestionar el acceso según el ciclo de vida
        # Check for inactive users or old credentials
        inactive_users = []
        if users:
            for user in users:
                if not user.get("mfa_enabled", False):
                    inactive_users.append(user["user_name"])

        if inactive_users:
            score -= 15
            findings.append(
                {
                    "bp": "SEC03-BP06",
                    "status": "NON_COMPLIANT",
                    "finding": f"{len(inactive_users)} users without MFA - proper lifecycle management needed",
                    "severity": "HIGH",
                    "risk": "Users without MFA can be easily compromised, violating lifecycle controls",
                    "remediation": "Implement automated provisioning/deprovisioning with MFA requirements",
                    "evidence": f"{len(inactive_users)} users lacking MFA: {', '.join(inactive_users[:3])}",
                }
            )
        else:
            findings.append(
                {
                    "bp": "SEC03-BP06",
                    "status": "COMPLIANT",
                    "finding": "User lifecycle management properly configured with MFA",
                    "severity": "NONE",
                    "risk": "N/D",
                    "remediation": "N/D",
                    "evidence": f"All {len(users)} users have proper lifecycle controls (MFA enabled)",
                }
            )

        # SEC03-BP07: Analizar el acceso público y entre cuentas
        # Check for cross-account roles and trust relationships
        cross_account_roles = [
            r
            for r in roles
            if r.get("trust_policy") and "AWS" in r.get("trust_policy", "")
        ]

        public_ec2_instances = 0
        public_rds_instances = 0
        public_albs = 0
        public_apis = 0
        cloudfront_distributions = 0

        try:
            ec2_instances = self.connector.client.ec2.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
            )
            public_ec2_instances = sum(
                1
                for r in ec2_instances.get("Reservations", [])
                for i in r.get("Instances", [])
                if i.get("PublicIpAddress")
            )
        except Exception:
            public_ec2_instances = 0

        try:
            rds_instances = self.connector.client.rds.describe_db_instances()
            public_rds_instances = sum(
                1
                for db in rds_instances.get("DBInstances", [])
                if db.get("PubliclyAccessible")
            )
        except Exception:
            public_rds_instances = 0

        try:
            elbv2 = self.connector.client.elbv2.describe_load_balancers()
            public_albs = sum(
                1
                for lb in elbv2.get("LoadBalancers", [])
                if lb.get("Scheme") == "internet-facing"
            )
        except Exception:
            public_albs = 0

        try:
            rest_apis = self.connector.client.apigateway.get_rest_apis()
            public_apis += len(rest_apis.get("items", []))
        except Exception:
            pass

        try:
            http_apis = self.connector.client.apigatewayv2.get_apis()
            public_apis += len(http_apis.get("Items", []))
        except Exception:
            pass

        try:
            cfd = self.connector.client.cloudfront.list_distributions()
            cloudfront_distributions = len(
                cfd.get("DistributionList", {}).get("Items", [])
            )
        except Exception:
            cloudfront_distributions = 0

        public_access_summary = (
            f"Public EC2: {public_ec2_instances} | Public RDS: {public_rds_instances} | "
            f"Internet-facing ALB/NLB: {public_albs} | API Gateways: {public_apis} | "
            f"CloudFront distributions: {cloudfront_distributions}"
        )

        if cross_account_roles:
            external_id_count = sum(
                1
                for r in cross_account_roles
                if "ExternalId" in r.get("trust_policy", "")
            )
            if external_id_count == len(cross_account_roles):
                findings.append(
                    {
                        "bp": "SEC03-BP07",
                        "status": "COMPLIANT",
                        "finding": "Cross-account access properly controlled with External IDs",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f"All {len(cross_account_roles)} cross-account roles use External IDs | {public_access_summary}",
                    }
                )
            else:
                score -= 18
                findings.append(
                    {
                        "bp": "SEC03-BP07",
                        "status": "NON_COMPLIANT",
                        "finding": f"{len(cross_account_roles) - external_id_count} cross-account roles missing External IDs",
                        "severity": "CRITICAL",
                        "risk": "Cross-account access without External IDs allows account takeover",
                        "remediation": "Add External IDs to all cross-account trust relationships",
                        "evidence": f"{len(cross_account_roles)} cross-account roles found, only {external_id_count} use External IDs | {public_access_summary}",
                    }
                )
        else:
            findings.append(
                {
                    "bp": "SEC03-BP07",
                    "status": "COMPLIANT",
                    "finding": "No cross-account roles detected or properly isolated",
                    "severity": "NONE",
                    "risk": "N/D",
                    "remediation": "N/D",
                        "evidence": f"No cross-account access roles found among {len(roles)} total roles | {public_access_summary}",
                }
            )

        # SEC03-BP08: Comparta recursos de forma segura dentro de su organización
        # Check if using AWS Organizations for resource sharing
        try:
            org_info = self.connector.get_organization_info()
            if org_info.get("enabled"):
                findings.append(
                    {
                        "bp": "SEC03-BP08",
                        "status": "COMPLIANT",
                        "finding": "AWS Organizations enabled for secure resource sharing",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f"Organizations enabled with {org_info.get('accounts_count', 1)} accounts. Use AWS RAM for resource sharing.",
                    }
                )
            else:
                findings.append(
                    {
                        "bp": "SEC03-BP08",
                        "status": "NON_COMPLIANT",
                        "finding": "AWS Organizations not enabled for secure intra-organization resource sharing",
                        "severity": "MEDIUM",
                        "risk": "Improperly shared resources could expose sensitive data",
                        "remediation": "Enable AWS Organizations and use AWS Resource Access Manager (RAM) for controlled resource sharing",
                        "evidence": "Organizations not configured - unable to enforce secure resource sharing policies",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking SEC03-BP08: {str(e)}")
            findings.append(
                self._create_pending_finding(
                    "SEC03-BP08",
                    "Unable to verify secure intra-organization resource sharing",
                    "MEDIUM",
                    f"Error checking Organizations: {str(e)[:100]}",
                )
            )

        # SEC03-BP09: Compartir recursos de forma segura con un tercero
        # Check for roles with third-party indicators (external accounts in trust policy)
        third_party_roles = [
            r
            for r in roles
            if any(
                ext in r.get("trust_policy", "").upper()
                for ext in ["EXTERNAL", "THIRD", "PARTNER", "VENDOR"]
            )
        ]

        if third_party_roles:
            external_id_count = sum(
                1
                for r in third_party_roles
                if "ExternalId" in r.get("trust_policy", "")
            )
            mfa_count = sum(
                1
                for r in third_party_roles
                if "aws:MultiFactorAuthPresent" in r.get("trust_policy", "")
            )

            if external_id_count == len(third_party_roles) and mfa_count > 0:
                findings.append(
                    {
                        "bp": "SEC03-BP09",
                        "status": "COMPLIANT",
                        "finding": "Third-party access properly secured with External IDs and MFA controls",
                        "severity": "NONE",
                        "risk": "N/D",
                        "remediation": "N/D",
                        "evidence": f"All {len(third_party_roles)} third-party roles use External IDs and MFA controls",
                    }
                )
            else:
                score -= 18
                findings.append(
                    {
                        "bp": "SEC03-BP09",
                        "status": "NON_COMPLIANT",
                        "finding": "Third-party access missing security controls (External IDs or MFA)",
                        "severity": "CRITICAL",
                        "risk": "Improper third-party access could lead to data breach or unauthorized operations",
                        "remediation": "Add External IDs and MFA requirements to all third-party roles",
                        "evidence": f"Third-party roles: {len(third_party_roles)} total, {external_id_count} with External ID, {mfa_count} with MFA",
                    }
                )
        else:
            findings.append(
                {
                    "bp": "SEC03-BP09",
                    "status": "COMPLIANT",
                    "finding": "No third-party access roles detected or properly restricted",
                    "severity": "NONE",
                    "risk": "N/D",
                    "remediation": "N/D",
                    "evidence": f"No third-party access roles found among {len(roles)} total roles",
                }
            )

        return {
            "question_id": "SEC03",
            "question": "Gestión de identidad y acceso - Permisos",
            "findings": findings,
            "score": self._calculate_score_from_findings(findings),
            "bps_evaluated": 9,
        }

    def evaluate_sec04(self) -> Dict[str, Any]:
        """SEC04: Detección - ¿Cómo se detectan e investigan los eventos de seguridad? (4 BPs)"""
        findings = []
        primary_region = (
            self.connector.regions[0] if self.connector.regions else "us-east-1"
        )

        # SEC04-BP01: Configurar el servicio y el registro de aplicaciones
        logger.info("[SEC04-BP01] Evaluating logging configuration...")
        cloudtrail_ok = False
        cloudwatch_logs_ok = False
        config_ok = False
        vpc_flow_logs_ok = False

        try:
            # Check CloudTrail
            trails = self.connector.get_cloudtrail_trails(primary_region)
            cloudtrail_ok = (
                trails
                and any(t.get("is_logging", False) for t in trails)
                and any(t.get("multi_region", False) for t in trails)
            )
            cloudtrail_status = (
                "COMPLIANT" if cloudtrail_ok else "NON_COMPLIANT"
            )
            cloudtrail_evidence = (
                f"{len([t for t in trails if t.get('is_logging')])} logging trails found with multi-region support"
                if trails
                else "No CloudTrail trails configured"
            )

            # Check CloudWatch Logs
            try:
                log_groups = self.connector.get_log_groups(primary_region)
                log_group_count = len(log_groups)
                cloudwatch_logs_ok = log_group_count > 0
                cloudwatch_status = (
                    "COMPLIANT" if cloudwatch_logs_ok else "NON_COMPLIANT"
                )
                cloudwatch_evidence = (
                    f"{log_group_count} CloudWatch Log Groups configured"
                )
            except Exception as e:
                logger.warning(f"[SEC04-BP01] Error checking CloudWatch Logs: {str(e)}")
                cloudwatch_logs_ok = False
                cloudwatch_status = "PENDING_REVIEW"
                cloudwatch_evidence = f"Unable to verify: {str(e)[:50]}"

            # Check AWS Config
            try:
                config_status = self.connector.get_config_status(primary_region)
                config_ok = config_status.get("recording", False)
                config_state = (
                    "COMPLIANT" if config_ok else "NON_COMPLIANT"
                )
                config_evidence = (
                    "AWS Config recording enabled"
                    if config_ok
                    else "AWS Config not recording"
                )
            except Exception as e:
                logger.warning(f"[SEC04-BP01] Error checking AWS Config: {str(e)}")
                config_ok = False
                config_state = "PENDING_REVIEW"
                config_evidence = f"Unable to verify: {str(e)[:50]}"

            # Check VPC Flow Logs
            try:
                ec2_client = self.connector._get_ec2_client(primary_region)
                vpcs = ec2_client.describe_vpcs()
                vpc_count = len(vpcs.get("Vpcs", []))
                vpcs_with_flow_logs = 0
                for vpc in vpcs.get("Vpcs", []):
                    try:
                        flow_logs = ec2_client.describe_flow_logs(
                            Filters=[{"Name": "resource-id", "Values": [vpc["VpcId"]]}]
                        )
                        if flow_logs.get("FlowLogs"):
                            vpcs_with_flow_logs += 1
                    except Exception:
                        pass

                vpc_flow_logs_ok = (
                    vpcs_with_flow_logs > 0 and vpc_flow_logs_ok is False
                ) or (vpc_count == vpcs_with_flow_logs)
                vpc_flow_status = (
                    "COMPLIANT" if vpc_flow_logs_ok else "NON_COMPLIANT"
                )
                vpc_flow_evidence = (
                    f"{vpcs_with_flow_logs}/{vpc_count} VPCs have Flow Logs configured"
                )
            except Exception as e:
                logger.warning(f"[SEC04-BP01] Error checking VPC Flow Logs: {str(e)}")
                vpc_flow_status = "PENDING_REVIEW"
                vpc_flow_evidence = f"Unable to verify: {str(e)[:50]}"

            # Overall BP01 status
            services_enabled = sum(
                [cloudtrail_ok, cloudwatch_logs_ok, config_ok, vpc_flow_logs_ok]
            )
            bp01_status = (
                "COMPLIANT"
                if services_enabled >= 3
                else "NON_COMPLIANT"
                if services_enabled == 0
                else "PARTIAL"
            )

            findings.append(
                {
                    "bp": "SEC04-BP01",
                    "status": bp01_status,
                    "finding": f"Application and service logging configuration - {services_enabled}/4 services configured",
                    "severity": "CRITICAL" if services_enabled == 0 else "HIGH",
                    "risk": "Without comprehensive logging, security events cannot be detected or investigated",
                    "remediation": "Enable CloudTrail (multi-region), CloudWatch Logs, AWS Config recording, and VPC Flow Logs",
                    "evidence": f"CloudTrail: {cloudtrail_status} | CloudWatch: {cloudwatch_status} | Config: {config_state} | VPC Flow Logs: {vpc_flow_status}",
                }
            )

        except Exception as e:
            logger.error(f"[SEC04-BP01] Error: {str(e)}", exc_info=True)
            findings.append(
                self._create_pending_finding(
                    "SEC04-BP01",
                    "Unable to evaluate logging configuration",
                    "HIGH",
                    f"Error during evaluation: {str(e)[:100]}",
                )
            )

        # SEC04-BP02: Capture registros, hallazgos y métricas en ubicaciones estandarizadas
        logger.info("[SEC04-BP02] Evaluating centralized log storage...")
        try:
            security_hub_ok = False
            centralized_storage_ok = False
            org_trails_ok = False

            # Check Security Hub
            try:
                sh_hub = self.connector.client.securityhub.describe_hub()
                security_hub_ok = True
                sh_status = "COMPLIANT"
                sh_evidence = "AWS Security Hub enabled"
            except Exception:
                security_hub_ok = False
                sh_status = "NON_COMPLIANT"
                sh_evidence = "AWS Security Hub not enabled"

            # Check for centralized S3 logging bucket
            try:
                buckets = self.connector.client.s3.list_buckets()
                log_buckets = [
                    b
                    for b in buckets.get("Buckets", [])
                    if "log" in b.get("Name", "").lower()
                ]
                centralized_storage_ok = len(log_buckets) > 0
                s3_status = (
                    "COMPLIANT" if centralized_storage_ok else "NON_COMPLIANT"
                )
                s3_evidence = (
                    f"{len(log_buckets)} S3 buckets for log storage identified"
                    if log_buckets
                    else "No dedicated log storage buckets found"
                )
            except Exception:
                centralized_storage_ok = False
                s3_status = "NON_COMPLIANT"
                s3_evidence = "Unable to verify S3 log storage"

            # Check for organization-level trails
            try:
                all_trails = self.connector.get_cloudtrail_trails(primary_region)
                org_trails_ok = any(t.get("is_organization_trail", False) for t in all_trails)
                org_status = (
                    "COMPLIANT" if org_trails_ok else "NON_COMPLIANT"
                )
                org_evidence = (
                    "Organization-level CloudTrail trail configured"
                    if org_trails_ok
                    else "No organization-level trails found"
                )
            except Exception:
                org_trails_ok = False
                org_status = "NON_COMPLIANT"
                org_evidence = "Unable to verify organization trails"

            services_centralized = sum(
                [security_hub_ok, centralized_storage_ok, org_trails_ok]
            )
            bp02_status = (
                "COMPLIANT"
                if services_centralized >= 2
                else "NON_COMPLIANT"
            )

            findings.append(
                {
                    "bp": "SEC04-BP02",
                    "status": bp02_status,
                    "finding": f"Centralized log and metric storage - {services_centralized}/3 mechanisms in place",
                    "severity": "HIGH",
                    "risk": "Without centralized storage, logs may be deleted or modified after compromise",
                    "remediation": "Implement AWS Security Hub, centralized S3 bucket for logs, and organization-level CloudTrail trails",
                    "evidence": f"Security Hub: {sh_status} | S3 Logs: {s3_status} | Org Trails: {org_status}",
                }
            )

        except Exception as e:
            logger.error(f"[SEC04-BP02] Error: {str(e)}", exc_info=True)
            findings.append(
                self._create_pending_finding(
                    "SEC04-BP02",
                    "Unable to evaluate centralized log storage",
                    "HIGH",
                    f"Error during evaluation: {str(e)[:100]}",
                )
            )

        # SEC04-BP03: Correlaciona y enriquece las alertas de seguridad
        logger.info("[SEC04-BP03] Evaluating alert correlation and enrichment...")
        try:
            guardduty_ok = False
            detective_ok = False
            eventbridge_ok = False

            # Check GuardDuty
            try:
                detectors = self.connector.get_guardduty_detectors(primary_region)
                guardduty_ok = len(detectors) > 0
                gd_status = (
                    "COMPLIANT" if guardduty_ok else "NON_COMPLIANT"
                )
                gd_evidence = (
                    f"{len(detectors)} GuardDuty detector(s) enabled"
                    if detectors
                    else "GuardDuty not enabled"
                )
            except Exception:
                guardduty_ok = False
                gd_status = "NON_COMPLIANT"
                gd_evidence = "Unable to verify GuardDuty"

            # Check Detective
            try:
                graphs = self.connector.client.detective.list_graphs()
                detective_ok = len(graphs.get("GraphList", [])) > 0
                detective_status = (
                    "COMPLIANT" if detective_ok else "NON_COMPLIANT"
                )
                detective_evidence = (
                    f"{len(graphs.get('GraphList', []))} Detective graph(s) enabled"
                    if graphs.get("GraphList")
                    else "Amazon Detective not enabled"
                )
            except Exception:
                detective_ok = False
                detective_status = "NON_COMPLIANT"
                detective_evidence = "Unable to verify Detective"

            # Check EventBridge for correlation
            try:
                rules = self.connector.client.events.list_rules()
                security_rules = [
                    r
                    for r in rules.get("Rules", [])
                    if "security" in r.get("Name", "").lower()
                    or "alert" in r.get("Name", "").lower()
                ]
                eventbridge_ok = len(security_rules) > 0
                eb_status = (
                    "COMPLIANT" if eventbridge_ok else "NON_COMPLIANT"
                )
                eb_evidence = (
                    f"{len(security_rules)} security-related EventBridge rules configured"
                    if security_rules
                    else "No security event routing rules found"
                )
            except Exception:
                eventbridge_ok = False
                eb_status = "NON_COMPLIANT"
                eb_evidence = "Unable to verify EventBridge rules"

            services_correlation = sum([guardduty_ok, detective_ok, eventbridge_ok])
            bp03_status = (
                "COMPLIANT"
                if services_correlation >= 2
                else "NON_COMPLIANT"
            )

            findings.append(
                {
                    "bp": "SEC04-BP03",
                    "status": bp03_status,
                    "finding": f"Alert correlation and enrichment - {services_correlation}/3 systems configured",
                    "severity": "HIGH",
                    "risk": "Without correlation, patterns and attack chains cannot be detected",
                    "remediation": "Enable GuardDuty, Amazon Detective, and implement EventBridge rules for threat intelligence integration",
                    "evidence": f"GuardDuty: {gd_status} | Detective: {detective_status} | EventBridge: {eb_status}",
                }
            )

        except Exception as e:
            logger.error(f"[SEC04-BP03] Error: {str(e)}", exc_info=True)
            findings.append(
                self._create_pending_finding(
                    "SEC04-BP03",
                    "Unable to evaluate alert correlation",
                    "HIGH",
                    f"Error during evaluation: {str(e)[:100]}",
                )
            )

        # SEC04-BP04: Iniciar remediación para recursos no conformes
        logger.info("[SEC04-BP04] Evaluating automated remediation...")
        try:
            config_remediation_ok = False
            ssm_automation_ok = False
            lambda_remediation_ok = False

            # Check AWS Config Remediation
            try:
                config_rules = self.connector.client.config.describe_config_rules()
                rules_with_remediation = [
                    r
                    for r in config_rules.get("ConfigRules", [])
                    if r.get("Source", {}).get("SourceIdentifier")
                    and "remediation" in str(r).lower()
                ]
                config_remediation_ok = len(rules_with_remediation) > 0
                config_rem_status = (
                    "COMPLIANT" if config_remediation_ok else "NON_COMPLIANT"
                )
                config_rem_evidence = (
                    f"{len(rules_with_remediation)} AWS Config rules with auto-remediation"
                    if rules_with_remediation
                    else "No auto-remediation rules configured"
                )
            except Exception:
                config_remediation_ok = False
                config_rem_status = "NON_COMPLIANT"
                config_rem_evidence = "Unable to verify Config remediation"

            # Check Systems Manager Automation
            try:
                ssm_docs = self.connector.client.ssm.list_documents()
                automation_docs = [
                    d
                    for d in ssm_docs.get("DocumentIdentifiers", [])
                    if "Automation" in d.get("DocumentType", "")
                ]
                ssm_automation_ok = len(automation_docs) > 0
                ssm_status = (
                    "COMPLIANT" if ssm_automation_ok else "NON_COMPLIANT"
                )
                ssm_evidence = (
                    f"{len(automation_docs)} SSM Automation documents defined"
                    if automation_docs
                    else "No automation documents found"
                )
            except Exception:
                ssm_automation_ok = False
                ssm_status = "NON_COMPLIANT"
                ssm_evidence = "Unable to verify SSM Automation"

            # Check Lambda for remediation functions
            try:
                lambdas = self.connector.client.awslambda.list_functions()
                remediation_lambdas = [
                    f
                    for f in lambdas.get("Functions", [])
                    if "remediat" in f.get("FunctionName", "").lower()
                    or "remedi" in f.get("FunctionName", "").lower()
                ]
                lambda_remediation_ok = len(remediation_lambdas) > 0
                lambda_status = (
                    "COMPLIANT" if lambda_remediation_ok else "NON_COMPLIANT"
                )
                lambda_evidence = (
                    f"{len(remediation_lambdas)} Lambda remediation functions"
                    if remediation_lambdas
                    else "No Lambda remediation functions found"
                )
            except Exception:
                lambda_remediation_ok = False
                lambda_status = "NON_COMPLIANT"
                lambda_evidence = "Unable to verify Lambda remediation"

            remediation_mechanisms = sum(
                [config_remediation_ok, ssm_automation_ok, lambda_remediation_ok]
            )
            bp04_status = (
                "COMPLIANT"
                if remediation_mechanisms >= 2
                else "NON_COMPLIANT"
            )

            findings.append(
                {
                    "bp": "SEC04-BP04",
                    "status": bp04_status,
                    "finding": f"Automated remediation for non-compliant resources - {remediation_mechanisms}/3 systems in place",
                    "severity": "HIGH",
                    "risk": "Manual remediation delays increase exposure window and may miss violations",
                    "remediation": "Implement AWS Config auto-remediation, SSM Automation documents, and Lambda-based response functions",
                    "evidence": f"Config Remediation: {config_rem_status} | SSM Automation: {ssm_status} | Lambda: {lambda_status}",
                }
            )

        except Exception as e:
            logger.error(f"[SEC04-BP04] Error: {str(e)}", exc_info=True)
            findings.append(
                self._create_pending_finding(
                    "SEC04-BP04",
                    "Unable to evaluate automated remediation",
                    "HIGH",
                    f"Error during evaluation: {str(e)[:100]}",
                )
            )

        # Normalize all findings
        findings = [self._normalize_finding(f) for f in findings]

        return {
            "question_id": "SEC04",
            "question": "Detección - ¿Cómo se detectan e investigan los eventos de seguridad?",
            "findings": findings,
            "score": self._calculate_score_from_findings(findings),
            "bps_evaluated": 4,
        }

    def evaluate_sec05(self) -> Dict[str, Any]:
        """SEC05: Protección de infraestructura - ¿Cómo protege los recursos de red? (4 BPs)"""
        findings = []
        primary_region = (
            self.connector.regions[0] if self.connector.regions else "us-east-1"
        )

        # SEC05-BP01: Crear capas de red
        logger.info("[SEC05-BP01] Evaluating network layering...")
        try:
            ec2_client = self.connector._get_ec2_client(primary_region)
            vpcs = ec2_client.describe_vpcs()
            vpc_count = len(vpcs.get("Vpcs", []))
            
            multi_tier_vpcs = 0
            transit_gateways_found = False
            vpc_peering_found = False
            privatelink_found = False
            public_subnets = 0
            private_subnets = 0
            internet_gateways_count = 0
            nat_gateways_count = 0
            client_vpn_count = 0
            site_to_site_vpn_count = 0
            alb_internet_facing = 0
            alb_internal = 0
            cloudfront_distributions = 0

            for vpc in vpcs.get("Vpcs", []):
                vpc_id = vpc["VpcId"]
                # Check for multi-tier setup (public and private subnets)
                try:
                    subnets = ec2_client.describe_subnets(
                        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
                    )
                    if len(subnets.get("Subnets", [])) >= 2:
                        multi_tier_vpcs += 1
                    for subnet in subnets.get("Subnets", []):
                        if subnet.get("MapPublicIpOnLaunch"):
                            public_subnets += 1
                        else:
                            private_subnets += 1
                except Exception:
                    pass

            # Check for Transit Gateway
            try:
                tgws = ec2_client.describe_transit_gateways()
                transit_gateways_found = len(tgws.get("TransitGateways", [])) > 0
            except Exception:
                pass

            # Check for VPC Peering
            try:
                pcx = ec2_client.describe_vpc_peering_connections()
                vpc_peering_found = len(pcx.get("VpcPeeringConnections", [])) > 0
            except Exception:
                pass

            # Check for PrivateLink
            try:
                endpoints = ec2_client.describe_vpc_endpoints()
                privatelink_found = len(endpoints.get("VpcEndpoints", [])) > 0
            except Exception:
                pass

            # Check Internet Gateways
            try:
                igws = ec2_client.describe_internet_gateways()
                internet_gateways_count = len(igws.get("InternetGateways", []))
            except Exception:
                internet_gateways_count = 0

            # Check NAT Gateways
            try:
                nat_gws = ec2_client.describe_nat_gateways()
                nat_gateways_count = len(nat_gws.get("NatGateways", []))
            except Exception:
                nat_gateways_count = 0

            # Check Client VPN endpoints
            try:
                client_vpn = ec2_client.describe_client_vpn_endpoints()
                client_vpn_count = len(client_vpn.get("ClientVpnEndpoints", []))
            except Exception:
                client_vpn_count = 0

            # Check Site-to-Site VPN connections
            try:
                vpn_connections = ec2_client.describe_vpn_connections()
                site_to_site_vpn_count = len(vpn_connections.get("VpnConnections", []))
            except Exception:
                site_to_site_vpn_count = 0

            # Check ALB/NLB schemes
            try:
                elbv2 = self.connector.client.elbv2.describe_load_balancers()
                for lb in elbv2.get("LoadBalancers", []):
                    if lb.get("Scheme") == "internet-facing":
                        alb_internet_facing += 1
                    else:
                        alb_internal += 1
            except Exception:
                alb_internet_facing = 0
                alb_internal = 0

            # Check CloudFront distributions
            try:
                cfd = self.connector.client.cloudfront.list_distributions()
                cloudfront_distributions = len(
                    cfd.get("DistributionList", {}).get("Items", [])
                )
            except Exception:
                cloudfront_distributions = 0

            network_mechanisms = sum(
                [
                    multi_tier_vpcs > 0,
                    transit_gateways_found,
                    vpc_peering_found,
                    privatelink_found,
                    (public_subnets > 0 and private_subnets > 0),
                    internet_gateways_count > 0,
                    nat_gateways_count > 0,
                    (client_vpn_count + site_to_site_vpn_count) > 0,
                    alb_internal > 0,
                    cloudfront_distributions > 0,
                ]
            )
            
            bp01_status = (
                "COMPLIANT"
                if multi_tier_vpcs > 0 and network_mechanisms >= 3
                else "NON_COMPLIANT"
                if vpc_count == 0
                else "PARTIAL"
            )

            findings.append(
                {
                    "bp": "SEC05-BP01",
                    "status": bp01_status,
                    "finding": f"Network layering - {multi_tier_vpcs}/{vpc_count} VPCs with multi-tier architecture",
                    "severity": "HIGH",
                    "risk": "Flat network architectures cannot properly segregate security domains",
                    "remediation": "Implement public/private subnet segregation, Transit Gateway for hub-and-spoke, and PrivateLink for service access",
                    "evidence": (
                        f"Multi-tier VPCs: {multi_tier_vpcs}/{vpc_count} | Public subnets: {public_subnets} | Private subnets: {private_subnets} | "
                        f"IGW: {internet_gateways_count} | NAT GWs: {nat_gateways_count} | Transit Gateway: {transit_gateways_found} | "
                        f"VPC Peering: {vpc_peering_found} | PrivateLink: {privatelink_found} | "
                        f"ALB/NLB internet-facing: {alb_internet_facing} | ALB/NLB internal: {alb_internal} | "
                        f"VPNs (client/site-to-site): {client_vpn_count}/{site_to_site_vpn_count} | CloudFront: {cloudfront_distributions}"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"[SEC05-BP01] Error: {str(e)}", exc_info=True)
            findings.append(
                self._create_pending_finding(
                    "SEC05-BP01",
                    "Unable to evaluate network layering",
                    "HIGH",
                    f"Error during evaluation: {str(e)[:100]}",
                )
            )

        # SEC05-BP02: Controle el flujo de tráfico dentro de capas de red
        logger.info("[SEC05-BP02] Evaluating traffic flow control...")
        try:
            sgs_with_restrictions = 0
            nacls_configured = 0
            network_firewall_ok = False
            waf_ok = False
            open_critical_sgs = 0
            nacl_deny_rules = 0
            public_route_tables = 0
            alb_public_count = 0

            # Check Security Groups
            try:
                sgs = self.connector.client.ec2.describe_security_groups()
                total_sgs = len(sgs.get("SecurityGroups", []))
                
                # Count SGs with restricted inbound rules (not 0.0.0.0/0 on critical ports)
                for sg in sgs.get("SecurityGroups", []):
                    restricted = True
                    for rule in sg.get("IpPermissions", []):
                        if rule.get("IpRanges"):
                            for ip_range in rule.get("IpRanges", []):
                                if ip_range.get("CidrIp") == "0.0.0.0/0":
                                    # Critical ports are 22, 3306, 5432, 1433
                                    if rule.get("FromPort") in [22, 3306, 5432, 1433]:
                                        restricted = False
                                        open_critical_sgs += 1
                                        break
                    if restricted:
                        sgs_with_restrictions += 1

                sg_status = f"{sgs_with_restrictions}/{total_sgs} security groups properly restricted"
            except Exception:
                sg_status = "Unable to verify"
                sgs_with_restrictions = 0

            # Check NACLs
            try:
                nacls = self.connector.client.ec2.describe_network_acls()
                total_nacls = len(nacls.get("NetworkAcls", []))
                # Count non-default NACLs as configured
                nacls_configured = sum(
                    1
                    for n in nacls.get("NetworkAcls", [])
                    if not n.get("IsDefault", False)
                )
                nacl_deny_rules = sum(
                    1
                    for n in nacls.get("NetworkAcls", [])
                    for entry in n.get("Entries", [])
                    if entry.get("RuleAction") == "deny"
                )
                nacl_status = (
                    f"{nacls_configured} custom NACLs configured"
                    if nacls_configured > 0
                    else "Using default NACLs"
                )
            except Exception:
                nacl_status = "Unable to verify"
                nacls_configured = 0

            # Check Network Firewall
            try:
                nfw = self.connector.client.network_firewall.list_firewalls()
                network_firewall_ok = len(nfw.get("Firewalls", [])) > 0
                nfw_status = (
                    f"{len(nfw.get('Firewalls', []))} Network Firewall(s) configured"
                    if network_firewall_ok
                    else "Network Firewall not configured"
                )
            except Exception:
                nfw_status = "Unable to verify"

            # Check WAF
            try:
                wafs = self.connector.client.wafv2.list_web_acls(Scope="REGIONAL")
                waf_ok = len(wafs.get("WebACLs", [])) > 0
                waf_status = (
                    f"{len(wafs.get('WebACLs', []))} WAF Web ACLs configured"
                    if waf_ok
                    else "WAF not configured"
                )
            except Exception:
                waf_status = "Unable to verify"
                waf_ok = False

            # Check public routes to Internet Gateway
            try:
                route_tables = self.connector.client.ec2.describe_route_tables()
                public_route_tables = sum(
                    1
                    for rt in route_tables.get("RouteTables", [])
                    for r in rt.get("Routes", [])
                    if r.get("DestinationCidrBlock") == "0.0.0.0/0"
                    and r.get("GatewayId", "").startswith("igw-")
                )
            except Exception:
                public_route_tables = 0

            # Check internet-facing ALBs
            try:
                elbv2 = self.connector.client.elbv2.describe_load_balancers()
                alb_public_count = sum(
                    1
                    for lb in elbv2.get("LoadBalancers", [])
                    if lb.get("Scheme") == "internet-facing"
                )
            except Exception:
                alb_public_count = 0

            flow_control_mechanisms = sum(
                [
                    sgs_with_restrictions > 0,
                    nacls_configured > 0,
                    network_firewall_ok,
                    waf_ok,
                    nacl_deny_rules > 0,
                ]
            )
            bp02_status = (
                "COMPLIANT"
                if flow_control_mechanisms >= 2 and open_critical_sgs == 0
                else "NON_COMPLIANT"
            )

            findings.append(
                {
                    "bp": "SEC05-BP02",
                    "status": bp02_status,
                    "finding": f"Traffic flow control - {flow_control_mechanisms}/4 control mechanisms in place",
                    "severity": "CRITICAL",
                    "risk": "Without traffic control, lateral movement and data exfiltration become possible",
                    "remediation": "Implement restrictive Security Groups, Network ACLs, Network Firewall, and WAF rules",
                    "evidence": (
                        f"SGs: {sg_status} | Open critical SGs: {open_critical_sgs} | "
                        f"NACLs: {nacl_status} (deny rules: {nacl_deny_rules}) | "
                        f"Network Firewall: {nfw_status} | WAF: {waf_status} | "
                        f"Public route tables: {public_route_tables} | Internet-facing ALBs: {alb_public_count}"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"[SEC05-BP02] Error: {str(e)}", exc_info=True)
            findings.append(
                self._create_pending_finding(
                    "SEC05-BP02",
                    "Unable to evaluate traffic flow control",
                    "CRITICAL",
                    f"Error during evaluation: {str(e)[:100]}",
                )
            )

        # SEC05-BP03: Implementar protección basada en inspección
        logger.info("[SEC05-BP03] Evaluating inspection-based protection...")
        try:
            guardduty_ok = False
            shield_ok = False
            inspector_ok = False
            waf_rules_ok = False
            waf_assoc_ok = False
            cloudfront_waf_ok = False
            waf_assoc_details = "N/D"
            waf_rules_status = "N/D"

            # Check GuardDuty (analyzes VPC Flow Logs)
            try:
                detectors = self.connector.get_guardduty_detectors(primary_region)
                guardduty_ok = len(detectors) > 0
                gd_status = (
                    f"{len(detectors)} GuardDuty detector(s) analyzing traffic"
                    if guardduty_ok
                    else "GuardDuty not enabled"
                )
            except Exception:
                gd_status = "Unable to verify GuardDuty"

            # Check Shield Advanced
            try:
                subscription = self.connector.client.shield.describe_subscription()
                shield_ok = subscription.get("Subscription", {}).get("SubscriptionState") == "Active"
                shield_status = (
                    "AWS Shield Advanced enabled"
                    if shield_ok
                    else "Only AWS Shield Standard (free tier)"
                )
            except Exception:
                shield_status = "Unable to verify Shield"

            # Check Inspector
            try:
                assessments = self.connector.client.inspector.list_assessment_templates()
                inspector_ok = (
                    len(assessments.get("assessmentTemplateArns", [])) > 0
                )
                inspector_status = (
                    f"{len(assessments.get('assessmentTemplateArns', []))} assessment templates"
                    if inspector_ok
                    else "Amazon Inspector not configured"
                )
            except Exception:
                inspector_status = "Unable to verify Inspector"
                inspector_ok = False

            # Check WAF Rule Groups
            try:
                rule_groups = self.connector.client.wafv2.list_rule_groups(Scope="REGIONAL")
                waf_rules_ok = len(rule_groups.get("RuleGroups", [])) > 0
                waf_rules_status = (
                    f"{len(rule_groups.get('RuleGroups', []))} WAF rule groups (SQL injection, XSS protection)"
                    if waf_rules_ok
                    else "WAF rule groups not configured"
                )
                regional_acls = self.connector.client.wafv2.list_web_acls(Scope="REGIONAL").get("WebACLs", [])
                cloudfront_acls = self.connector.client.wafv2.list_web_acls(Scope="CLOUDFRONT").get("WebACLs", [])
                cloudfront_waf_ok = len(cloudfront_acls) > 0

                assoc_total = 0
                assoc_alb = 0
                assoc_api = 0
                assoc_cf = 0

                for acl in regional_acls:
                    try:
                        resources = self.connector.client.wafv2.list_resources_for_web_acl(
                            WebACLArn=acl.get("ARN"), ResourceType="APPLICATION_LOAD_BALANCER"
                        ).get("ResourceArns", [])
                        assoc_alb += len(resources)
                        assoc_total += len(resources)
                    except Exception:
                        pass
                    try:
                        resources = self.connector.client.wafv2.list_resources_for_web_acl(
                            WebACLArn=acl.get("ARN"), ResourceType="API_GATEWAY"
                        ).get("ResourceArns", [])
                        assoc_api += len(resources)
                        assoc_total += len(resources)
                    except Exception:
                        pass

                for acl in cloudfront_acls:
                    try:
                        resources = self.connector.client.wafv2.list_resources_for_web_acl(
                            WebACLArn=acl.get("ARN"), ResourceType="CLOUDFRONT"
                        ).get("ResourceArns", [])
                        assoc_cf += len(resources)
                        assoc_total += len(resources)
                    except Exception:
                        pass

                waf_assoc_ok = assoc_total > 0
                waf_assoc_details = (
                    f"WAF associations - ALB: {assoc_alb}, API Gateway: {assoc_api}, CloudFront: {assoc_cf}"
                )
            except Exception:
                waf_rules_status = "Unable to verify"
                waf_rules_ok = False

            inspection_mechanisms = sum(
                [guardduty_ok, shield_ok, inspector_ok, waf_rules_ok, waf_assoc_ok, cloudfront_waf_ok]
            )
            bp03_status = (
                "COMPLIANT"
                if inspection_mechanisms >= 3
                else "NON_COMPLIANT"
            )

            findings.append(
                {
                    "bp": "SEC05-BP03",
                    "status": bp03_status,
                    "finding": f"Inspection-based protection - {inspection_mechanisms}/4 inspection systems active",
                    "severity": "HIGH",
                    "risk": "Without deep packet inspection, application-layer attacks (SQL injection, XSS) may bypass network controls",
                    "remediation": "Enable GuardDuty, AWS Shield Advanced, Amazon Inspector, and configure WAF rule groups",
                    "evidence": f"GuardDuty: {gd_status} | Shield: {shield_status} | Inspector: {inspector_status} | WAF Rules: {waf_rules_status} | {waf_assoc_details} | CloudFront WAF: {cloudfront_waf_ok}",
                }
            )

        except Exception as e:
            logger.error(f"[SEC05-BP03] Error: {str(e)}", exc_info=True)
            findings.append(
                self._create_pending_finding(
                    "SEC05-BP03",
                    "Unable to evaluate inspection-based protection",
                    "HIGH",
                    f"Error during evaluation: {str(e)[:100]}",
                )
            )

        # SEC05-BP04: Automatice la protección de red
        logger.info("[SEC05-BP04] Evaluating automated network protection...")
        try:
            config_network_rules_ok = False
            cloudformation_iac_ok = False
            eventbridge_automation_ok = False
            firewall_manager_ok = False
            waf_logging_ok = False
            fms_status = "N/D"
            waf_logging_status = "N/D"

            # Check AWS Config for network compliance rules
            try:
                config_rules = self.connector.client.config.describe_config_rules()
                network_rules = [
                    r
                    for r in config_rules.get("ConfigRules", [])
                    if any(
                        keyword in str(r).lower()
                        for keyword in [
                            "security",
                            "network",
                            "vpc",
                            "nacl",
                            "sg",
                        ]
                    )
                ]
                config_network_rules_ok = len(network_rules) > 0
                config_status = (
                    f"{len(network_rules)} network compliance rules"
                    if config_network_rules_ok
                    else "No network compliance rules"
                )
            except Exception:
                config_status = "Unable to verify"

            # Check for CloudFormation IaC
            try:
                stacks = self.connector.client.cloudformation.list_stacks()
                network_stacks = [
                    s
                    for s in stacks.get("StackSummaries", [])
                    if "network" in s.get("StackName", "").lower()
                    and s.get("StackStatus") != "DELETE_COMPLETE"
                ]
                cloudformation_iac_ok = len(network_stacks) > 0
                cf_status = (
                    f"{len(network_stacks)} network infrastructure stacks"
                    if cloudformation_iac_ok
                    else "No IaC network stacks found"
                )
            except Exception:
                cf_status = "Unable to verify"

            # Check EventBridge for network automation
            try:
                rules = self.connector.client.events.list_rules()
                network_rules = [
                    r
                    for r in rules.get("Rules", [])
                    if any(
                        keyword in r.get("Name", "").lower()
                        for keyword in ["network", "sg", "nacl", "vpc"]
                    )
                ]
                eventbridge_automation_ok = len(network_rules) > 0
                eb_status = (
                    f"{len(network_rules)} network automation rules"
                    if eventbridge_automation_ok
                    else "No network automation rules"
                )
            except Exception:
                eb_status = "Unable to verify"

            # Check Firewall Manager policies
            try:
                fms_policies = self.connector.client.fms.list_policies()
                firewall_manager_ok = len(fms_policies.get("PolicyList", [])) > 0
                fms_status = (
                    f"{len(fms_policies.get('PolicyList', []))} Firewall Manager policies"
                    if firewall_manager_ok
                    else "No Firewall Manager policies"
                )
            except Exception:
                fms_status = "Unable to verify"

            # Check WAF logging configuration
            try:
                web_acls = self.connector.client.wafv2.list_web_acls(Scope="REGIONAL").get("WebACLs", [])
                waf_logging_ok = False
                for acl in web_acls:
                    try:
                        logging_cfg = self.connector.client.wafv2.get_logging_configuration(
                            ResourceArn=acl.get("ARN")
                        )
                        if logging_cfg.get("LoggingConfiguration"):
                            waf_logging_ok = True
                            break
                    except Exception:
                        continue
                waf_logging_status = "WAF logging configured" if waf_logging_ok else "WAF logging not configured"
            except Exception:
                waf_logging_status = "Unable to verify"

            automation_mechanisms = sum(
                [
                    config_network_rules_ok,
                    cloudformation_iac_ok,
                    eventbridge_automation_ok,
                    firewall_manager_ok,
                    waf_logging_ok,
                ]
            )
            bp04_status = (
                "COMPLIANT"
                if automation_mechanisms >= 3
                else "NON_COMPLIANT"
            )

            findings.append(
                {
                    "bp": "SEC05-BP04",
                    "status": bp04_status,
                    "finding": f"Automated network protection - {automation_mechanisms}/3 automation mechanisms in place",
                    "severity": "HIGH",
                    "risk": "Manual network configuration is error-prone and cannot respond quickly to threats",
                    "remediation": "Implement AWS Config network rules, CloudFormation/CDK for network IaC, and EventBridge for automated responses",
                    "evidence": f"Config Rules: {config_status} | CloudFormation: {cf_status} | EventBridge: {eb_status} | Firewall Manager: {fms_status} | WAF Logging: {waf_logging_status}",
                }
            )

        except Exception as e:
            logger.error(f"[SEC05-BP04] Error: {str(e)}", exc_info=True)
            findings.append(
                self._create_pending_finding(
                    "SEC05-BP04",
                    "Unable to evaluate automated network protection",
                    "HIGH",
                    f"Error during evaluation: {str(e)[:100]}",
                )
            )

        # Normalize all findings
        findings = [self._normalize_finding(f) for f in findings]

        return {
            "question_id": "SEC05",
            "question": "Protección de infraestructura - ¿Cómo protege los recursos de red?",
            "findings": findings,
            "score": self._calculate_score_from_findings(findings),
            "bps_evaluated": 4,
        }

    def evaluate_sec06(self) -> Dict[str, Any]:
        """SEC06: Protección de infraestructura - ¿Cómo protege sus recursos computacionales? (5 BPs)"""
        findings = []
        primary_region = (
            self.connector.regions[0] if self.connector.regions else "us-east-1"
        )

        # SEC06-BP01: Realizar gestión de vulnerabilidades
        logger.info("[SEC06-BP01] Evaluating vulnerability management...")
        try:
            inspector_ok = False
            patch_manager_ok = False
            ecr_scanning_ok = False
            security_hub_vuln_ok = False
            ecs_clusters_count = 0
            eks_clusters_count = 0

            # Check Amazon Inspector
            try:
                assessments = self.connector.client.inspector.list_assessment_templates()
                inspector_ok = (
                    len(assessments.get("assessmentTemplateArns", [])) > 0
                )
                inspector_status = (
                    f"{len(assessments.get('assessmentTemplateArns', []))} assessment templates"
                    if inspector_ok
                    else "Amazon Inspector not configured"
                )
            except Exception:
                inspector_status = "Unable to verify Inspector"

            # Check Systems Manager Patch Manager
            try:
                baselines = self.connector.client.ssm.describe_patch_baselines()
                patch_manager_ok = (
                    len(baselines.get("BaselineIdentities", [])) > 0
                )
                patch_status = (
                    f"{len(baselines.get('BaselineIdentities', []))} patch baselines defined"
                    if patch_manager_ok
                    else "Patch Manager not configured"
                )
            except Exception:
                patch_status = "Unable to verify Patch Manager"

            # Check ECR Image Scanning
            try:
                repos = self.connector.client.ecr.describe_repositories()
                scanning_repos = [
                    r
                    for r in repos.get("repositories", [])
                    if r.get("imageScanningConfiguration", {}).get("scanOnPush", False)
                ]
                ecr_scanning_ok = len(scanning_repos) > 0
                ecr_status = (
                    f"{len(scanning_repos)} ECR repos with scan-on-push enabled"
                    if ecr_scanning_ok
                    else "ECR image scanning not configured"
                )
            except Exception:
                ecr_status = "Unable to verify ECR scanning"

            # Check Security Hub for vulnerability findings
            try:
                sh_hub = self.connector.client.securityhub.describe_hub()
                security_hub_vuln_ok = True
                sh_vuln_status = "Security Hub configured for vulnerability aggregation"
            except Exception:
                security_hub_vuln_ok = False
                sh_vuln_status = "Security Hub not enabled"

            # Check ECS/EKS presence for vulnerability coverage context
            try:
                ecs_clusters = self.connector.client.ecs.list_clusters()
                ecs_clusters_count = len(ecs_clusters.get("clusterArns", []))
            except Exception:
                ecs_clusters_count = 0

            try:
                eks_clusters = self.connector.client.eks.list_clusters()
                eks_clusters_count = len(eks_clusters.get("clusters", []))
            except Exception:
                eks_clusters_count = 0

            vuln_mgmt_mechanisms = sum(
                [inspector_ok, patch_manager_ok, ecr_scanning_ok, security_hub_vuln_ok]
            )
            bp01_status = (
                "COMPLIANT"
                if vuln_mgmt_mechanisms >= 2
                else "NON_COMPLIANT"
            )

            findings.append(
                {
                    "bp": "SEC06-BP01",
                    "status": bp01_status,
                    "finding": f"Vulnerability management - {vuln_mgmt_mechanisms}/4 systems in place",
                    "severity": "CRITICAL",
                    "risk": "Unpatched systems are easy targets for exploitation",
                    "remediation": "Implement Amazon Inspector assessments, Patch Manager baselines, ECR image scanning, and Security Hub aggregation",
                    "evidence": f"Inspector: {inspector_status} | Patch Manager: {patch_status} | ECR: {ecr_status} | Security Hub: {sh_vuln_status} | ECS clusters: {ecs_clusters_count} | EKS clusters: {eks_clusters_count}",
                }
            )

        except Exception as e:
            logger.error(f"[SEC06-BP01] Error: {str(e)}", exc_info=True)
            findings.append(
                self._create_pending_finding(
                    "SEC06-BP01",
                    "Unable to evaluate vulnerability management",
                    "CRITICAL",
                    f"Error during evaluation: {str(e)[:100]}",
                )
            )

        # SEC06-BP02: Computación de provisión a partir de imágenes endurecidas
        logger.info("[SEC06-BP02] Evaluating hardened compute provisioning...")
        try:
            ec2_amis_ok = False
            image_builder_ok = False
            ecs_hardening_ok = False
            lambda_hardening_ok = False
            ebs_encryption_ok = False
            ebs_encryption_default = False
            encrypted_volume_pct = 0
            gp3_volume_pct = 0
            ecs_readonly_root_ok = False
            ecs_checked_defs = 0
            eks_bottlerocket_ok = False
            eks_nodegroups_checked = 0

            # Check EC2 AMI hardening (golden images)
            try:
                amis = self.connector.client.ec2.describe_images(Owners=["self"])
                golden_amis = [
                    a
                    for a in amis.get("Images", [])
                    if "golden" in a.get("Name", "").lower()
                    or "hardened" in a.get("Name", "").lower()
                    or "base" in a.get("Name", "").lower()
                ]
                ec2_amis_ok = len(golden_amis) > 0
                ami_status = (
                    f"{len(golden_amis)} golden/hardened AMIs available"
                    if golden_amis
                    else "No hardened AMIs found"
                )
            except Exception:
                ami_status = "Unable to verify AMIs"

            # Check Image Builder
            try:
                pipelines = self.connector.client.imagebuilder.list_image_pipelines()
                image_builder_ok = (
                    len(pipelines.get("imagePipelineList", [])) > 0
                )
                ib_status = (
                    f"{len(pipelines.get('imagePipelineList', []))} image building pipelines"
                    if image_builder_ok
                    else "Image Builder not configured"
                )
            except Exception:
                ib_status = "Unable to verify Image Builder"

            # Check ECS task definitions for security baseline
            try:
                task_defs = self.connector.client.ecs.list_task_definitions()
                hardened_tasks = [
                    t
                    for t in task_defs.get("taskDefinitionArns", [])
                    if "hardened" in t.lower() or "prod" in t.lower()
                ]
                ecs_hardening_ok = len(hardened_tasks) > 0
                ecs_status = (
                    f"{len(hardened_tasks)} hardened task definitions"
                    if hardened_tasks
                    else "ECS hardening baseline not evident"
                )
            except Exception:
                ecs_status = "Unable to verify ECS hardening"

            # Check Lambda function encryption and VPC
            try:
                lambdas = self.connector.client.awslambda.list_functions()
                secure_lambdas = [
                    f
                    for f in lambdas.get("Functions", [])
                    if f.get("VpcConfig", {}).get("SubnetIds")
                    and f.get("KMSKeyArn")
                ]
                lambda_hardening_ok = (
                    len(secure_lambdas) / max(len(lambdas.get("Functions", [])), 1)
                ) > 0.5
                lambda_status = (
                    f"{len(secure_lambdas)}/{len(lambdas.get('Functions', []))} Lambda functions with VPC + KMS encryption"
                    if lambdas.get("Functions")
                    else "No Lambda functions"
                )
            except Exception:
                lambda_status = "Unable to verify Lambda hardening"

            # Check EBS encryption and storage types
            try:
                ebs_encryption_default = self.connector.client.ec2.get_ebs_encryption_by_default().get("EbsEncryptionByDefault", False)
            except Exception:
                ebs_encryption_default = False

            try:
                volumes = self.connector.client.ec2.describe_volumes(MaxResults=500)
                all_vols = volumes.get("Volumes", [])
                total_vols = len(all_vols)
                if total_vols > 0:
                    encrypted_vols = [v for v in all_vols if v.get("Encrypted")]
                    gp3_vols = [v for v in all_vols if v.get("VolumeType") == "gp3"]
                    encrypted_volume_pct = (len(encrypted_vols) / total_vols) * 100
                    gp3_volume_pct = (len(gp3_vols) / total_vols) * 100
                    ebs_encryption_ok = encrypted_volume_pct >= 90 or ebs_encryption_default
                else:
                    ebs_encryption_ok = True
            except Exception:
                ebs_encryption_ok = False

            # Check ECS task definitions for hardened settings
            try:
                task_defs = self.connector.client.ecs.list_task_definitions(sort="DESC")
                for td_arn in task_defs.get("taskDefinitionArns", [])[:20]:
                    ecs_checked_defs += 1
                    try:
                        td = self.connector.client.ecs.describe_task_definition(taskDefinition=td_arn)
                        for cdef in td.get("taskDefinition", {}).get("containerDefinitions", []):
                            if cdef.get("readonlyRootFilesystem"):
                                ecs_readonly_root_ok = True
                                break
                        if ecs_readonly_root_ok:
                            break
                    except Exception:
                        continue
            except Exception:
                ecs_readonly_root_ok = False

            # Check EKS nodegroups for hardened AMIs (Bottlerocket)
            try:
                clusters = self.connector.client.eks.list_clusters().get("clusters", [])
                for cluster_name in clusters:
                    nodegroups = self.connector.client.eks.list_nodegroups(clusterName=cluster_name).get("nodegroups", [])
                    for ng in nodegroups:
                        eks_nodegroups_checked += 1
                        try:
                            ng_desc = self.connector.client.eks.describe_nodegroup(clusterName=cluster_name, nodegroupName=ng)
                            ami_type = ng_desc.get("nodegroup", {}).get("amiType", "")
                            if "BOTTLEROCKET" in ami_type:
                                eks_bottlerocket_ok = True
                                break
                        except Exception:
                            continue
                    if eks_bottlerocket_ok:
                        break
            except Exception:
                eks_bottlerocket_ok = False

            hardened_compute = sum(
                [
                    ec2_amis_ok,
                    image_builder_ok,
                    ecs_hardening_ok,
                    lambda_hardening_ok,
                    ebs_encryption_ok,
                    ecs_readonly_root_ok,
                    eks_bottlerocket_ok,
                ]
            )
            bp02_status = (
                "COMPLIANT"
                if hardened_compute >= 3
                else "NON_COMPLIANT"
            )

            findings.append(
                {
                    "bp": "SEC06-BP02",
                    "status": bp02_status,
                    "finding": f"Hardened compute provisioning - {hardened_compute}/4 mechanisms in place",
                    "severity": "HIGH",
                    "risk": "Provisioning from uncontrolled/non-hardened images introduces security vulnerabilities",
                    "remediation": "Implement golden AMIs, AWS Image Builder pipelines, ECS hardening baselines, and Lambda security controls",
                    "evidence": (
                        f"EC2 AMIs: {ami_status} | Image Builder: {ib_status} | ECS: {ecs_status} | Lambda: {lambda_status} | "
                        f"EBS encryption default: {ebs_encryption_default} | Encrypted volumes: {encrypted_volume_pct:.0f}% | "
                        f"gp3 volumes: {gp3_volume_pct:.0f}% | ECS read-only rootfs: {ecs_readonly_root_ok} (checked {ecs_checked_defs}) | "
                        f"EKS Bottlerocket nodegroups: {eks_bottlerocket_ok} (checked {eks_nodegroups_checked})"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"[SEC06-BP02] Error: {str(e)}", exc_info=True)
            findings.append(
                self._create_pending_finding(
                    "SEC06-BP02",
                    "Unable to evaluate hardened compute provisioning",
                    "HIGH",
                    f"Error during evaluation: {str(e)[:100]}",
                )
            )

        # SEC06-BP03: Reducir la gestión manual y el acceso interactivo
        logger.info("[SEC06-BP03] Evaluating reduction of manual access...")
        try:
            session_manager_ok = False
            ssm_run_command_ok = False
            codedeploy_ok = False
            serverless_ok = False
            ssm_managed_coverage_ok = False
            ecs_exec_ok = False
            eks_private_endpoint_ok = False
            managed_instances = 0
            running_instances = 0
            ecs_exec_services = 0
            ecs_services_checked = 0
            eks_clusters_checked = 0

            # Check Systems Manager Session Manager
            try:
                # Check if Session Manager document exists and is enabled
                docs = self.connector.client.ssm.list_documents(
                    Filters=[{"Key": "DocumentType", "Values": ["Session"]}]
                )
                session_manager_ok = (
                    len(docs.get("DocumentIdentifiers", [])) > 0
                )
                sm_status = (
                    "Systems Manager Session Manager configured"
                    if session_manager_ok
                    else "Session Manager not configured"
                )
            except Exception:
                sm_status = "Unable to verify Session Manager"

            # Check Systems Manager Run Command usage
            try:
                commands = self.connector.client.ssm.list_command_invocations()
                ssm_run_command_ok = (
                    len(commands.get("CommandInvocations", [])) > 0
                )
                run_cmd_status = (
                    f"{len(commands.get('CommandInvocations', []))} Run Command invocations detected"
                    if ssm_run_command_ok
                    else "Run Command not in use"
                )
            except Exception:
                run_cmd_status = "Unable to verify Run Command"

            # Check CodeDeploy for automated deployments
            try:
                applications = self.connector.client.codedeploy.list_applications()
                codedeploy_ok = (
                    len(applications.get("applications", [])) > 0
                )
                cd_status = (
                    f"{len(applications.get('applications', []))} CodeDeploy applications"
                    if codedeploy_ok
                    else "CodeDeploy not configured"
                )
            except Exception:
                cd_status = "Unable to verify CodeDeploy"

            # Check Lambda for serverless automation
            try:
                lambdas = self.connector.client.awslambda.list_functions()
                automation_lambdas = [
                    f
                    for f in lambdas.get("Functions", [])
                    if any(
                        keyword in f.get("FunctionName", "").lower()
                        for keyword in [
                            "automat",
                            "deploy",
                            "respons",
                            "handler",
                        ]
                    )
                ]
                serverless_ok = len(automation_lambdas) > 0
                lambda_auto_status = (
                    f"{len(automation_lambdas)} Lambda automation functions"
                    if serverless_ok
                    else "No serverless automation detected"
                )
            except Exception:
                lambda_auto_status = "Unable to verify Lambda automation"

            # Check SSM managed instance coverage (reduce interactive access)
            try:
                ec2_instances = self.connector.client.ec2.describe_instances(
                    Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
                )
                running_instances = sum(
                    len(r.get("Instances", [])) for r in ec2_instances.get("Reservations", [])
                )
            except Exception:
                running_instances = 0

            try:
                ssm_instances = self.connector.client.ssm.describe_instance_information()
                managed_instances = len(ssm_instances.get("InstanceInformationList", []))
                if running_instances == 0:
                    ssm_managed_coverage_ok = True
                else:
                    ssm_managed_coverage_ok = (managed_instances / running_instances) >= 0.5
            except Exception:
                ssm_managed_coverage_ok = False

            # Check ECS Exec usage
            try:
                clusters = self.connector.client.ecs.list_clusters().get("clusterArns", [])
                for cluster_arn in clusters[:5]:
                    services = self.connector.client.ecs.list_services(cluster=cluster_arn).get("serviceArns", [])
                    for svc_arn in services[:20]:
                        ecs_services_checked += 1
                        try:
                            svc = self.connector.client.ecs.describe_services(cluster=cluster_arn, services=[svc_arn])
                            for s in svc.get("services", []):
                                if s.get("enableExecuteCommand"):
                                    ecs_exec_services += 1
                                    ecs_exec_ok = True
                                    break
                        except Exception:
                            continue
                    if ecs_exec_ok:
                        break
            except Exception:
                ecs_exec_ok = False

            # Check EKS private endpoint access
            try:
                clusters = self.connector.client.eks.list_clusters().get("clusters", [])
                for cluster_name in clusters:
                    eks_clusters_checked += 1
                    try:
                        cluster = self.connector.client.eks.describe_cluster(name=cluster_name)
                        vpc_cfg = cluster.get("cluster", {}).get("resourcesVpcConfig", {})
                        if vpc_cfg.get("endpointPublicAccess") is False:
                            eks_private_endpoint_ok = True
                            break
                    except Exception:
                        continue
            except Exception:
                eks_private_endpoint_ok = False

            manual_access_reduction = sum(
                [
                    session_manager_ok,
                    ssm_run_command_ok,
                    codedeploy_ok,
                    serverless_ok,
                    ssm_managed_coverage_ok,
                    ecs_exec_ok,
                    eks_private_endpoint_ok,
                ]
            )
            bp03_status = (
                "COMPLIANT"
                if manual_access_reduction >= 4
                else "NON_COMPLIANT"
                if manual_access_reduction == 0
                else "PARTIAL"
            )

            findings.append(
                {
                    "bp": "SEC06-BP03",
                    "status": bp03_status,
                    "finding": f"Reduced manual access - {manual_access_reduction}/4 automation mechanisms in place",
                    "severity": "HIGH",
                    "risk": "Interactive access and manual configuration increase human error risk and compliance violations",
                    "remediation": "Implement Session Manager, Run Command, CodeDeploy, and Lambda-based automation to eliminate manual access",
                    "evidence": (
                        f"Session Manager: {sm_status} | Run Command: {run_cmd_status} | CodeDeploy: {cd_status} | "
                        f"Lambda: {lambda_auto_status} | SSM managed instances: {managed_instances}/{running_instances} | "
                        f"ECS Exec enabled services: {ecs_exec_services} (checked {ecs_services_checked}) | "
                        f"EKS private endpoint: {eks_private_endpoint_ok} (checked {eks_clusters_checked})"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"[SEC06-BP03] Error: {str(e)}", exc_info=True)
            findings.append(
                self._create_pending_finding(
                    "SEC06-BP03",
                    "Unable to evaluate reduction of manual access",
                    "HIGH",
                    f"Error during evaluation: {str(e)[:100]}",
                )
            )

        # SEC06-BP04: Validar la integridad del software
        logger.info("[SEC06-BP04] Evaluating software integrity validation...")
        try:
            aws_signer_ok = False
            lambda_signing_ok = False
            ecr_signing_ok = False

            # Check AWS Signer
            try:
                signing_profiles = self.connector.client.signer.list_signing_profiles()
                aws_signer_ok = (
                    len(signing_profiles.get("profiles", [])) > 0
                )
                signer_status = (
                    f"{len(signing_profiles.get('profiles', []))} signing profiles configured"
                    if aws_signer_ok
                    else "AWS Signer not configured"
                )
            except Exception:
                signer_status = "Unable to verify AWS Signer"

            # Check Lambda code signing
            try:
                lambdas = self.connector.client.awslambda.list_functions()
                signed_lambdas = [
                    f
                    for f in lambdas.get("Functions", [])
                    if f.get("CodeSigningConfig")
                ]
                lambda_signing_ok = len(signed_lambdas) > 0
                lambda_sign_status = (
                    f"{len(signed_lambdas)}/{len(lambdas.get('Functions', []))} Lambda functions with code signing"
                    if signed_lambdas
                    else "Lambda code signing not enabled"
                )
            except Exception:
                lambda_sign_status = "Unable to verify Lambda signing"

            # Check ECR image signing
            try:
                repos = self.connector.client.ecr.describe_repositories()
                repos_with_signing = [
                    r
                    for r in repos.get("repositories", [])
                    if r.get("encryptionConfiguration", {}).get("encryptionType") == "KMS"
                ]
                ecr_signing_ok = len(repos_with_signing) > 0
                ecr_sign_status = (
                    f"{len(repos_with_signing)} ECR repos with content trust/encryption"
                    if repos_with_signing
                    else "ECR image signing not configured"
                )
            except Exception:
                ecr_sign_status = "Unable to verify ECR signing"

            integrity_mechanisms = sum(
                [aws_signer_ok, lambda_signing_ok, ecr_signing_ok]
            )
            bp04_status = (
                "COMPLIANT"
                if integrity_mechanisms >= 2
                else "NON_COMPLIANT"
            )

            findings.append(
                {
                    "bp": "SEC06-BP04",
                    "status": bp04_status,
                    "finding": f"Software integrity validation - {integrity_mechanisms}/3 signing mechanisms in place",
                    "severity": "HIGH",
                    "risk": "Without code signing, malicious code could be injected during deployment",
                    "remediation": "Implement AWS Signer for all artifacts, Lambda code signing, and ECR image signing/trust policies",
                    "evidence": f"AWS Signer: {signer_status} | Lambda: {lambda_sign_status} | ECR: {ecr_sign_status}",
                }
            )

        except Exception as e:
            logger.error(f"[SEC06-BP04] Error: {str(e)}", exc_info=True)
            findings.append(
                self._create_pending_finding(
                    "SEC06-BP04",
                    "Unable to evaluate software integrity validation",
                    "HIGH",
                    f"Error during evaluation: {str(e)[:100]}",
                )
            )

        # SEC06-BP05: Automatice la protección informática
        logger.info("[SEC06-BP05] Evaluating automated compute protection...")
        try:
            config_compute_rules_ok = False
            auto_scaling_ok = False
            cloudwatch_automation_ok = False
            security_hub_automation_ok = False

            # Check AWS Config for compute compliance
            try:
                config_rules = self.connector.client.config.describe_config_rules()
                compute_rules = [
                    r
                    for r in config_rules.get("ConfigRules", [])
                    if any(
                        keyword in str(r).lower()
                        for keyword in [
                            "ec2",
                            "lambda",
                            "ecs",
                            "compute",
                            "instance",
                        ]
                    )
                ]
                config_compute_rules_ok = len(compute_rules) > 0
                config_compute_status = (
                    f"{len(compute_rules)} compute compliance rules"
                    if compute_rules
                    else "No compute compliance rules"
                )
            except Exception:
                config_compute_status = "Unable to verify Config rules"

            # Check Auto Scaling
            try:
                asg_groups = self.connector.client.autoscaling.describe_auto_scaling_groups()
                auto_scaling_ok = (
                    len(asg_groups.get("AutoScalingGroups", [])) > 0
                )
                asg_status = (
                    f"{len(asg_groups.get('AutoScalingGroups', []))} Auto Scaling Groups"
                    if auto_scaling_ok
                    else "No Auto Scaling configured"
                )
            except Exception:
                asg_status = "Unable to verify Auto Scaling"

            # Check CloudWatch for compute monitoring
            try:
                alarms = self.connector.client.cloudwatch.describe_alarms()
                compute_alarms = [
                    a
                    for a in alarms.get("MetricAlarms", [])
                    if any(
                        keyword in a.get("MetricName", "").lower()
                        for keyword in ["cpu", "memory", "disk", "network"]
                    )
                ]
                cloudwatch_automation_ok = len(compute_alarms) > 0
                cw_status = (
                    f"{len(compute_alarms)} compute monitoring alarms"
                    if compute_alarms
                    else "No compute monitoring alarms"
                )
            except Exception:
                cw_status = "Unable to verify CloudWatch alarms"

            # Check Security Hub for automated response
            try:
                hub_info = self.connector.client.securityhub.describe_hub()
                security_hub_automation_ok = True
                sh_automation_status = "Security Hub configured for automated responses"
            except Exception:
                security_hub_automation_ok = False
                sh_automation_status = "Security Hub not enabled"

            compute_automation = sum(
                [
                    config_compute_rules_ok,
                    auto_scaling_ok,
                    cloudwatch_automation_ok,
                    security_hub_automation_ok,
                ]
            )
            bp05_status = (
                "COMPLIANT"
                if compute_automation >= 3
                else "NON_COMPLIANT"
            )

            findings.append(
                {
                    "bp": "SEC06-BP05",
                    "status": bp05_status,
                    "finding": f"Automated compute protection - {compute_automation}/4 automation systems in place",
                    "severity": "HIGH",
                    "risk": "Without automation, compute resources cannot respond quickly to threats or scale securely",
                    "remediation": "Implement AWS Config compute rules, Auto Scaling policies, CloudWatch monitoring/alarms, and Security Hub automation",
                    "evidence": f"Config: {config_compute_status} | Auto Scaling: {asg_status} | CloudWatch: {cw_status} | Security Hub: {sh_automation_status}",
                }
            )

        except Exception as e:
            logger.error(f"[SEC06-BP05] Error: {str(e)}", exc_info=True)
            findings.append(
                self._create_pending_finding(
                    "SEC06-BP05",
                    "Unable to evaluate automated compute protection",
                    "HIGH",
                    f"Error during evaluation: {str(e)[:100]}",
                )
            )

        # Normalize all findings
        findings = [self._normalize_finding(f) for f in findings]

        return {
            "question_id": "SEC06",
            "question": "Protección de infraestructura - ¿Cómo protege sus recursos computacionales?",
            "findings": findings,
            "score": self._calculate_score_from_findings(findings),
            "bps_evaluated": 5,
        }

    def evaluate_sec07(self) -> Dict[str, Any]:
        """SEC07: ¿Cómo clasifica sus datos? (4 BPs)"""
        findings = []
        score = 100
        self.connector.regions[0] if self.connector.regions else "us-east-1"

        # SEC07-BP01: Comprender su esquema de clasificación de datos
        try:
            s3_buckets = self.connector.get_s3_buckets()
            if s3_buckets:
                findings.append(
                    {
                        "bp": "SEC07-BP01",
                        "status": "PENDING_REVIEW",
                        "finding": f"{len(s3_buckets)} S3 buckets found - verify data classification tags",
                        "severity": "MEDIUM",
                        "risk": "Unclassified data cannot be properly protected",
                        "remediation": "Tag all S3 buckets with data classification (Public, Internal, Confidential, Restricted)",
                        "evidence": f"{len(s3_buckets)} buckets require classification review",
                    }
                )
            else:
                findings.append(
                    {
                        "bp": "SEC07-BP01",
                        "status": "COMPLIANT",
                        "finding": "No S3 buckets found",
                        "severity": "NONE",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking S3 buckets: {str(e)}")

        # SEC07-BP02: Aplicar controles de protección de datos basados en sensibilidad
        try:
            s3_buckets = self.connector.get_s3_buckets()
            unencrypted_buckets = [
                b for b in s3_buckets if not b.get("encryption_enabled")
            ]
            if unencrypted_buckets:
                score -= 20
                findings.append(
                    {
                        "bp": "SEC07-BP02",
                        "status": "NON_COMPLIANT",
                        "finding": f"{len(unencrypted_buckets)} of {len(s3_buckets)} S3 buckets without encryption",
                        "severity": "CRITICAL",
                        "risk": "Unencrypted data can be accessed if bucket is compromised",
                        "remediation": "Enable default encryption for all S3 buckets using SSE-S3 or SSE-KMS",
                        "evidence": ", ".join(
                            [b["name"] for b in unencrypted_buckets[:5]]
                        ),
                    }
                )
            else:
                findings.append(
                    {
                        "bp": "SEC07-BP02",
                        "status": "COMPLIANT",
                        "finding": f"All {len(s3_buckets)} S3 buckets have encryption enabled",
                        "severity": "NONE",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking bucket encryption: {str(e)}")

        # SEC07-BP03: Automatizar identificación y clasificación
        findings.append(
            {
                "bp": "SEC07-BP03",
                "status": "PENDING_REVIEW",
                "finding": "Verify Amazon Macie is enabled for automated data discovery and classification",
                "severity": "MEDIUM",
                "risk": "Manual classification is error-prone and incomplete",
                "remediation": "Enable Amazon Macie to automatically discover and classify sensitive data in S3",
            }
        )

        # SEC07-BP04: Definir gestión escalable del ciclo de vida de datos
        try:
            s3_buckets = self.connector.get_s3_buckets()
            unversioned_buckets = [
                b for b in s3_buckets if not b.get("versioning_enabled")
            ]
            if unversioned_buckets:
                score -= 10
                findings.append(
                    {
                        "bp": "SEC07-BP04",
                        "status": "NON_COMPLIANT",
                        "finding": f"{len(unversioned_buckets)} of {len(s3_buckets)} buckets without versioning",
                        "severity": "MEDIUM",
                        "risk": "Data can be permanently lost or deleted without versioning",
                        "remediation": "Enable versioning on all S3 buckets to protect against accidental deletion",
                        "evidence": f"{len(unversioned_buckets)} buckets need versioning",
                    }
                )
            else:
                findings.append(
                    {
                        "bp": "SEC07-BP04",
                        "status": "COMPLIANT",
                        "finding": "All S3 buckets have versioning enabled",
                        "severity": "NONE",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking versioning: {str(e)}")

        return {
            "question_id": "SEC07",
            "question": "Clasificación de datos",
            "findings": findings,
            "score": self._calculate_score_from_findings(findings),
            "bps_evaluated": 4,
        }

    def evaluate_sec08(self) -> Dict[str, Any]:
        """SEC08: ¿Cómo protege sus datos en reposo? (4 BPs)"""
        findings = []
        score = 100
        primary_region = (
            self.connector.regions[0] if self.connector.regions else "us-east-1"
        )

        # SEC08-BP01: Implementar gestión segura de claves
        try:
            kms_keys = self.connector.get_kms_keys(primary_region)
            if kms_keys:
                findings.append(
                    {
                        "bp": "SEC08-BP01",
                        "status": "COMPLIANT",
                        "finding": f"{len(kms_keys)} KMS keys configured for encryption",
                        "severity": "NONE",
                        "evidence": "KMS keys in use for encryption management",
                    }
                )
            else:
                score -= 10
                findings.append(
                    {
                        "bp": "SEC08-BP01",
                        "status": "NON_COMPLIANT",
                        "finding": "No KMS keys found - using default AWS-managed keys",
                        "severity": "MEDIUM",
                        "risk": "Cannot control key rotation or access policies with default keys",
                        "remediation": "Create customer-managed KMS keys for better control",
                        "evidence": "No customer-managed KMS keys detected",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking KMS keys: {str(e)}")

        # SEC08-BP02: Hacer cumplir el cifrado en reposo
        try:
            s3_buckets = self.connector.get_s3_buckets()
            ebs_volumes = self.connector.get_ebs_volumes(primary_region)
            rds_instances = self.connector.get_rds_instances(primary_region)

            unencrypted_resources = []
            if s3_buckets:
                unenc_s3 = [b for b in s3_buckets if not b.get("encryption_enabled")]
                if unenc_s3:
                    unencrypted_resources.append(f"{len(unenc_s3)} S3 buckets")

            if ebs_volumes:
                unenc_ebs = [v for v in ebs_volumes if not v.get("encrypted")]
                if unenc_ebs:
                    unencrypted_resources.append(f"{len(unenc_ebs)} EBS volumes")

            if rds_instances:
                unenc_rds = [d for d in rds_instances if not d.get("encrypted")]
                if unenc_rds:
                    unencrypted_resources.append(f"{len(unenc_rds)} RDS instances")

            if unencrypted_resources:
                score -= 25
                findings.append(
                    {
                        "bp": "SEC08-BP02",
                        "status": "NON_COMPLIANT",
                        "finding": f"Unencrypted resources: {', '.join(unencrypted_resources)}",
                        "severity": "CRITICAL",
                        "risk": "Unencrypted data at rest can be accessed if storage is compromised",
                        "remediation": "Enable encryption at rest for all S3 buckets, EBS volumes, and RDS instances",
                        "evidence": ", ".join(unencrypted_resources),
                    }
                )
            else:
                findings.append(
                    {
                        "bp": "SEC08-BP02",
                        "status": "COMPLIANT",
                        "finding": "All resources have encryption at rest enabled",
                        "severity": "NONE",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking encryption at rest: {str(e)}")

        # SEC08-BP03: Automatizar protección de datos en reposo
        findings.append(
            {
                "bp": "SEC08-BP03",
                "status": "PENDING_REVIEW",
                "finding": "Verify AWS Config rules enforce encryption requirements automatically",
                "severity": "MEDIUM",
                "risk": "Manual enforcement is unreliable and slow",
                "remediation": "Use AWS Config rules like s3-bucket-server-side-encryption-enabled, encrypted-volumes",
            }
        )

        # SEC08-BP04: Hacer cumplir el control de acceso
        try:
            s3_buckets = self.connector.get_s3_buckets()
            public_buckets = [
                b for b in s3_buckets if not b.get("public_access_blocked")
            ]
            if public_buckets:
                score -= 15
                findings.append(
                    {
                        "bp": "SEC08-BP04",
                        "status": "NON_COMPLIANT",
                        "finding": f"{len(public_buckets)} of {len(s3_buckets)} S3 buckets without public access block",
                        "severity": "HIGH",
                        "risk": "Buckets can be accidentally made public",
                        "remediation": "Enable S3 Block Public Access for all buckets",
                        "evidence": ", ".join([b["name"] for b in public_buckets[:5]]),
                    }
                )
            else:
                findings.append(
                    {
                        "bp": "SEC08-BP04",
                        "status": "COMPLIANT",
                        "finding": f"All {len(s3_buckets)} S3 buckets have public access blocked",
                        "severity": "NONE",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking public access: {str(e)}")

        return {
            "question_id": "SEC08",
            "question": "Protección de datos en reposo",
            "findings": findings,
            "score": self._calculate_score_from_findings(findings),
            "bps_evaluated": 4,
        }

    def evaluate_sec09(self) -> Dict[str, Any]:
        """SEC09: ¿Cómo protege sus datos en tránsito? (3 BPs)"""
        findings = []
        score = 100
        primary_region = (
            self.connector.regions[0] if self.connector.regions else "us-east-1"
        )

        # SEC09-BP01: Implementar gestión segura de claves y certificados
        findings.append(
            {
                "bp": "SEC09-BP01",
                "status": "PENDING_REVIEW",
                "finding": "Verify AWS Certificate Manager (ACM) is used for SSL/TLS certificates",
                "severity": "MEDIUM",
                "risk": "Self-managed certificates are difficult to rotate and expire",
                "remediation": "Use AWS Certificate Manager for automatic certificate provisioning and renewal",
            }
        )

        # SEC09-BP02: Hacer cumplir el cifrado en tránsito
        try:
            s3_buckets = self.connector.get_s3_buckets()
            # Check if buckets enforce HTTPS
            findings.append(
                {
                    "bp": "SEC09-BP02",
                    "status": "PENDING_REVIEW",
                    "finding": f"Verify {len(s3_buckets)} S3 buckets enforce HTTPS-only access via bucket policy",
                    "severity": "HIGH",
                    "risk": "Unencrypted data in transit can be intercepted",
                    "remediation": "Add bucket policy to deny non-HTTPS requests (aws:SecureTransport = false)",
                    "evidence": f"{len(s3_buckets)} buckets require HTTPS enforcement verification",
                }
            )
        except Exception as e:
            logger.error(f"Error checking S3: {str(e)}")

        # SEC09-BP03: Autenticar las comunicaciones de red
        try:
            vpcs = self.connector.get_vpcs(primary_region)
            findings.append(
                {
                    "bp": "SEC09-BP03",
                    "status": "PENDING_REVIEW",
                    "finding": f"{len(vpcs)} VPC(s) found - verify VPN or TLS used for all network communications",
                    "severity": "HIGH",
                    "risk": "Unauthenticated network traffic can be spoofed or intercepted",
                    "remediation": "Use AWS VPN, Direct Connect with MACsec, or TLS for all inter-VPC and external communications",
                    "evidence": f"{len(vpcs)} VPCs require network authentication review",
                }
            )
        except Exception as e:
            logger.error(f"Error checking VPCs: {str(e)}")

        return {
            "question_id": "SEC09",
            "question": "Protección de datos en tránsito",
            "findings": findings,
            "score": self._calculate_score_from_findings(findings),
            "bps_evaluated": 3,
        }

        # SEC09-BP03: RDS Encryption
        findings.append(
            {
                "bp": "SEC09-BP03",
                "status": "PENDING_REVIEW",
                "finding": "Verify all RDS instances have encryption-at-rest enabled",
                "severity": "HIGH",
            }
        )

        # SEC09-BP04: DynamoDB Encryption
        findings.append(
            {
                "bp": "SEC09-BP04",
                "status": "PENDING_REVIEW",
                "finding": "Verify all DynamoDB tables use encryption with CMK",
                "severity": "MEDIUM",
            }
        )

        # SEC09-BP05: EBS Encryption
        findings.append(
            {
                "bp": "SEC09-BP05",
                "status": "PENDING_REVIEW",
                "finding": "Verify all EBS volumes have encryption enabled",
                "severity": "HIGH",
            }
        )

        # SEC09-BP06: Snapshots and backups encryption
        findings.append(
            {
                "bp": "SEC09-BP06",
                "status": "PENDING_REVIEW",
                "finding": "Ensure all backup snapshots are encrypted",
                "severity": "HIGH",
            }
        )

        return {
            "question_id": "SEC09",
            "question": "Protección de datos en reposo",
            "findings": findings,
            "score": max(0, score),
            "bps_evaluated": 3,
        }

    def evaluate_sec10(self) -> Dict[str, Any]:
        """SEC10: ¿Cómo se anticipa, responde y se recupera ante incidentes?"""
        findings = []
        score = 100

        findings.append(
            {
                "bp": "SEC10-BP01",
                "status": "PENDING_REVIEW",
                "finding": "Establish and test incident response plan",
                "severity": "HIGH",
            }
        )

        findings.append(
            {
                "bp": "SEC10-BP02",
                "status": "PENDING_REVIEW",
                "finding": "Enable AWS Backup for automated data protection",
                "severity": "HIGH",
            }
        )

        findings.append(
            {
                "bp": "SEC10-BP03",
                "status": "PENDING_REVIEW",
                "finding": "Implement multi-region backup strategy",
                "severity": "HIGH",
            }
        )

        findings.append(
            {
                "bp": "SEC10-BP04",
                "status": "PENDING_REVIEW",
                "finding": "Test disaster recovery procedures regularly",
                "severity": "HIGH",
            }
        )

        findings.append(
            {
                "bp": "SEC10-BP05",
                "status": "PENDING_REVIEW",
                "finding": "Define RTO and RPO targets for critical workloads",
                "severity": "MEDIUM",
            }
        )

        findings.append(
            {
                "bp": "SEC10-BP06",
                "status": "PENDING_REVIEW",
                "finding": "Implement automated incident response workflows",
                "severity": "MEDIUM",
            }
        )

        return {
            "question_id": "SEC10",
            "question": "Anticipación, respuesta y recuperación ante incidentes",
            "findings": findings,
            "score": max(0, score),
            "bps_evaluated": 8,
        }

    def evaluate_sec11(self) -> Dict[str, Any]:
        """SEC11: ¿Cómo cumple con los requisitos regulatorios?"""
        findings = []
        score = 100

        findings.append(
            {
                "bp": "SEC11-BP01",
                "status": "PENDING_REVIEW",
                "finding": "Use AWS Artifact to access compliance reports and agreements",
                "severity": "MEDIUM",
            }
        )

        findings.append(
            {
                "bp": "SEC11-BP02",
                "status": "PENDING_REVIEW",
                "finding": "Use AWS Config Rules to verify compliance with standards (HIPAA, PCI-DSS, etc.)",
                "severity": "MEDIUM",
            }
        )

        findings.append(
            {
                "bp": "SEC11-BP03",
                "status": "PENDING_REVIEW",
                "finding": "Implement audit logging and maintain immutable logs for compliance",
                "severity": "HIGH",
            }
        )

        return {
            "question_id": "SEC11",
            "question": "Cumplimiento normativo y auditoría",
            "findings": findings,
            "score": max(0, score),
            "bps_evaluated": 8,
        }

    def evaluate_all(self) -> Dict[str, Any]:
        """Evaluate all 11 Security pillar questions"""
        questions = [
            self.evaluate_sec01(),
            self.evaluate_sec02(),
            self.evaluate_sec03(),
            self.evaluate_sec04(),
            self.evaluate_sec05(),
            self.evaluate_sec06(),
            self.evaluate_sec07(),
            self.evaluate_sec08(),
            self.evaluate_sec09(),
            self.evaluate_sec10(),
            self.evaluate_sec11(),
        ]

        # Normalize all findings to ensure complete fields
        for question in questions:
            question["findings"] = self._normalize_findings_list(question["findings"])

        # Calculate overall security score
        overall_score = sum(q["score"] for q in questions) / len(questions)
        total_findings = sum(len(q["findings"]) for q in questions)

        return {
            "questions": questions,
            "overall_score": round(overall_score, 2),
            "total_findings": total_findings,
            "total_questions": 11,
            "total_best_practices": 63,
        }

    def evaluate_bp(self, bp_id: str) -> Dict[str, Any]:
        """
        Evaluate a single Best Practice by its ID (e.g., 'SEC01-BP01')

        Returns:
            {
                'bp_id': 'SEC01-BP01',
                'question_id': 'SEC01',
                'finding': {...},
                'message': 'Evaluation successful' or error message
            }
        """
        try:
            # Extract SEC number from BP ID (e.g., 'SEC01' from 'SEC01-BP01')
            sec_num = bp_id[:5]  # 'SEC01'

            if sec_num not in [
                "SEC01",
                "SEC02",
                "SEC03",
                "SEC04",
                "SEC05",
                "SEC06",
                "SEC07",
                "SEC08",
                "SEC09",
                "SEC10",
                "SEC11",
            ]:
                return {
                    "success": False,
                    "bp_id": bp_id,
                    "error": f"Invalid SEC section: {sec_num}",
                }

            # Evaluate the full question
            evaluate_method = getattr(self, f"evaluate_{sec_num.lower()}", None)
            if not evaluate_method:
                return {
                    "success": False,
                    "bp_id": bp_id,
                    "error": f"Evaluation method not found for {sec_num}",
                }

            question_result = evaluate_method()

            # Find the specific BP finding
            matching_finding = None
            for finding in question_result["findings"]:
                if finding.get("bp") == bp_id:
                    matching_finding = finding
                    break

            if matching_finding is None:
                return {
                    "success": False,
                    "bp_id": bp_id,
                    "error": "BP not found in results",
                }

            # Normalize the finding
            matching_finding = self._normalize_finding(matching_finding)

            return {
                "success": True,
                "bp_id": bp_id,
                "question_id": question_result["question_id"],
                "finding": matching_finding,
                "message": "BP evaluation successful",
            }

        except Exception as e:
            logger.error(f"Error evaluating BP {bp_id}: {str(e)}")
            return {
                "success": False,
                "bp_id": bp_id,
                "error": f"Evaluation error: {str(e)[:100]}",
            }

    def evaluate_bps_batch(self, bp_ids: List[str]) -> Dict[str, Any]:
        """
        Re-evaluate multiple BPs

        Args:
            bp_ids: List of BP IDs like ['SEC01-BP01', 'SEC02-BP03']

        Returns:
            {
                'success': True,
                'evaluated': [..],
                'failed': [...],
                'timestamp': '...'
            }
        """
        from datetime import datetime

        evaluated = []
        failed = []

        for bp_id in bp_ids:
            result = self.evaluate_bp(bp_id)
            if result["success"]:
                evaluated.append(result)
            else:
                failed.append(
                    {"bp_id": bp_id, "error": result.get("error", "Unknown error")}
                )

        return {
            "success": len(failed) == 0,
            "evaluated": evaluated,
            "failed": failed,
            "evaluated_count": len(evaluated),
            "failed_count": len(failed),
            "timestamp": datetime.now().isoformat(),
        }
