# StreetRace Manager System - Integration Testing

## System Overview

The StreetRace Manager is a command-line system for managing underground street races, crew members, vehicles, missions, and racing operations. The system is built as a modular architecture where each component handles specific aspects of the racing ecosystem.

## Core Modules (6 Required)

### 1. **Registration Module** (`registration.py`)
- **Purpose**: Manages crew member registration and basic member information
- **Key Classes**:
  - `CrewMember`: Represents a registered crew member with ID, name, role, and status
  - `RegistrationModule`: Handles registration, activation/deactivation, and member queries
- **Key Features**:
  - Register crew members with name and initial role
  - Track member status (active/inactive)
  - Query members by ID or role
  - Validates role against allowed roles

### 2. **Crew Management Module** (`crew_management.py`)
- **Purpose**: Manages crew member roles and skill levels
- **Key Classes**:
  - `CrewSkills`: Stores skill levels for driver, mechanic, and strategist
  - `CrewManagementModule`: Handles skill updates and role assignments
- **Key Features**:
  - Assign roles to registered members only
  - Update and query skill levels (0-100 scale)
  - Check role qualifications based on minimum skill requirements
  - List crew by role
  - Identify available drivers and mechanics

### 3. **Inventory Module** (`inventory.py`)
- **Purpose**: Tracks vehicles, spare parts, tools, and cash balance
- **Key Classes**:
  - `Vehicle`: Represents a vehicle with condition state and fuel
  - `InventoryModule`: Manages all inventory items
- **Key Features**:
  - Add/remove vehicles with different types
  - Track vehicle condition (good, damaged, destroyed)
  - Manage spare parts and tools inventory
  - Maintain cash balance
  - Repair damaged vehicles (requires spare parts)
  - Prevent transactions that exceed available cash

### 4. **Race Management Module** (`race_management.py`)
- **Purpose**: Creates races and manages driver/vehicle selection
- **Key Classes**:
  - `Race`: Represents a single street race with participants and status
  - `RaceManagementModule`: Handles race creation and participant management
- **Key Features**:
  - Create races by type (street, circuit, drag)
  - Register drivers and vehicles as participants
  - Enforce driver-only participation (non-drivers rejected)
  - Prevent unavailable vehicles from racing
  - Track race status (pending, ongoing, completed, cancelled)
  - Validate minimum participant count (2 minimum)

### 5. **Results Module** (`results.py`)
- **Purpose**: Records race outcomes, updates rankings, and distributes prizes
- **Key Classes**:
  - `RaceResult`: Calculates prize distribution for a race
  - `Ranking`: Tracks driver statistics and points
  - `ResultsModule`: Records results and maintains leaderboards
- **Key Features**:
  - Record race results with positions and prize distribution
  - Maintain driver rankings by points and wins
  - Calculate and award prize money
  - Generate leaderboards (top 5, etc.)
  - Track driver statistics (races, wins, total prizes, points)
  - Update inventory cash from race prizes

### 6. **Mission Planning Module** (`mission_planning.py`)
- **Purpose**: Assigns missions and verifies required roles are available
- **Key Classes**:
  - `Mission`: Represents a mission with assigned crew
  - `MissionPlanningModule`: Handles mission creation and assignment
- **Key Features**:
  - Create missions with specific role requirements (delivery, rescue, heist)
  - Verify role availability before mission assignment
  - Assign active crew members to missions
  - Enforce role matching (member must have required role)
  - Complete missions and award rewards
  - Track mission status (available, active, completed, failed)

## Additional Modules (2 Custom)

### 7. **Fuel Management Module** (`fuel_management.py`) - *(Additional Module 1)*

**Purpose**: Manages vehicle fuel consumption and refueling for racing operations

**Why This Module Was Chosen**:
- Adds realism to race management - vehicles need fuel to race
- Integrates cash system (refueling costs money from inventory)
- Adds a limiting factor to race planning (must refuel or can't race)
- Demonstrates module interaction (depends on Inventory and Race Management)

**Key Classes**:
- `FuelManagementModule`: Manages fuel levels and consumption

**Key Features**:
- Track fuel level per vehicle (0-100 scale)
- Initialize vehicles with full tanks
- Consume fuel based on race type:
  - Street races: 20 units
  - Circuit races: 30 units  
  - Drag races: 40 units
- Refuel vehicles to full tank with cash cost (100 per unit)
- Check fuel sufficiency before races
- Report fuel status (critical, low, medium, good)
- System prevents races if vehicle lacks sufficient fuel

**Business Rules Enforced**:
- Cannot race without enough fuel
- Refueling deducts from inventory cash
- Different race types consume different fuel amounts

### 8. **Reputation System Module** (`reputation_system.py`) - *(Additional Module 2)*

**Purpose**: Tracks crew member reputation and unlocks special races/missions

**Why This Module Was Chosen**:
- Adds progression system and goals for crew members
- Unlocks exclusive content based on achievement
- Integrates with race results (automatic reputation gain/loss)
- Provides long-term gameplay incentive
- Demonstrates tier-based unlock mechanics

**Key Classes**:
- `ReputationTier`: Enum-like class for tier names
- `ReputationSystem`: Manages reputation points and tier progression

**Key Features**:
- Track reputation points per crew member (0+)
- Automatic tier advancement based on thresholds:
  - Bronze: 100 points
  - Silver: 500 points
  - Gold: 1000 points
  - Platinum: 2000 points
- Unlock content at each tier:
  - Bronze: "Night Race", "City Circuit"
  - Silver: "High-Speed Dash", "Mountain Pass"
  - Gold: "Underground Championship", "Sponsored Event"
  - Platinum: "World Tour", "Legendary Race", "VIP Heist"
- Gain reputation from race wins (50 points for 1st, 30 for 2nd, etc.)
- Lose reputation from mission failures (25 points)
- Generate reputation leaderboard
- Check if crew member has unlocked specific content

**Business Rules Enforced**:
- Reputation only increases for race wins and mission completions
- Tier unlocks happen automatically when threshold is reached
- Content remains unlocked even if reputation drops below threshold

## Module Interactions & Data Flow

```
Registration ←→ Crew Management
     ↓              ↓
     └─→ Race Management ←─→ Fuel Management
     │       ↓
     │   Results → Reputation System
     │
     └─→ Mission Planning
         ↓
     Inventory (shared state)
```

### Key Integration Points:

1. **Registration + Crew Management**: 
   - New member registered → roles can be assigned
   - Only registered members can have roles

2. **Crew Management + Race Management**:
   - Only crew members with DRIVER role can race
   - Driver must be active to register for race

3. **Race Management + Fuel Management**:
   - Before race starts, check fuel sufficiency
   - During race completion, consume fuel

4. **Race Management + Results**:
   - Race results recorded immediately after completion
   - Results update driver rankings

5. **Results + Reputation System**:
   - Race position automatically grants reputation points
   - Reputation gains unlock special races

6. **Inventory + All Modules**:
   - Shared cash balance used for refueling, repairs, mission rewards
   - Vehicle state (available/damaged) managed centrally

7. **Mission Planning + Crew Management**:
   - Mission requires specific roles
   - Only active crew with correct roles can be assigned

8. **Mission Planning + Inventory**:
   - Completing mission adds reward to cash balance

## Business Rules Implemented

1. ✅ **Crew members must be registered before role assignment**
   - `CrewManagementModule.assign_role()` validates registration first

2. ✅ **Only crew members with driver role may race**
   - `RaceManagementModule.register_participant()` checks role == DRIVER

3. ✅ **Damaged vehicles cannot race, need mechanic for repairs**
   - `InventoryModule.damage_vehicle()` marks unavailable
   - `InventoryModule.repair_vehicle()` requires spare parts and mechanic availability

4. ✅ **Race results update inventory cash**
   - `ResultsModule.record_race_result()` calculates prizes
   - `ResultsModule.update_cash_balance_from_race()` adds prize to inventory

5. ✅ **Missions cannot start if required roles unavailable**
   - `MissionPlanningModule.check_roles_availability()` verifies before assignment
   - `MissionPlanningModule.assign_mission()` validates all roles are assigned

## Integration Testing Strategy

The test suite (`test_integration.py`) includes:

- **Business Rule Compliance Tests** (5 rule categories)
- **Module Interaction Tests** (complete workflows)
- **Error Handling Tests** (invalid inputs, boundary conditions)
- **State Consistency Tests** (multiple concurrent operations)
- **Leaderboard and System State Tests** (comprehensive tracking)

### Test Coverage:
- 45+ test cases covering:
  - Individual module functionality
  - Inter-module interactions
  - Business rule enforcement
  - Error conditions
  - Edge cases
  - Complete system workflows

### Running Tests:
```bash
cd integration
pytest test_integration.py -v
```

## File Structure

```
integration/
├── config.py                  # System constants and configuration
├── registration.py            # Registration module (required)
├── crew_management.py         # Crew management module (required)
├── inventory.py              # Inventory module (required)
├── race_management.py        # Race management module (required)
├── results.py                # Results module (required)
├── mission_planning.py       # Mission planning module (required)
├── fuel_management.py        # Fuel management module (additional)
├── reputation_system.py      # Reputation system module (additional)
├── test_integration.py       # Comprehensive integration tests
└── README.md                 # This file
```

## Example Workflow: Complete Racing Season

```python
# 1. Register crew
driver1_id = system['registration'].register_member("Alice", DRIVER)
driver2_id = system['registration'].register_member("Bob", DRIVER)
mechanic_id = system['registration'].register_member("Charlie", MECHANIC)

# 2. Setup inventory
car1_id = system['inventory'].add_vehicle("Speedster", "sports")
car2_id = system['inventory'].add_vehicle("Cruiser", "sports")
system['inventory'].add_spare_parts("engine_part", 10)
system['fuel'].initialize_vehicle_fuel(car1_id)
system['fuel'].initialize_vehicle_fuel(car2_id)

# 3. Create and run races
race_id = system['race_mgmt'].create_race("City Championship", RACE_TYPE_STREET, 20000)
system['race_mgmt'].register_participant(race_id, driver1_id, car1_id)
system['race_mgmt'].register_participant(race_id, driver2_id, car2_id)
system['race_mgmt'].start_race(race_id)

# Consume fuel during race
system['fuel'].consume_fuel(car1_id, RACE_TYPE_STREET)
system['fuel'].consume_fuel(car2_id, RACE_TYPE_STREET)

# 4. Record results
results = [(driver1_id, 1), (driver2_id, 2)]
system['race_mgmt'].complete_race(race_id, results)
system['results'].record_race_result(race_id, results, 20000)

# 5. Update reputation
system['reputation'].gain_reputation_from_race_win(driver1_id, 1)
system['reputation'].gain_reputation_from_race_win(driver2_id, 2)

# 6. Run mission
mission_id = system['missions'].create_mission(
    "Urgent Delivery", MISSION_TYPE_DELIVERY, [DRIVER], reward=5000
)
system['missions'].assign_mission(mission_id, {DRIVER: driver1_id})
system['missions'].complete_mission(mission_id, system['inventory'])

# 7. Check standings
leaderboard = system['results'].get_top_drivers(5)
for ranking in leaderboard:
    print(f"{ranking.driver_name}: {ranking.points} points, {ranking.wins} wins")
```

## Conclusion

The StreetRace Manager system demonstrates comprehensive integration testing with:
- **Modular Architecture**: 8 independent but interconnected modules
- **Clear Responsibilities**: Each module handles one aspect of the system
- **Business Rule Enforcement**: Rules verified across module boundaries
- **Data Flow**: Information flows consistently between modules
- **Error Handling**: Invalid states prevented at integration points
- **Extensibility**: Easy to add new modules or rules

The two additional modules (Fuel Management and Reputation System) were chosen to add meaningful gameplay complexity while demonstrating proper module integration and data flow validation.
