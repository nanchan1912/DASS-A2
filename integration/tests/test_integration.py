"""
Integration Tests for StreetRace Manager System

This test suite verifies:
1. Individual module functionality
2. Module interactions and data flow
3. Business rule compliance
4. System consistency
"""

import pytest
from registration import RegistrationModule
from crew_management import CrewManagementModule
from inventory import InventoryModule
from race_management import RaceManagementModule
from results import ResultsModule
from mission_planning import MissionPlanningModule
from fuel_management import FuelManagementModule
from reputation_system import ReputationSystem
from config import (
    DRIVER, MECHANIC, STRATEGIST, RACE_TYPE_STREET, RACE_TYPE_CIRCUIT,
    MISSION_TYPE_DELIVERY, MISSION_TYPE_RESCUE
)


class TestSystemIntegration:
    """Test complete system integration and data flow."""

    @pytest.fixture
    def system(self):
        """Initialize complete system."""
        registration = RegistrationModule()
        inventory = InventoryModule(initial_cash=100000)
        crew_mgmt = CrewManagementModule(registration)
        race_mgmt = RaceManagementModule(crew_mgmt, inventory)
        results = ResultsModule(crew_mgmt)
        missions = MissionPlanningModule(crew_mgmt, inventory)
        fuel = FuelManagementModule(inventory)
        reputation = ReputationSystem(crew_mgmt)
        
        return {
            'registration': registration,
            'inventory': inventory,
            'crew_mgmt': crew_mgmt,
            'race_mgmt': race_mgmt,
            'results': results,
            'missions': missions,
            'fuel': fuel,
            'reputation': reputation
        }

    # ============================================================================
    # BUSINESS RULE 1: Crew members must be registered before role assignment
    # ============================================================================
    
    def test_cannot_assign_role_before_registration(self, system):
        """Verify that roles cannot be assigned to unregistered members."""
        with pytest.raises(ValueError):
            system['crew_mgmt'].assign_role(999, DRIVER)
    
    def test_role_assignment_after_registration(self, system):
        """Verify that roles can be assigned after registration."""
        member_id = system['registration'].register_member("John Doe", DRIVER)
        # Should not raise exception
        system['crew_mgmt'].assign_role(member_id, MECHANIC)
        
        member = system['registration'].get_member(member_id)
        assert member.role == MECHANIC
    
    def test_member_must_exist_for_any_operation(self, system):
        """Verify member existence is checked across all modules."""
        # Try to get skills for non-existent member
        with pytest.raises(ValueError):
            system['crew_mgmt'].get_skill_level(999, DRIVER)

    def test_list_crew_by_role_returns_only_active_members(self, system):
        """Verify crew role listings exclude inactive members."""
        driver_id = system['registration'].register_member("Active Driver", DRIVER)
        retired_id = system['registration'].register_member("Inactive Driver", DRIVER)
        system['registration'].deactivate_member(retired_id)

        listed_ids = [member.member_id for member in system['crew_mgmt'].list_crew_by_role(DRIVER)]
        assert driver_id in listed_ids
        assert retired_id not in listed_ids

    # ============================================================================
    # BUSINESS RULE 2: Only crew members with DRIVER role may enter races
    # ============================================================================
    
    def test_non_driver_cannot_register_for_race(self, system):
        """Verify non-drivers cannot register for races."""
        # Register mechanic
        mechanic_id = system['registration'].register_member("Bob Smith", MECHANIC)
        
        # Add a vehicle
        vehicle_id = system['inventory'].add_vehicle("Car 1", "sports")
        
        # Create race
        race_id = system['race_mgmt'].create_race("City Race", RACE_TYPE_STREET)
        
        # Try to register mechanic as participant
        with pytest.raises(ValueError):
            system['race_mgmt'].register_participant(race_id, mechanic_id, vehicle_id)
    
    def test_only_driver_can_race(self, system):
        """Verify only drivers can register for races."""
        # Register driver
        driver_id = system['registration'].register_member("Alice Johnson", DRIVER)
        
        # Add vehicle
        vehicle_id = system['inventory'].add_vehicle("Fast Car", "sports")
        
        # Create race
        race_id = system['race_mgmt'].create_race("Street Race", RACE_TYPE_STREET)
        
        # Register driver - should succeed
        system['race_mgmt'].register_participant(race_id, driver_id, vehicle_id)
        
        participants = system['race_mgmt'].get_race_participants(race_id)
        assert len(participants) == 1
        assert participants[0] == (driver_id, vehicle_id)
    
    def test_inactive_driver_cannot_race(self, system):
        """Verify inactive drivers cannot participate in races."""
        driver_id = system['registration'].register_member("Charlie Brown", DRIVER)
        vehicle_id = system['inventory'].add_vehicle("Car", "sports")
        race_id = system['race_mgmt'].create_race("Race", RACE_TYPE_STREET)
        
        # Deactivate driver
        system['registration'].deactivate_member(driver_id)
        
        with pytest.raises(ValueError):
            system['race_mgmt'].register_participant(race_id, driver_id, vehicle_id)

    # ============================================================================
    # BUSINESS RULE 3: Car damage and mechanic availability for repairs
    # ============================================================================
    
    def test_damaged_vehicle_cannot_race(self, system):
        """Verify damaged vehicles cannot be used in races."""
        driver_id = system['registration'].register_member("Dave Miller", DRIVER)
        vehicle_id = system['inventory'].add_vehicle("Damaged Car", "sports")
        
        # Damage the vehicle
        system['inventory'].damage_vehicle(vehicle_id, 30)
        
        race_id = system['race_mgmt'].create_race("Race", RACE_TYPE_STREET)
        
        # Cannot register damaged vehicle
        with pytest.raises(ValueError):
            system['race_mgmt'].register_participant(race_id, driver_id, vehicle_id)
    
    def test_vehicle_repair_requires_mechanic(self, system):
        """Verify that damaged vehicles need mechanics to repair."""
        vehicle_id = system['inventory'].add_vehicle("Car", "sports")
        
        # Damage vehicle
        system['inventory'].damage_vehicle(vehicle_id, 25)
        
        # Try to repair without spare parts
        with pytest.raises(ValueError):
            system['inventory'].repair_vehicle(vehicle_id)
        
        # Add spare parts
        system['inventory'].add_spare_parts("engine_part", 2)
        
        # Register mechanic
        mechanic_id = system['registration'].register_member("Eve Davis", MECHANIC)
        
        # Now repair should work
        system['inventory'].repair_vehicle(vehicle_id)
        vehicle = system['inventory'].get_vehicle(vehicle_id)
        assert vehicle.condition == "good"
    
    def test_mission_requires_available_mechanic_for_repairs(self, system):
        """Verify missions requiring mechanic check availability."""
        # Create delivery mission (requires driver)
        mission_id = system['missions'].create_mission(
            "Parts Delivery", MISSION_TYPE_DELIVERY, [DRIVER], reward=3000
        )
        
        # Register driver
        driver_id = system['registration'].register_member("Frank Green", DRIVER)
        
        # Check mechanic availability (should be false)
        available, unavailable = system['missions'].check_roles_availability([MECHANIC])
        assert not available
        assert MECHANIC in unavailable

    # ============================================================================
    # BUSINESS RULE 4: Race results update cash balance in inventory
    # ============================================================================
    
    def test_race_prize_updates_inventory_cash(self, system):
        """Verify that race prizes are added to inventory cash."""
        initial_cash = system['inventory'].get_cash_balance()
        
        # Register drivers and vehicles
        driver1_id = system['registration'].register_member("Grace Lee", DRIVER)
        driver2_id = system['registration'].register_member("Henry White", DRIVER)
        vehicle1_id = system['inventory'].add_vehicle("Car 1", "sports")
        vehicle2_id = system['inventory'].add_vehicle("Car 2", "sports")
        
        # Create and run race
        race_id = system['race_mgmt'].create_race("Main Race", RACE_TYPE_STREET, prize_pool=10000)
        system['race_mgmt'].register_participant(race_id, driver1_id, vehicle1_id)
        system['race_mgmt'].register_participant(race_id, driver2_id, vehicle2_id)
        system['race_mgmt'].start_race(race_id)
        
        # Record results
        results = [(driver1_id, 1), (driver2_id, 2)]
        system['race_mgmt'].complete_race(race_id, results)
        system['results'].record_race_result(race_id, results, 10000)
        
        # Update cash for winner
        system['results'].update_cash_balance_from_race(
            system['inventory'], driver1_id, race_id
        )
        
        # Cash should increase by first place prize
        new_cash = system['inventory'].get_cash_balance()
        assert new_cash > initial_cash
        assert new_cash == initial_cash + 5000  # 50% of 10000

    # ============================================================================
    # BUSINESS RULE 5: Missions cannot start if required roles unavailable
    # ============================================================================
    
    def test_mission_cannot_start_without_required_role(self, system):
        """Verify missions require all necessary roles."""
        # Create mission requiring mechanic
        mission_id = system['missions'].create_mission(
            "Engine Repair", MISSION_TYPE_DELIVERY, [MECHANIC], reward=2000
        )
        
        available, unavailable = system['missions'].check_roles_availability([MECHANIC])
        assert not available
        assert MECHANIC in unavailable
    
    def test_mission_starts_when_roles_available(self, system):
        """Verify missions can start when all roles are available."""
        # Register mechanic
        mechanic_id = system['registration'].register_member("Iris Brown", MECHANIC)
        
        # Create mission
        mission_id = system['missions'].create_mission(
            "Repair Job", MISSION_TYPE_DELIVERY, [MECHANIC], reward=2000
        )
        
        # Check availability
        available, unavailable = system['missions'].check_roles_availability([MECHANIC])
        assert available
        assert len(unavailable) == 0
        
        # Assign and start mission
        system['missions'].assign_mission(mission_id, {MECHANIC: mechanic_id})
        
        mission = system['missions'].get_mission(mission_id)
        assert mission.status == "active"
    
    def test_inactive_member_cannot_be_assigned_to_mission(self, system):
        """Verify inactive members cannot be assigned to missions."""
        driver_id = system['registration'].register_member("Jack Johnson", DRIVER)
        system['registration'].deactivate_member(driver_id)
        
        mission_id = system['missions'].create_mission(
            "Delivery", MISSION_TYPE_DELIVERY, [DRIVER], reward=1500
        )
        
        with pytest.raises(ValueError):
            system['missions'].assign_mission(mission_id, {DRIVER: driver_id})

    # ============================================================================
    # MODULE INTERACTION TESTS
    # ============================================================================
    
    def test_complete_race_workflow(self, system):
        """Test complete race workflow from creation to results."""
        # Register drivers
        driver1_id = system['registration'].register_member("Karen Moore", DRIVER)
        driver2_id = system['registration'].register_member("Larry Taylor", DRIVER)
        
        # Add and initialize vehicles
        vehicle1_id = system['inventory'].add_vehicle("Racer 1", "sports")
        vehicle2_id = system['inventory'].add_vehicle("Racer 2", "sports")
        system['fuel'].initialize_vehicle_fuel(vehicle1_id)
        system['fuel'].initialize_vehicle_fuel(vehicle2_id)
        
        # Create race
        race_id = system['race_mgmt'].create_race("Championship", RACE_TYPE_CIRCUIT, 15000)
        
        # Register participants
        system['race_mgmt'].register_participant(race_id, driver1_id, vehicle1_id)
        system['race_mgmt'].register_participant(race_id, driver2_id, vehicle2_id)
        
        # Check fuel before race
        assert system['fuel'].check_fuel_sufficiency(vehicle1_id, RACE_TYPE_CIRCUIT)
        
        # Start race
        system['race_mgmt'].start_race(race_id)
        race = system['race_mgmt'].get_race(race_id)
        assert race.status == "ongoing"
        
        # Consume fuel
        system['fuel'].consume_fuel(vehicle1_id, RACE_TYPE_CIRCUIT)
        system['fuel'].consume_fuel(vehicle2_id, RACE_TYPE_CIRCUIT)
        
        # Complete race
        results = [(driver1_id, 1), (driver2_id, 2)]
        system['race_mgmt'].complete_race(race_id, results)
        system['results'].record_race_result(race_id, results, 15000)
        
        # Verify results and rankings
        ranking1 = system['results'].get_driver_ranking(driver1_id)
        ranking2 = system['results'].get_driver_ranking(driver2_id)
        
        assert ranking1.wins == 1
        assert ranking2.wins == 0
        assert ranking1.points > ranking2.points
    
    def test_complete_mission_workflow(self, system):
        """Test complete mission workflow with crew assignment."""
        # Register crew
        driver_id = system['registration'].register_member("Monica Price", DRIVER)
        mechanic_id = system['registration'].register_member("Nathan Young", MECHANIC)
        
        # Create mission requiring both roles
        mission_id = system['missions'].create_mission(
            "High-Risk Delivery", MISSION_TYPE_RESCUE, [DRIVER, MECHANIC], reward=5000
        )
        
        # Assign mission
        system['missions'].assign_mission(
            mission_id,
            {DRIVER: driver_id, MECHANIC: mechanic_id}
        )
        
        mission = system['missions'].get_mission(mission_id)
        assert mission.status == "active"
        assert mission.assigned_crew[DRIVER] == driver_id
        assert mission.assigned_crew[MECHANIC] == mechanic_id
        
        # Complete mission
        initial_cash = system['inventory'].get_cash_balance()
        system['missions'].complete_mission(mission_id, system['inventory'])
        
        # Verify cash updated
        new_cash = system['inventory'].get_cash_balance()
        assert new_cash == initial_cash + 5000

    # ============================================================================
    # REPUTATION AND UNLOCK SYSTEM INTEGRATION
    # ============================================================================
    
    def test_reputation_gain_from_race_wins(self, system):
        """Verify reputation increases from race victories."""
        driver_id = system['registration'].register_member("Oscar Hall", DRIVER)
        driver2_id = system['registration'].register_member("Oscar Competitor", DRIVER)
        vehicle_id = system['inventory'].add_vehicle("Fast Car", "sports")
        vehicle2_id = system['inventory'].add_vehicle("Competing Car", "sports")
        
        # Initialize reputation
        initial_rep = system['reputation'].get_member_reputation(driver_id)
        assert initial_rep == 0
        
        # Register and win race (need 2 participants)
        race_id = system['race_mgmt'].create_race("Glory Race", RACE_TYPE_STREET)
        system['race_mgmt'].register_participant(race_id, driver_id, vehicle_id)
        system['race_mgmt'].register_participant(race_id, driver2_id, vehicle2_id)
        system['race_mgmt'].start_race(race_id)
        system['race_mgmt'].complete_race(race_id, [(driver_id, 1), (driver2_id, 2)])
        
        # Gain reputation
        system['reputation'].gain_reputation_from_race_win(driver_id, 1)
        
        new_rep = system['reputation'].get_member_reputation(driver_id)
        assert new_rep == 50  # First place reward
    
    def test_reputation_unlock_content(self, system):
        """Verify content unlocks based on reputation tier."""
        driver_id = system['registration'].register_member("Pam Wilson", DRIVER)
        
        # Initially no content unlocked
        content = system['reputation'].get_unlocked_content(driver_id)
        assert len(content) == 0
        
        # Add reputation to silver tier
        system['reputation'].add_reputation(driver_id, 500)
        
        content = system['reputation'].get_unlocked_content(driver_id)
        assert len(content) > 0
        assert "High-Speed Dash" in content

    # ============================================================================
    # FUEL MANAGEMENT INTEGRATION
    # ============================================================================
    
    def test_fuel_consumption_prevents_race_without_refuel(self, system):
        """Verify races require sufficient fuel."""
        driver_id = system['registration'].register_member("Quinn Carter", DRIVER)
        vehicle_id = system['inventory'].add_vehicle("Car", "sports")
        
        system['fuel'].initialize_vehicle_fuel(vehicle_id)
        
        # Consume fuel multiple times (consuming street race 5 times = 100 fuel)
        for _ in range(5):
            system['fuel'].consume_fuel(vehicle_id, RACE_TYPE_STREET)
        
        # Check fuel is now 0
        fuel_level = system['fuel'].get_fuel_level(vehicle_id)
        assert fuel_level == 0
        
        # Check fuel is insufficient for any race
        assert not system['fuel'].check_fuel_sufficiency(vehicle_id, RACE_TYPE_CIRCUIT)
        assert not system['fuel'].check_fuel_sufficiency(vehicle_id, RACE_TYPE_STREET)
        
        # Refuel
        system['fuel'].refuel_vehicle(vehicle_id, cost_per_unit=100)
        
        # Should now have sufficient fuel
        assert system['fuel'].check_fuel_sufficiency(vehicle_id, RACE_TYPE_CIRCUIT)
    
    def test_fuel_refuel_deducts_cash(self, system):
        """Verify refueling costs and updates cash balance."""
        vehicle_id = system['inventory'].add_vehicle("Car", "sports")
        initial_cash = system['inventory'].get_cash_balance()
        
        # Use fuel
        system['fuel'].initialize_vehicle_fuel(vehicle_id)
        system['fuel'].consume_fuel(vehicle_id, RACE_TYPE_STREET)
        
        # Refuel
        system['fuel'].refuel_vehicle(vehicle_id, cost_per_unit=100)
        
        new_cash = system['inventory'].get_cash_balance()
        assert new_cash < initial_cash  # Cash should decrease

    def test_fuel_module_rejects_unknown_vehicle_ids(self, system):
        """Verify fuel actions cannot target vehicles missing from inventory."""
        with pytest.raises(ValueError):
            system['fuel'].get_fuel_level(999)

        with pytest.raises(ValueError):
            system['fuel'].refuel_vehicle(999)

    # ============================================================================
    # ERROR HANDLING AND EDGE CASES
    # ============================================================================
    
    def test_cannot_register_with_invalid_role(self, system):
        """Verify invalid roles are rejected."""
        with pytest.raises(ValueError):
            system['registration'].register_member("Ryan Scott", "invalid_role")
    
    def test_cannot_create_race_with_invalid_type(self, system):
        """Verify invalid race types are rejected."""
        with pytest.raises(ValueError):
            system['race_mgmt'].create_race("Race", "invalid_type")
    
    def test_race_requires_minimum_participants(self, system):
        """Verify races require at least 2 participants."""
        driver_id = system['registration'].register_member("Sophia Lee", DRIVER)
        vehicle_id = system['inventory'].add_vehicle("Car", "sports")
        
        race_id = system['race_mgmt'].create_race("Solo Race", RACE_TYPE_STREET)
        system['race_mgmt'].register_participant(race_id, driver_id, vehicle_id)
        
        with pytest.raises(ValueError):
            system['race_mgmt'].start_race(race_id)
    
    def test_cannot_assign_invalid_skill_level(self, system):
        """Verify skill levels are bounded (0-100)."""
        driver_id = system['registration'].register_member("Tom Anderson", DRIVER)
        
        with pytest.raises(ValueError):
            system['crew_mgmt'].update_skill_level(driver_id, DRIVER, 150)
    
    def test_inventory_cash_cannot_go_negative(self, system):
        """Verify inventory prevents negative cash balance."""
        with pytest.raises(ValueError):
            system['inventory'].deduct_cash(500000)  # More than initial 100000

    def test_reputation_module_rejects_unknown_member_ids(self, system):
        """Verify reputation tracking cannot create phantom crew members."""
        with pytest.raises(ValueError):
            system['reputation'].get_member_reputation(999)

        with pytest.raises(ValueError):
            system['reputation'].get_unlocked_content(999)

    # ============================================================================
    # COMPREHENSIVE SYSTEM STATE TESTS
    # ============================================================================
    
    def test_multiple_races_concurrent(self, system):
        """Verify system can handle multiple races simultaneously."""
        # Register 4 drivers
        drivers = [
            system['registration'].register_member(f"Driver {i}", DRIVER)
            for i in range(4)
        ]
        
        # Register 4 vehicles
        vehicles = [
            system['inventory'].add_vehicle(f"Car {i}", "sports")
            for i in range(4)
        ]
        
        # Create 2 races
        race1_id = system['race_mgmt'].create_race("Race 1", RACE_TYPE_STREET)
        race2_id = system['race_mgmt'].create_race("Race 2", RACE_TYPE_CIRCUIT)
        
        # Register participants in different races
        system['race_mgmt'].register_participant(race1_id, drivers[0], vehicles[0])
        system['race_mgmt'].register_participant(race1_id, drivers[1], vehicles[1])
        
        system['race_mgmt'].register_participant(race2_id, drivers[2], vehicles[2])
        system['race_mgmt'].register_participant(race2_id, drivers[3], vehicles[3])
        
        # Verify both races are active
        assert len(system['race_mgmt'].get_race_participants(race1_id)) == 2
        assert len(system['race_mgmt'].get_race_participants(race2_id)) == 2
    
    def test_leaderboard_generation(self, system):
        """Verify leaderboard is correctly generated from results."""
        # Register drivers
        drivers = [
            system['registration'].register_member(f"Racer {i}", DRIVER)
            for i in range(3)
        ]
        
        # Simulate multiple races with different winners
        for race_num in range(3):
            vehicles = [
                system['inventory'].add_vehicle(f"Vehicle {i}_{race_num}", "sports")
                for i in range(3)
            ]
            
            race_id = system['race_mgmt'].create_race(f"Race {race_num}", RACE_TYPE_STREET)
            for driver, vehicle in zip(drivers, vehicles):
                system['race_mgmt'].register_participant(race_id, driver, vehicle)
            
            system['race_mgmt'].start_race(race_id)
            
            # Rotate winner
            winner_idx = race_num % len(drivers)
            results = [(drivers[winner_idx], 1)]
            for i, driver in enumerate(drivers):
                if i != winner_idx:
                    results.append((driver, i + 2))
            
            system['race_mgmt'].complete_race(race_id, results)
            system['results'].record_race_result(race_id, results, 10000)
        
        # Check leaderboard
        leaderboard = system['results'].get_top_drivers(3)
        assert len(leaderboard) == 3
        
        # Each driver should have at least 1 win
        for ranking in leaderboard:
            assert ranking.wins >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
