# StreetRace Manager - Integration Testing System
__version__ = "1.0.0"
__author__ = "Integration Testing Team"

# Import all modules for easy access
from registration import RegistrationModule, CrewMember
from crew_management import CrewManagementModule, CrewSkills
from inventory import InventoryModule, Vehicle
from race_management import RaceManagementModule, Race
from results import ResultsModule, RaceResult, Ranking
from mission_planning import MissionPlanningModule, Mission
from fuel_management import FuelManagementModule
from reputation_system import ReputationSystem, ReputationTier

__all__ = [
    'RegistrationModule',
    'CrewMember',
    'CrewManagementModule',
    'CrewSkills',
    'InventoryModule',
    'Vehicle',
    'RaceManagementModule',
    'Race',
    'ResultsModule',
    'RaceResult',
    'Ranking',
    'MissionPlanningModule',
    'Mission',
    'FuelManagementModule',
    'ReputationSystem',
    'ReputationTier'
]
