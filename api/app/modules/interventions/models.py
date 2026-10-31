"""
DISHA Interventions Models

This module re-exports intervention domain models authoritatively owned and maintained
in the Cases domain (`app.modules.cases.models`), preventing duplicate SQLAlchemy table
registrations for `disha_interventions`, `disha_intervention_catalogue`, and
`disha_intervention_outcomes`.
"""

from app.modules.cases.models import (
    InterventionCatalogue,
    Intervention,
    InterventionOutcome,
    JSONType,
)

__all__ = [
    "InterventionCatalogue",
    "Intervention",
    "InterventionOutcome",
    "JSONType",
]

