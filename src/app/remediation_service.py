"""
Remediation Service for AutoWAR Platform
Generates detailed remediation plans based on evaluation results
"""

from typing import Dict, List, Any
from .models import RemediationPlan, RemediationStep


class RemediationService:
    """Service for remediation planning and tracking"""

    def __init__(
        self, dynamodb_table=None, table_name: str = "autowar-remediation-tracking"
    ):
        self.dynamodb = dynamodb_table.meta.client if dynamodb_table else None
        self.table_name = table_name
        self.table = dynamodb_table

    def generate_bp_remediation(
        self, bp_id: str, current_score: float
    ) -> List[RemediationStep]:
        """Generate remediation steps for a specific best practice"""
        steps = []

        # Get base remediation steps for this BP
        base_steps = self._get_bp_remediation_steps(bp_id)

        # Adjust steps based on current score
        for step in base_steps:
            # Adjust priority based on score
            if current_score < 30:
                step.priority = min(
                    step.priority + 2, 10
                )  # Increase priority for critical issues
            elif current_score < 50:
                step.priority = min(step.priority + 1, 10)

            steps.append(step)

        return steps

    def generate_question_remediation_plan(
        self, question_id: str, bp_results: Dict[str, Any]
    ) -> RemediationPlan:
        """Generate comprehensive remediation plan for a question"""
        all_steps = []
        total_effort = "low"
        total_cost = "low"

        for bp_id, bp_data in bp_results.items():
            if isinstance(bp_data, dict) and "score" in bp_data:
                bp_steps = self.generate_bp_remediation(bp_id, bp_data["score"])
                all_steps.extend(bp_steps)

        # Sort steps by priority
        all_steps.sort(key=lambda x: x.priority, reverse=True)

        # Calculate total effort and cost
        if len(all_steps) > 10:
            total_effort = "high"
            total_cost = "high"
        elif len(all_steps) > 5:
            total_effort = "medium"
            total_cost = "medium"

        # Get prerequisites and success criteria
        prerequisites = self._get_question_prerequisites(question_id)
        success_criteria = self._get_question_success_criteria(question_id)

        return RemediationPlan(
            question_id=question_id,
            total_steps=len(all_steps),
            estimated_effort=total_effort,
            estimated_cost=total_cost,
            steps=all_steps,
            prerequisites=prerequisites,
            success_criteria=success_criteria,
        )

    def _get_bp_remediation_steps(self, bp_id: str) -> List[RemediationStep]:
        """Get remediation steps for a specific BP"""
        remediation_db = {
            "SEC01-BP01": [
                RemediationStep(
                    step_id="SEC01-BP01-1",
                    bp_id="SEC01-BP01",
                    title="Habilitar MFA para usuario root",
                    description="Configure Multi-Factor Authentication (MFA) para el usuario root de la cuenta AWS",
                    effort="low",
                    impact="high",
                    time_estimate="1 hour",
                    cost_estimate="$0",
                    required_skills=["AWS IAM", "MFA Setup"],
                    validation_criteria="MFA habilitado y verificado en la consola AWS",
                    priority=9,
                ),
                RemediationStep(
                    step_id="SEC01-BP01-2",
                    bp_id="SEC01-BP01",
                    title="Eliminar access keys del usuario root",
                    description="Remover cualquier access key asociada al usuario root",
                    effort="low",
                    impact="high",
                    time_estimate="30 minutes",
                    cost_estimate="$0",
                    required_skills=["AWS IAM"],
                    validation_criteria="No access keys activas para usuario root",
                    priority=8,
                ),
            ],
            "SEC01-BP02": [
                RemediationStep(
                    step_id="SEC01-BP02-1",
                    bp_id="SEC01-BP02",
                    title="Crear roles IAM para workloads",
                    description="Crear roles IAM con permisos específicos para cada aplicación o servicio",
                    effort="medium",
                    impact="high",
                    time_estimate="4 hours",
                    cost_estimate="$0",
                    required_skills=["AWS IAM", "Policy Design"],
                    validation_criteria="Roles creados y asignados a recursos EC2/Lambda",
                    priority=7,
                ),
                RemediationStep(
                    step_id="SEC01-BP02-2",
                    bp_id="SEC01-BP02",
                    title="Migrar aplicaciones a usar roles",
                    description="Actualizar código de aplicaciones para usar roles IAM en lugar de access keys",
                    effort="high",
                    impact="high",
                    time_estimate="2-3 days",
                    cost_estimate="$500-2000",
                    required_skills=["AWS SDK", "Application Development"],
                    validation_criteria="Aplicaciones funcionando con roles, access keys removidas",
                    priority=6,
                ),
            ],
            "SEC02-BP01": [
                RemediationStep(
                    step_id="SEC02-BP01-1",
                    bp_id="SEC02-BP01",
                    title="Habilitar AWS CloudTrail",
                    description="Configurar CloudTrail para logging de todas las regiones",
                    effort="low",
                    impact="high",
                    time_estimate="1 hour",
                    cost_estimate="$0-50/month",
                    required_skills=["AWS CloudTrail"],
                    validation_criteria="CloudTrail activo y recolectando logs",
                    priority=9,
                )
            ],
        }

        return remediation_db.get(bp_id, [])

    def _get_question_prerequisites(self, question_id: str) -> List[str]:
        """Get prerequisites for remediating a question"""
        prerequisites = {
            "SEC01": [
                "Acceso administrativo a cuenta AWS",
                "Conocimiento básico de IAM",
                "Backup de configuraciones actuales",
            ],
            "SEC02": [
                "Permisos para configurar CloudTrail",
                "Acceso a CloudWatch",
                "Configuración de SNS topics (opcional)",
            ],
        }
        return prerequisites.get(question_id, ["Acceso administrativo a AWS"])

    def _get_question_success_criteria(self, question_id: str) -> str:
        """Get success criteria for question remediation"""
        criteria = {
            "SEC01": "Todas las mejores prácticas de identidad y acceso implementadas con score >80",
            "SEC02": "Sistema de monitoreo completo activo con alertas configuradas",
        }
        return criteria.get(
            question_id, "Todas las BPs con score >70 y validación técnica completa"
        )
