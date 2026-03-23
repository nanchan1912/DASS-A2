# Race Management Module - Creates and manages races

from config import DRIVER, VALID_ROLES, RACE_TYPE_STREET, RACE_TYPE_CIRCUIT, RACE_TYPE_DRAG


class Race:
    """Represents a street race."""
    
    def __init__(self, race_id, race_name, race_type, prize_pool):
        """
        Initialize a race.
        
        Args:
            race_id: Unique race identifier
            race_name: Name of the race
            race_type: Type of race (street, circuit, drag)
            prize_pool: Total prize money
        """
        self.race_id = race_id
        self.race_name = race_name
        self.race_type = race_type
        self.prize_pool = prize_pool
        self.participants = []  # List of (driver_id, vehicle_id) tuples
        self.status = "pending"  # pending, ongoing, completed, cancelled
        self.winner = None
        self.results = []
    
    def add_participant(self, driver_id, vehicle_id):
        """Add a driver-vehicle pair to the race."""
        self.participants.append((driver_id, vehicle_id))
    
    def start_race(self):
        """Start the race."""
        if len(self.participants) < 2:
            raise ValueError("Race must have at least 2 participants")
        self.status = "ongoing"
    
    def complete_race(self, results):
        """Complete the race with results."""
        self.status = "completed"
        self.results = results
        if results:
            self.winner = results[0][0]  # First result is winner
    
    def cancel_race(self):
        """Cancel the race."""
        self.status = "cancelled"
    
    def __repr__(self):
        return f"Race(id={self.race_id}, name={self.race_name}, status={self.status}, participants={len(self.participants)})"


class RaceManagementModule:
    """Manages race creation and execution."""
    
    def __init__(self, crew_management, inventory):
        """
        Initialize race management module.
        
        Args:
            crew_management: CrewManagementModule instance
            inventory: InventoryModule instance
        """
        self.crew_management = crew_management
        self.inventory = inventory
        self.races = {}
        self.next_race_id = 1
    
    def create_race(self, race_name, race_type, prize_pool=5000):
        """
        Create a new race.
        
        Args:
            race_name: Name of the race
            race_type: Type of race
            prize_pool: Total prize money
        
        Returns:
            race_id
        
        Raises:
            ValueError: If race type invalid
        """
        valid_types = [RACE_TYPE_STREET, RACE_TYPE_CIRCUIT, RACE_TYPE_DRAG]
        if race_type not in valid_types:
            raise ValueError(f"Invalid race type: {race_type}")
        
        race_id = self.next_race_id
        race = Race(race_id, race_name, race_type, prize_pool)
        self.races[race_id] = race
        self.next_race_id += 1
        
        return race_id
    
    def get_race(self, race_id):
        """Get a race by ID."""
        return self.races.get(race_id)
    
    def register_participant(self, race_id, driver_id, vehicle_id):
        """
        Register a driver and vehicle for a race (driver must have driver role).
        
        Args:
            race_id: Race ID
            driver_id: Crew member ID (must be a driver)
            vehicle_id: Vehicle ID
        
        Raises:
            ValueError: If driver not driver role, vehicle not available, or race not found
        """
        race = self.get_race(race_id)
        if not race:
            raise ValueError(f"Race {race_id} not found")
        
        # Check driver is active and has driver role
        driver = self.crew_management.registration.get_member(driver_id)
        if not driver:
            raise ValueError(f"Driver {driver_id} not found")
        
        if not driver.is_active:
            raise ValueError(f"Driver {driver_id} is not active")
        
        if driver.role != DRIVER:
            raise ValueError(f"Crew member {driver_id} must have {DRIVER} role to race")
        
        # Check vehicle exists and is available
        vehicle = self.inventory.get_vehicle(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle {vehicle_id} not found")
        
        if not vehicle.is_available:
            raise ValueError(f"Vehicle {vehicle_id} is not available")
        
        # Add participant to race
        race.add_participant(driver_id, vehicle_id)
    
    def start_race(self, race_id):
        """
        Start a race.
        
        Args:
            race_id: Race ID
        
        Raises:
            ValueError: If race not found or doesn't have enough participants
        """
        race = self.get_race(race_id)
        if not race:
            raise ValueError(f"Race {race_id} not found")
        
        race.start_race()
    
    def complete_race(self, race_id, results):
        """
        Complete a race with results.
        
        Args:
            race_id: Race ID
            results: List of (driver_id, position) tuples in finishing order
        """
        race = self.get_race(race_id)
        if not race:
            raise ValueError(f"Race {race_id} not found")
        
        race.complete_race(results)
    
    def cancel_race(self, race_id):
        """Cancel a race."""
        race = self.get_race(race_id)
        if not race:
            raise ValueError(f"Race {race_id} not found")
        race.cancel_race()
    
    def get_race_participants(self, race_id):
        """Get all participants in a race."""
        race = self.get_race(race_id)
        if not race:
            raise ValueError(f"Race {race_id} not found")
        return race.participants
    
    def get_all_races(self):
        """Get all races."""
        return list(self.races.values())
    
    def get_races_by_status(self, status):
        """Get all races with a specific status."""
        return [r for r in self.races.values() if r.status == status]
