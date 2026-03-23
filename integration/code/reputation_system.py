# Reputation System Module (Additional Module 2) - Tracks reputation and unlocks special content

from config import REPUTATION_THRESHOLD_BRONZE, REPUTATION_THRESHOLD_SILVER, REPUTATION_THRESHOLD_GOLD, REPUTATION_THRESHOLD_PLATINUM


class ReputationTier:
    """Represents reputation tier levels."""
    
    UNKNOWN = "unknown"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class ReputationSystem:
    """Tracks crew member reputation and unlocks special races/missions."""
    
    def __init__(self, crew_management):
        """
        Initialize reputation system.
        
        Args:
            crew_management: CrewManagementModule instance
        """
        self.crew_management = crew_management
        self.reputation = {}  # member_id -> reputation points
        self.tiers = {}  # member_id -> tier
        self.unlocked_content = {}  # member_id -> list of unlocked content
        
        # Special races/missions unlocked at each tier
        self.tier_unlocks = {
            ReputationTier.BRONZE: ["Night Race", "City Circuit"],
            ReputationTier.SILVER: ["High-Speed Dash", "Mountain Pass"],
            ReputationTier.GOLD: ["Underground Championship", "Sponsored Event"],
            ReputationTier.PLATINUM: ["World Tour", "Legendary Race", "VIP Heist"]
        }

    def _require_member(self, member_id):
        """Return the member if it exists, otherwise raise an error."""
        member = self.crew_management.registration.get_member(member_id)
        if member is None:
            raise ValueError(f"Member {member_id} not found")
        return member

    def initialize_member_reputation(self, member_id):
        """Initialize reputation for a member."""
        self._require_member(member_id)
        if member_id not in self.reputation:
            self.reputation[member_id] = 0
            self.tiers[member_id] = ReputationTier.UNKNOWN
            self.unlocked_content[member_id] = []
    
    def add_reputation(self, member_id, points):
        """
        Add reputation points to a member.
        
        Args:
            member_id: Member ID
            points: Reputation points to add
        
        Raises:
            ValueError: If member not found
        """
        self._require_member(member_id)

        self.initialize_member_reputation(member_id)
        
        if points < 0:
            raise ValueError("Reputation points cannot be negative")
        
        self.reputation[member_id] += points
        self._update_tier(member_id)
    
    def reduce_reputation(self, member_id, points):
        """
        Reduce reputation points (e.g., for failed missions).
        
        Args:
            member_id: Member ID
            points: Reputation points to reduce
        """
        self._require_member(member_id)

        self.initialize_member_reputation(member_id)
        
        if points < 0:
            raise ValueError("Reputation points cannot be negative")
        
        self.reputation[member_id] = max(0, self.reputation[member_id] - points)
        self._update_tier(member_id)
    
    def _update_tier(self, member_id):
        """Update tier based on reputation points."""
        rep_points = self.reputation[member_id]
        old_tier = self.tiers[member_id]
        
        if rep_points >= REPUTATION_THRESHOLD_PLATINUM:
            new_tier = ReputationTier.PLATINUM
        elif rep_points >= REPUTATION_THRESHOLD_GOLD:
            new_tier = ReputationTier.GOLD
        elif rep_points >= REPUTATION_THRESHOLD_SILVER:
            new_tier = ReputationTier.SILVER
        elif rep_points >= REPUTATION_THRESHOLD_BRONZE:
            new_tier = ReputationTier.BRONZE
        else:
            new_tier = ReputationTier.UNKNOWN
        
        self.tiers[member_id] = new_tier
        
        # Unlock new content if tier changed
        if new_tier != old_tier and new_tier != ReputationTier.UNKNOWN:
            if new_tier in self.tier_unlocks:
                new_unlocks = self.tier_unlocks[new_tier]
                for content in new_unlocks:
                    if content not in self.unlocked_content[member_id]:
                        self.unlocked_content[member_id].append(content)
    
    def get_member_reputation(self, member_id):
        """Get reputation points for a member."""
        self.initialize_member_reputation(member_id)
        return self.reputation[member_id]
    
    def get_member_tier(self, member_id):
        """Get reputation tier for a member."""
        self.initialize_member_reputation(member_id)
        return self.tiers[member_id]
    
    def get_unlocked_content(self, member_id):
        """Get list of unlocked special races/missions for a member."""
        self.initialize_member_reputation(member_id)
        return self.unlocked_content[member_id].copy()
    
    def is_content_unlocked(self, member_id, content_name):
        """
        Check if a member has unlocked specific content.
        
        Args:
            member_id: Member ID
            content_name: Name of content to check
        
        Returns:
            True if unlocked, False otherwise
        """
        self.initialize_member_reputation(member_id)
        return content_name in self.unlocked_content[member_id]
    
    def get_reputation_status(self, member_id):
        """Get detailed reputation status for a member."""
        self.initialize_member_reputation(member_id)
        member = self._require_member(member_id)

        return {
            "member_id": member_id,
            "member_name": member.name,
            "reputation_points": self.reputation[member_id],
            "tier": self.tiers[member_id],
            "unlocked_content": self.unlocked_content[member_id]
        }
    
    def get_leaderboard(self):
        """Get reputation leaderboard (top 10 members by reputation)."""
        sorted_members = sorted(
            self.reputation.items(),
            key=lambda x: (-x[1], x[0])  # Sort by reputation desc, then by ID
        )
        leaderboard = []
        for i, (member_id, rep_points) in enumerate(sorted_members[:10], 1):
            member = self.crew_management.registration.get_member(member_id)
            leaderboard.append({
                "rank": i,
                "member_name": member.name if member else f"Member {member_id}",
                "reputation": rep_points,
                "tier": self.tiers.get(member_id, ReputationTier.UNKNOWN)
            })
        return leaderboard
    
    def gain_reputation_from_race_win(self, member_id, position):
        """
        Award reputation points based on race position.
        
        Args:
            member_id: Member ID
            position: Race finishing position (1=first, 2=second, etc.)
        """
        reputation_rewards = {
            1: 50,   # First place
            2: 30,   # Second place
            3: 20,   # Third place
            4: 10,   # Fourth place
        }
        
        points = reputation_rewards.get(position, 5)
        self.add_reputation(member_id, points)
    
    def lose_reputation_from_mission_failure(self, member_id):
        """
        Lose reputation points from failed mission.
        
        Args:
            member_id: Member ID
        """
        self.reduce_reputation(member_id, 25)
