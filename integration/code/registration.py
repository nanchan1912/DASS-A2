# Registration Module - Handles crew member registration

from datetime import datetime
from config import VALID_ROLES


class CrewMember:
    """Represents a registered crew member."""
    
    def __init__(self, member_id, name, role):
        """
        Initialize a crew member.
        
        Args:
            member_id: Unique identifier for the member
            name: Name of the crew member
            role: Role (driver, mechanic, strategist)
        
        Raises:
            ValueError: If role is not valid
        """
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}. Must be one of {VALID_ROLES}")
        
        self.member_id = member_id
        self.name = name
        self.role = role
        self.registration_date = datetime.now()
        self.is_active = True
    
    def deactivate(self):
        """Deactivate crew member."""
        self.is_active = False
    
    def activate(self):
        """Activate crew member."""
        self.is_active = True
    
    def __repr__(self):
        return f"CrewMember(id={self.member_id}, name={self.name}, role={self.role}, active={self.is_active})"


class RegistrationModule:
    """Manages crew member registration."""
    
    def __init__(self):
        """Initialize registration module."""
        self.members = {}
        self.next_id = 1
    
    def register_member(self, name, role):
        """
        Register a new crew member.
        
        Args:
            name: Name of the crew member
            role: Role (driver, mechanic, strategist)
        
        Returns:
            member_id: ID of the registered crew member
        
        Raises:
            ValueError: If name is empty or role is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string")
        
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        
        member_id = self.next_id
        member = CrewMember(member_id, name, role)
        self.members[member_id] = member
        self.next_id += 1
        
        return member_id
    
    def get_member(self, member_id):
        """
        Get a crew member by ID.
        
        Args:
            member_id: ID of the crew member
        
        Returns:
            CrewMember object or None if not found
        """
        return self.members.get(member_id)
    
    def member_exists(self, member_id):
        """Check if a crew member is registered."""
        return member_id in self.members
    
    def list_all_members(self):
        """Get list of all registered crew members."""
        return list(self.members.values())
    
    def list_active_members(self):
        """Get list of all active crew members."""
        return [m for m in self.members.values() if m.is_active]
    
    def get_members_by_role(self, role):
        """Get all members with a specific role."""
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        return [m for m in self.members.values() if m.role == role]
    
    def deactivate_member(self, member_id):
        """Deactivate a crew member."""
        if member_id not in self.members:
            raise ValueError(f"Member {member_id} not found")
        self.members[member_id].deactivate()
    
    def activate_member(self, member_id):
        """Activate a crew member."""
        if member_id not in self.members:
            raise ValueError(f"Member {member_id} not found")
        self.members[member_id].activate()
