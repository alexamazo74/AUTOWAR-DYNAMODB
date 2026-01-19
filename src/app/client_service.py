"""
Client Management Service for AutoWAR Platform
Manages client profiles and industry-specific configurations
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .models import ClientProfile
from .aws_connector import get_table


class ClientService:
    """Service for client management and profiling"""

    def __init__(self, dynamodb_table=None, table_name: str = 'autowar-clients'):
        self.dynamodb = dynamodb_table.meta.client if dynamodb_table else None
        self.table_name = table_name
        self.table = dynamodb_table

    def get_client_profile(self, client_id: str) -> Optional[ClientProfile]:
        """Get client profile by ID"""
        # Mock client profiles for now
        mock_clients = {
            "client-001": ClientProfile(
                client_id="client-001",
                name="Empresa Financiera XYZ",
                industry="finance",
                region="us-east-1",
                size="large",
                compliance_requirements=["SOX", "PCI-DSS", "GDPR"],
                risk_tolerance="low",
                contact_info={"email": "security@xyz.com", "phone": "+1-555-0123"}
            ),
            "client-002": ClientProfile(
                client_id="client-002",
                name="Hospital Central",
                industry="healthcare",
                region="eu-west-1",
                size="medium",
                compliance_requirements=["HIPAA", "GDPR"],
                risk_tolerance="low",
                contact_info={"email": "it@hospital.com", "phone": "+34-555-0123"}
            ),
            "client-003": ClientProfile(
                client_id="client-003",
                name="Startup Tech Inc",
                industry="technology",
                region="us-west-2",
                size="small",
                compliance_requirements=["SOC2"],
                risk_tolerance="medium",
                contact_info={"email": "admin@startup.com", "phone": "+1-555-0456"}
            )
        }

        return mock_clients.get(client_id)

    def get_industry_risk_multipliers(self, industry: str) -> Dict[str, float]:
        """Get risk multipliers based on industry"""
        industry_multipliers = {
            "finance": {
                "security_multiplier": 1.5,
                "compliance_multiplier": 2.0,
                "data_protection_multiplier": 1.8
            },
            "healthcare": {
                "security_multiplier": 1.8,
                "compliance_multiplier": 2.5,
                "data_protection_multiplier": 2.0
            },
            "government": {
                "security_multiplier": 2.0,
                "compliance_multiplier": 3.0,
                "data_protection_multiplier": 2.5
            },
            "technology": {
                "security_multiplier": 1.2,
                "compliance_multiplier": 1.5,
                "data_protection_multiplier": 1.3
            },
            "retail": {
                "security_multiplier": 1.3,
                "compliance_multiplier": 1.2,
                "data_protection_multiplier": 1.4
            }
        }

        return industry_multipliers.get(industry, {
            "security_multiplier": 1.0,
            "compliance_multiplier": 1.0,
            "data_protection_multiplier": 1.0
        })

    def get_compliance_frameworks(self, industry: str) -> List[str]:
        """Get relevant compliance frameworks for an industry"""
        frameworks = {
            "finance": ["SOX", "PCI-DSS", "GLBA", "FFIEC"],
            "healthcare": ["HIPAA", "HITECH", "GDPR", "HITRUST"],
            "government": ["FedRAMP", "FISMA", "NIST", "ISO 27001"],
            "technology": ["SOC 2", "ISO 27001", "CSA STAR", "PCI-DSS"],
            "retail": ["PCI-DSS", "GDPR", "CCPA"]
        }

        return frameworks.get(industry, ["ISO 27001", "GDPR"])