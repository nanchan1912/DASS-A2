# Mission Planning Module - Assigns missions and verifies role availability

from config import MECHANIC, DRIVER, STRATEGIST, MISSION_TYPE_DELIVERY, MISSION_TYPE_RESCUE, MISSION_TYPE_HEIST


class Mission:
    """Represents a mission."""
    
    def __init__(self, mission_id, mission_name, mission_type, required_roles, reward):
        """
        Initialize a mission.
        
        Args:
            mission_id: Unique mission identifier
            mission_name: Name of the mission
            mission_type: Type of mission
            required_roles: List of required roles
            reward: Reward amount
        """
        self.mission_id = mission_id
        self.mission_name = mission_name
        self.mission_type = mission_type
        self.required_roles = required_roles
        self.reward = reward
        self.assigned_crew = {}  # role -> member_id
        self.status = "available"  # available, active, completed, failed
    
    def start_mission(self, crew_assignment):
        """
        Start the mission with assigned crew.
        
        Args:
            crew_assignment: Dict of {role -> member_id}
        """
        # Verify all required roles are assigned
        for role in self.required_roles:
            if role not in crew_assignment:
                raise ValueError(f"Missing required role: {role}")
        
        self.assigned_crew = crew_assignment.copy()
        self.status = "active"
    
    def complete_mission(self):
        """Complete the mission."""
        self.status = "completed"
    
    def fail_mission(self):
        """Mark mission as failed."""
        self.status = "failed"
    
    def __repr__(self):
        return f"Mission(id={self.mission_id}, name={self.mission_name}, type={self.mission_type}, status={self.status})"


class MissionPlanningModule:
    """Manages mission planning and crew assignment."""
    
    def __init__(self, crew_management, inventory):
        """
        Initialize mission planning module.
        
        Args:
            crew_management: CrewManagementModule instance
            inventory: InventoryModule instance
        """
        self.crew_management = crew_management
        self.inventory = inventory
        self.missions = {}
        self.next_mission_id = 1
    
    def create_mission(self, mission_name, mission_type, required_roles, reward=2000):
        """
        Create a new mission.
        
        Args:
            mission_name: Name of the mission
            mission_type: Type of mission
            required_roles: List of required roles
            reward: Reward amount
        
        Returns:
            mission_id
        
        Raises:
            ValueError: If required roles are invalid
        """
        valid_types = [MISSION_TYPE_DELIVERY, MISSION_TYPE_RESCUE, MISSION_TYPE_HEIST]
        if mission_type not in valid_types:
            raise ValueError(f"Invalid mission type: {mission_type}")
        
        for role in required_roles:
            if role not in [DRIVER, MECHANIC, STRATEGIST]:
                raise ValueError(f"Invalid role required: {role}")
        
        mission_id = self.next_mission_id
        mission = Mission(mission_id, mission_name, mission_type, required_roles, reward)
        self.missions[mission_id] = mission
        self.next_mission_id += 1
        
        return mission_id
    
    def get_mission(self, mission_id):
        """Get a mission by ID."""
        return self.missions.get(mission_id)
    
    def check_role_availability(self, role):
        """
        Check if a role is available (has active crew members).
        
        Args:
            role: Role to check
        
        Returns:
            True if role is available, False otherwise
        """
        crew_with_role = self.crew_management.registration.get_members_by_role(role)
        active_crew = [m for m in crew_with_role if m.is_active]
        return len(active_crew) > 0
    
    def check_roles_availability(self, required_roles):
        """
        Check if all required roles are available.
        
        Args:
            required_roles: List of required roles
        
        Returns:
            Tuple (all_available: bool, unavailable_roles: list)
        """
        unavailable = []
        for role in required_roles:
            if not self.check_role_availability(role):
                unavailable.append(role)
        
        return len(unavailable) == 0, unavailable
    
    def get_available_members_for_role(self, role):
        """Get all available (active) members for a specific role."""
        crew_with_role = self.crew_management.registration.get_members_by_role(role)
        return [m for m in crew_with_role if m.is_active]
    
    def assign_mission(self, mission_id, crew_assignment):
        """
        Assign crew members to a mission and start it.
        
        Args:
            mission_id: Mission ID
            crew_assignment: Dict of {role -> member_id}
        
        Raises:
            ValueError: If mission not found, assignment invalid, or roles unavailable
        """
        mission = self.get_mission(mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")
        
        if mission.status != "available":
            raise ValueError(f"Mission {mission_id} is not available")
        
        # Verify all required roles are assigned
        for role in mission.required_roles:
            if role not in crew_assignment:
                raise ValueError(f"Missing required role assignment: {role}")
            
            member_id = crew_assignment[role]
            if not self.crew_management.registration.member_exists(member_id):
                raise ValueError(f"Member {member_id} not found")
            
            member = self.crew_management.registration.get_member(member_id)
            if not member.is_active:
                raise ValueError(f"Member {member_id} is not active")
            
            if member.role != role:
                raise ValueError(f"Member {member_id} does not have role {role}")
        
        # Start the mission
        mission.start_mission(crew_assignment)
    
    def complete_mission(self, mission_id, inventory):
        """
        Complete a mission and award reward.
        
        Args:
            mission_id: Mission ID
            inventory: InventoryModule instance
        """
        mission = self.get_mission(mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")
        
        if mission.status != "active":
            raise ValueError(f"Mission {mission_id} is not active")
        
        mission.complete_mission()
        inventory.add_cash(mission.reward)
    
    def fail_mission(self, mission_id):
        """Mark a mission as failed."""
        mission = self.get_mission(mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")
        
        mission.fail_mission()
    
    def get_all_missions(self):
        """Get all missions."""
        return list(self.missions.values())
    
    def get_missions_by_status(self, status):
        """Get all missions with a specific status."""
        return [m for m in self.missions.values() if m.status == status]
