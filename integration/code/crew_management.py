# Crew Management Module - Manages roles and skill levels

from config import VALID_ROLES, MIN_SKILL, MAX_SKILL, DRIVER, MECHANIC, STRATEGIST


class CrewSkills:
    """Represents skill levels for a crew member."""
    
    def __init__(self):
        """Initialize skill levels (driver, mechanic, strategist)."""
        self.driver_skill = MIN_SKILL
        self.mechanic_skill = MIN_SKILL
        self.strategist_skill = MIN_SKILL
    
    def get_skill(self, skill_type):
        """Get skill level by type."""
        if skill_type == DRIVER:
            return self.driver_skill
        elif skill_type == MECHANIC:
            return self.mechanic_skill
        elif skill_type == STRATEGIST:
            return self.strategist_skill
        else:
            raise ValueError(f"Unknown skill type: {skill_type}")
    
    def set_skill(self, skill_type, level):
        """Set skill level."""
        if not (MIN_SKILL <= level <= MAX_SKILL):
            raise ValueError(f"Skill level must be between {MIN_SKILL} and {MAX_SKILL}")
        
        if skill_type == DRIVER:
            self.driver_skill = level
        elif skill_type == MECHANIC:
            self.mechanic_skill = level
        elif skill_type == STRATEGIST:
            self.strategist_skill = level
        else:
            raise ValueError(f"Unknown skill type: {skill_type}")


class CrewManagementModule:
    """Manages crew member roles and skills."""
    
    def __init__(self, registration_module):
        """
        Initialize crew management module.
        
        Args:
            registration_module: RegistrationModule instance for member validation
        """
        self.registration = registration_module
        self.crew_skills = {}  # member_id -> CrewSkills
    
    def assign_role(self, member_id, role):
        """
        Assign a role to a crew member (must be registered first).
        
        Args:
            member_id: ID of the crew member
            role: Role to assign
        
        Raises:
            ValueError: If member not registered or role invalid
        """
        if not self.registration.member_exists(member_id):
            raise ValueError(f"Crew member {member_id} not registered. Must register before assigning role.")
        
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        
        # Update role in registration
        member = self.registration.get_member(member_id)
        member.role = role
        
        # Initialize skills if not exists
        if member_id not in self.crew_skills:
            self.crew_skills[member_id] = CrewSkills()
    
    def update_skill_level(self, member_id, skill_type, level):
        """
        Update skill level for a crew member.
        
        Args:
            member_id: ID of the crew member
            skill_type: Type of skill (driver, mechanic, strategist)
            level: New skill level (0-100)
        
        Raises:
            ValueError: If member not found or skill level invalid
        """
        if not self.registration.member_exists(member_id):
            raise ValueError(f"Crew member {member_id} not found")
        
        if member_id not in self.crew_skills:
            self.crew_skills[member_id] = CrewSkills()
        
        self.crew_skills[member_id].set_skill(skill_type, level)
    
    def get_skill_level(self, member_id, skill_type):
        """
        Get skill level for a crew member.
        
        Args:
            member_id: ID of the crew member
            skill_type: Type of skill
        
        Returns:
            Skill level (0-100)
        """
        if not self.registration.member_exists(member_id):
            raise ValueError(f"Crew member {member_id} not found")
        
        if member_id not in self.crew_skills:
            self.crew_skills[member_id] = CrewSkills()
        
        return self.crew_skills[member_id].get_skill(skill_type)
    
    def get_crew_skills(self, member_id):
        """Get all skills for a crew member."""
        if not self.registration.member_exists(member_id):
            raise ValueError(f"Crew member {member_id} not found")
        
        if member_id not in self.crew_skills:
            self.crew_skills[member_id] = CrewSkills()
        
        return self.crew_skills[member_id]
    
    def is_qualified_for_role(self, member_id, role, min_skill=50):
        """
        Check if crew member is qualified for a specific role (skill >= min_skill).
        
        Args:
            member_id: ID of the crew member
            role: Role to check
            min_skill: Minimum required skill level
        
        Returns:
            True if qualified, False otherwise
        """
        try:
            skill_level = self.get_skill_level(member_id, role)
            return skill_level >= min_skill
        except ValueError:
            return False
    
    def list_crew_by_role(self, role):
        """Get all active crew members with a specific role."""
        crew = self.registration.get_members_by_role(role)
        return [member for member in crew if member.is_active]
    
    def get_available_drivers(self):
        """Get list of available (active) drivers."""
        drivers = self.registration.get_members_by_role(DRIVER)
        return [d for d in drivers if d.is_active]
    
    def get_available_mechanics(self):
        """Get list of available (active) mechanics."""
        mechanics = self.registration.get_members_by_role(MECHANIC)
        return [m for m in mechanics if m.is_active]
