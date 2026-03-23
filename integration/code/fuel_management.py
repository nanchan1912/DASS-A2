# Fuel Management Module (Additional Module 1) - Manages fuel consumption and refueling

from config import FUEL_CONSUMPTION_STREET, FUEL_CONSUMPTION_CIRCUIT, FUEL_CONSUMPTION_DRAG, RACE_TYPE_STREET, RACE_TYPE_CIRCUIT, RACE_TYPE_DRAG


class FuelManagementModule:
    """Manages vehicle fuel levels and consumption."""
    
    def __init__(self, inventory):
        """
        Initialize fuel management module.
        
        Args:
            inventory: InventoryModule instance
        """
        self.inventory = inventory
        self.fuel_levels = {}  # vehicle_id -> fuel level (0-100)
    
    def initialize_vehicle_fuel(self, vehicle_id):
        """Initialize fuel level for a vehicle (full tank)."""
        self.fuel_levels[vehicle_id] = 100
    
    def refuel_vehicle(self, vehicle_id, cost_per_unit=100):
        """
        Refuel a vehicle to full tank.
        
        Args:
            vehicle_id: Vehicle ID
            cost_per_unit: Cost per unit of fuel
        
        Raises:
            ValueError: If vehicle not found or insufficient cash
        """
        if vehicle_id not in self.fuel_levels:
            self.initialize_vehicle_fuel(vehicle_id)
        
        current_fuel = self.fuel_levels[vehicle_id]
        fuel_needed = 100 - current_fuel
        total_cost = fuel_needed * cost_per_unit
        
        # Deduct from cash
        self.inventory.deduct_cash(total_cost)
        
        # Set to full tank
        self.fuel_levels[vehicle_id] = 100
    
    def get_fuel_level(self, vehicle_id):
        """Get current fuel level for a vehicle."""
        if vehicle_id not in self.fuel_levels:
            self.initialize_vehicle_fuel(vehicle_id)
        return self.fuel_levels[vehicle_id]
    
    def consume_fuel(self, vehicle_id, race_type):
        """
        Consume fuel during a race.
        
        Args:
            vehicle_id: Vehicle ID
            race_type: Type of race
        
        Raises:
            ValueError: If insufficient fuel or invalid race type
        """
        valid_types = [RACE_TYPE_STREET, RACE_TYPE_CIRCUIT, RACE_TYPE_DRAG]
        if race_type not in valid_types:
            raise ValueError(f"Invalid race type: {race_type}")
        
        # Determine fuel consumption
        consumption_map = {
            RACE_TYPE_STREET: FUEL_CONSUMPTION_STREET,
            RACE_TYPE_CIRCUIT: FUEL_CONSUMPTION_CIRCUIT,
            RACE_TYPE_DRAG: FUEL_CONSUMPTION_DRAG,
        }
        fuel_to_consume = consumption_map[race_type]
        
        if vehicle_id not in self.fuel_levels:
            self.initialize_vehicle_fuel(vehicle_id)
        
        current_fuel = self.fuel_levels[vehicle_id]
        if current_fuel < fuel_to_consume:
            raise ValueError(f"Vehicle {vehicle_id} has insufficient fuel for {race_type} race")
        
        self.fuel_levels[vehicle_id] -= fuel_to_consume
    
    def check_fuel_sufficiency(self, vehicle_id, race_type):
        """
        Check if vehicle has sufficient fuel for a race.
        
        Args:
            vehicle_id: Vehicle ID
            race_type: Type of race
        
        Returns:
            True if fuel sufficient, False otherwise
        """
        consumption_map = {
            RACE_TYPE_STREET: FUEL_CONSUMPTION_STREET,
            RACE_TYPE_CIRCUIT: FUEL_CONSUMPTION_CIRCUIT,
            RACE_TYPE_DRAG: FUEL_CONSUMPTION_DRAG,
        }
        fuel_needed = consumption_map.get(race_type, 0)
        
        if vehicle_id not in self.fuel_levels:
            self.initialize_vehicle_fuel(vehicle_id)
        
        return self.fuel_levels[vehicle_id] >= fuel_needed
    
    def get_fuel_status(self, vehicle_id):
        """Get fuel status for a vehicle."""
        fuel = self.get_fuel_level(vehicle_id)
        if fuel < 20:
            return "critical"
        elif fuel < 50:
            return "low"
        elif fuel < 80:
            return "medium"
        else:
            return "good"
    
    def get_all_vehicles_fuel_status(self):
        """Get fuel status for all vehicles."""
        status = {}
        for vehicle_id in self.inventory.vehicles.keys():
            fuel = self.get_fuel_level(vehicle_id)
            status[vehicle_id] = {
                "fuel_level": fuel,
                "status": self.get_fuel_status(vehicle_id)
            }
        return status
