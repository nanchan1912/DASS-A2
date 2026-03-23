# StreetRace Manager - Quick Start Guide

## Overview

StreetRace Manager is a Python-based integration testing system that manages underground street racing operations. The system is organized into 8 independent modules that interact with each other to enforce business rules and maintain data consistency.

## System Architecture

### Core Components (6 Required)

| Module | Responsibility |
|--------|-----------------|
| **Registration** | Register crew members with roles |
| **Crew Management** | Manage skills and qualifications |
| **Inventory** | Track vehicles, parts, tools, and cash |
| **Race Management** | Create races and manage participants |
| **Results** | Record outcomes and maintain rankings |
| **Mission Planning** | Assign missions with role requirements |

### Additional Components (2 Custom)

| Module | Responsibility |
|--------|-----------------|
| **Fuel Management** | Track fuel consumption and refueling |
| **Reputation System** | Manage reputation and unlock special content |

## Quick Start

### 1. Basic Setup

```python
from registration import RegistrationModule
from crew_management import CrewManagementModule
from inventory import InventoryModule
from race_management import RaceManagementModule
from results import ResultsModule
from mission_planning import MissionPlanningModule
from fuel_management import FuelManagementModule
from reputation_system import ReputationSystem
from config import DRIVER, MECHANIC, STRATEGIST, RACE_TYPE_STREET

# Initialize all modules
registration = RegistrationModule()
inventory = InventoryModule(initial_cash=100000)
crew_mgmt = CrewManagementModule(registration)
race_mgmt = RaceManagementModule(crew_mgmt, inventory)
results = ResultsModule(crew_mgmt)
missions = MissionPlanningModule(crew_mgmt, inventory)
fuel = FuelManagementModule(inventory)
reputation = ReputationSystem(crew_mgmt)
```

### 2. Register Crew Members

```python
# Register drivers
driver1_id = registration.register_member("Alice Johnson", DRIVER)
driver2_id = registration.register_member("Bob Smith", DRIVER)

# Register support crew
mechanic_id = registration.register_member("Charlie Brown", MECHANIC)
strategist_id = registration.register_member("Diana Prince", STRATEGIST)

# Update skill levels
crew_mgmt.update_skill_level(driver1_id, DRIVER, 85)  # High skill driver
crew_mgmt.update_skill_level(driver2_id, DRIVER, 60)  # Moderate skill
```

### 3. Setup Inventory

```python
# Add vehicles
car1_id = inventory.add_vehicle("Speedster", "sports")
car2_id = inventory.add_vehicle("Cruiser", "sports")

# Add spare parts
inventory.add_spare_parts("engine_part", 10)
inventory.add_spare_parts("tire_set", 5)

# Initialize fuel
fuel.initialize_vehicle_fuel(car1_id)
fuel.initialize_vehicle_fuel(car2_id)

# Check cash balance
print(f"Available cash: ${inventory.get_cash_balance()}")
```

### 4. Create and Run a Race

```python
# Create race
race_id = race_mgmt.create_race("City Championship", RACE_TYPE_STREET, prize_pool=20000)

# Register participants (must be drivers)
race_mgmt.register_participant(race_id, driver1_id, car1_id)
race_mgmt.register_participant(race_id, driver2_id, car2_id)

# Start race
race_mgmt.start_race(race_id)

# Consume fuel during race
fuel.consume_fuel(car1_id, RACE_TYPE_STREET)
fuel.consume_fuel(car2_id, RACE_TYPE_STREET)

# Record results
results_list = [(driver1_id, 1), (driver2_id, 2)]
race_mgmt.complete_race(race_id, results_list)

# Record in rankings and update cash
results.record_race_result(race_id, results_list, 20000)
results.update_cash_balance_from_race(inventory, driver1_id, race_id)

# Check updated rankings
ranking = results.get_driver_ranking(driver1_id)
print(f"{ranking.driver_name}: {ranking.wins} wins, {ranking.points} points")
```

### 5. Create and Assign Missions

```python
from config import MISSION_TYPE_DELIVERY

# Create mission requiring specific roles
mission_id = missions.create_mission(
    "Urgent Parts Delivery", 
    MISSION_TYPE_DELIVERY, 
    required_roles=[DRIVER],
    reward=5000
)

# Check role availability
available, unavailable = missions.check_roles_availability([DRIVER])
if available:
    # Assign to crew
    missions.assign_mission(mission_id, {DRIVER: driver1_id})
    
    # Complete mission
    missions.complete_mission(mission_id, inventory)
```

### 6. Manage Reputation

```python
# Gain reputation from race win
reputation.gain_reputation_from_race_win(driver1_id, 1)  # First place

# Check reputation status
status = reputation.get_reputation_status(driver1_id)
print(f"Reputation: {status['reputation_points']}, Tier: {status['tier']}")

# Check unlocked content
content = reputation.get_unlocked_content(driver1_id)
print(f"Unlocked: {content}")

# View leaderboard
leaderboard = reputation.get_leaderboard()
for entry in leaderboard:
    print(f"{entry['rank']}: {entry['member_name']} - {entry['reputation']} points")
```

## Business Rules Reference

### Rule 1: Registration Before Role Assignment
```python
# ✓ CORRECT
member_id = registration.register_member("John", DRIVER)
crew_mgmt.assign_role(member_id, DRIVER)

# ✗ INCORRECT
crew_mgmt.assign_role(999, DRIVER)  # Raises ValueError
```

### Rule 2: Only Drivers Can Race
```python
# ✓ CORRECT
driver_id = registration.register_member("Alice", DRIVER)
race_mgmt.register_participant(race_id, driver_id, car_id)

# ✗ INCORRECT
mechanic_id = registration.register_member("Bob", MECHANIC)
race_mgmt.register_participant(race_id, mechanic_id, car_id)  # Raises ValueError
```

### Rule 3: Car Damage and Mechanic Requirements
```python
# Damage vehicle during race
inventory.damage_vehicle(car_id, 30)  # Makes it unavailable

# Repair requires spare parts
inventory.add_spare_parts("engine_part", 2)
inventory.repair_vehicle(car_id)  # Restores to good condition
```

### Rule 4: Race Prizes Update Cash
```python
# When race completes
results.update_cash_balance_from_race(inventory, driver_id, race_id)

# Cash increased by prize amount
new_balance = inventory.get_cash_balance()
```

### Rule 5: Mission Role Availability
```python
# Create mission with role requirement
mission_id = missions.create_mission(
    "Engine Repair", 
    MISSION_TYPE_DELIVERY, 
    [MECHANIC],
    reward=2000
)

# Can only assign if mechanic is available
available, unavailable = missions.check_roles_availability([MECHANIC])
if not available:
    print(f"Unavailable roles: {unavailable}")
```

## Common Workflows

### 1. Complete Racing Season

```python
# Season setup
drivers = [
    registration.register_member(f"Driver {i}", DRIVER)
    for i in range(4)
]

vehicles = [
    inventory.add_vehicle(f"Car {i}", "sports")
    for i in range(4)
]

# Run multiple races
for race_num in range(5):
    race_id = race_mgmt.create_race(
        f"Race {race_num}", 
        RACE_TYPE_STREET, 
        prize_pool=10000
    )
    
    # Register participants
    for i in range(2):
        race_mgmt.register_participant(race_id, drivers[i], vehicles[i])
    
    # Execute race
    race_mgmt.start_race(race_id)
    fuel.consume_fuel(vehicles[0], RACE_TYPE_STREET)
    fuel.consume_fuel(vehicles[1], RACE_TYPE_STREET)
    
    # Record results (rotate winner)
    winner = drivers[race_num % len(drivers)]
    results_list = [(winner, 1), (drivers[(race_num + 1) % len(drivers)], 2)]
    race_mgmt.complete_race(race_id, results_list)
    results.record_race_result(race_id, results_list, 10000)
    
    # Update reputation
    reputation.gain_reputation_from_race_win(winner, 1)

# Show final standings
leaderboard = results.get_top_drivers(4)
for ranking in leaderboard:
    print(f"{ranking.driver_name}: {ranking.wins} wins, ${ranking.total_prize_money}")
```

### 2. Mission-Based Gameplay

```python
# Create mission chain
missions_data = [
    ("Delivery 1", MISSION_TYPE_DELIVERY, [DRIVER]),
    ("Engine Repair", MISSION_TYPE_RESCUE, [DRIVER, MECHANIC]),
    ("High-Risk Heist", MISSION_TYPE_HEIST, [DRIVER, STRATEGIST, MECHANIC])
]

completed_missions = 0

for name, mtype, roles in missions_data:
    mission_id = missions.create_mission(name, mtype, roles, reward=3000)
    
    # Check availability
    available, unavailable = missions.check_roles_availability(roles)
    if available:
        # Build crew assignment
        crew_assignment = {}
        for role in roles:
            members = missions.get_available_members_for_role(role)
            if members:
                crew_assignment[role] = members[0].member_id
        
        # Execute mission
        missions.assign_mission(mission_id, crew_assignment)
        missions.complete_mission(mission_id, inventory)
        completed_missions += 1
        
        # Update crew reputation
        for member_id in crew_assignment.values():
            reputation.add_reputation(member_id, 25)

print(f"Completed {completed_missions} missions")
```

## Data Flow Diagram

```
                    REGISTRATION
                         |
                         v
                 CREW MANAGEMENT
                    |         |
                    v         v
              RACE MGMT  MISSION PLANNING
                 |  |            |
                 |  |            v
                 |  |        INVENTORY
                 |  |            ^
                 v  v            |
            FUEL MANAGEMENT       |
                 |                |
                 v                v
             RESULTS <---------> REPUTATION
                 |
                 v
            LEADERBOARD
```

## Testing

Run the comprehensive integration test suite:

```bash
cd integration
pytest test_integration.py -v
```

Expected output:
```
26 passed in 0.11s
```

## Troubleshooting

### "Crew member not found"
- Make sure to register crew before using them
- Check member_id is correct

### "Role must be one of ['driver', 'mechanic', 'strategist']"
- Use the constants from `config.py`:
  - `DRIVER`, `MECHANIC`, `STRATEGIST`

### "Race must have at least 2 participants"
- Register 2 drivers with vehicles before calling `start_race()`

### "Insufficient cash balance"
- Add cash: `inventory.add_cash(5000)`
- Or complete missions to earn rewards

### "Vehicle not available"
- Vehicle is damaged. Repair it: `inventory.repair_vehicle(vehicle_id)`
- Or add spare parts first

## Performance Notes

- System supports unlimited crew members, vehicles, and races
- Memory usage is O(n) where n = total number of entities
- Tests complete in <200ms for typical operations

## Future Extensions

Potential modules to add:
- Sponsorship System
- Weather and Track Conditions
- Vehicle Damage Mechanics
- Law Enforcement System
- Economy and Market System

---

**For complete API documentation, see [README.md](README.md)**
