# Inventory Module - Tracks vehicles, parts, tools, and cash

from config import VEHICLE_CONDITION_GOOD, VEHICLE_CONDITION_DAMAGED, VEHICLE_CONDITION_DESTROYED


class Vehicle:
    """Represents a vehicle in the inventory."""
    
    def __init__(self, vehicle_id, name, vehicle_type):
        """
        Initialize a vehicle.
        
        Args:
            vehicle_id: Unique identifier
            name: Vehicle name
            vehicle_type: Type of vehicle (e.g., "sports", "truck")
        """
        self.vehicle_id = vehicle_id
        self.name = name
        self.vehicle_type = vehicle_type
        self.condition = VEHICLE_CONDITION_GOOD
        self.fuel_level = 100
        self.is_available = True
    
    def damage(self, damage_percent):
        """Apply damage to vehicle."""
        if damage_percent >= 50:
            self.condition = VEHICLE_CONDITION_DESTROYED
            self.is_available = False
        elif damage_percent >= 25:
            self.condition = VEHICLE_CONDITION_DAMAGED
            self.is_available = False
        else:
            self.condition = VEHICLE_CONDITION_DAMAGED
    
    def repair(self):
        """Repair vehicle to good condition."""
        self.condition = VEHICLE_CONDITION_GOOD
        self.is_available = True
    
    def __repr__(self):
        return f"Vehicle(id={self.vehicle_id}, name={self.name}, condition={self.condition}, available={self.is_available})"


class InventoryModule:
    """Manages inventory: vehicles, parts, tools, and cash."""
    
    def __init__(self, initial_cash=50000):
        """
        Initialize inventory module.
        
        Args:
            initial_cash: Starting cash balance
        """
        self.vehicles = {}
        self.spare_parts = {}  # part_name -> quantity
        self.tools = {}  # tool_name -> quantity
        self.cash_balance = initial_cash
        self.next_vehicle_id = 1
    
    def add_vehicle(self, name, vehicle_type):
        """
        Add a vehicle to inventory.
        
        Args:
            name: Vehicle name
            vehicle_type: Type of vehicle
        
        Returns:
            vehicle_id
        """
        vehicle_id = self.next_vehicle_id
        vehicle = Vehicle(vehicle_id, name, vehicle_type)
        self.vehicles[vehicle_id] = vehicle
        self.next_vehicle_id += 1
        return vehicle_id
    
    def get_vehicle(self, vehicle_id):
        """Get vehicle by ID."""
        return self.vehicles.get(vehicle_id)
    
    def remove_vehicle(self, vehicle_id):
        """Remove vehicle from inventory."""
        if vehicle_id in self.vehicles:
            del self.vehicles[vehicle_id]
    
    def get_available_vehicles(self):
        """Get list of all available vehicles."""
        return [v for v in self.vehicles.values() if v.is_available]
    
    def add_spare_parts(self, part_name, quantity):
        """Add spare parts to inventory."""
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if part_name not in self.spare_parts:
            self.spare_parts[part_name] = 0
        self.spare_parts[part_name] += quantity
    
    def use_spare_parts(self, part_name, quantity):
        """Use spare parts from inventory."""
        if part_name not in self.spare_parts or self.spare_parts[part_name] < quantity:
            raise ValueError(f"Not enough {part_name} in inventory")
        self.spare_parts[part_name] -= quantity
    
    def get_spare_parts_quantity(self, part_name):
        """Get quantity of spare parts."""
        return self.spare_parts.get(part_name, 0)
    
    def add_tool(self, tool_name, quantity):
        """Add tools to inventory."""
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if tool_name not in self.tools:
            self.tools[tool_name] = 0
        self.tools[tool_name] += quantity
    
    def use_tool(self, tool_name, quantity):
        """Use tool from inventory."""
        if tool_name not in self.tools or self.tools[tool_name] < quantity:
            raise ValueError(f"Not enough {tool_name} in inventory")
        self.tools[tool_name] -= quantity
    
    def get_tool_quantity(self, tool_name):
        """Get quantity of a tool."""
        return self.tools.get(tool_name, 0)
    
    def add_cash(self, amount):
        """Add cash to balance."""
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        self.cash_balance += amount
    
    def deduct_cash(self, amount):
        """Deduct cash from balance."""
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        if self.cash_balance < amount:
            raise ValueError("Insufficient cash balance")
        self.cash_balance -= amount
    
    def get_cash_balance(self):
        """Get current cash balance."""
        return self.cash_balance
    
    def repair_vehicle(self, vehicle_id):
        """Repair a damaged vehicle (requires spare parts)."""
        vehicle = self.get_vehicle(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle {vehicle_id} not found")
        
        if vehicle.condition == VEHICLE_CONDITION_GOOD:
            return  # Already in good condition
        
        # Check if we have spare parts
        if self.get_spare_parts_quantity("engine_part") < 2:
            raise ValueError("Not enough engine parts to repair vehicle")
        
        # Use parts and repair
        self.use_spare_parts("engine_part", 2)
        vehicle.repair()
    
    def damage_vehicle(self, vehicle_id, damage_percent):
        """Apply damage to a vehicle."""
        vehicle = self.get_vehicle(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle {vehicle_id} not found")
        vehicle.damage(damage_percent)
    
    def get_inventory_status(self):
        """Get full inventory status."""
        return {
            "vehicles": len(self.vehicles),
            "available_vehicles": len(self.get_available_vehicles()),
            "cash": self.cash_balance,
            "spare_parts": dict(self.spare_parts),
            "tools": dict(self.tools)
        }
