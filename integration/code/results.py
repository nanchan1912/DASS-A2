# Results Module - Records race outcomes, rankings, and prize distribution

from config import RACE_PRIZE_FIRST, RACE_PRIZE_SECOND, RACE_PRIZE_THIRD


class RaceResult:
    """Represents the result of a race."""
    
    def __init__(self, race_id, results_list):
        """
        Initialize race result.
        
        Args:
            race_id: ID of the race
            results_list: List of (driver_id, position) tuples
        """
        self.race_id = race_id
        self.results = results_list
        self.prize_distribution = {}
    
    def calculate_prizes(self, prize_pool):
        """Calculate prize distribution for race."""
        prizes = {
            1: int(prize_pool * 0.5),  # 50% to first
            2: int(prize_pool * 0.3),  # 30% to second
            3: int(prize_pool * 0.2),  # 20% to third
        }
        
        for driver_id, position in self.results:
            if position in prizes:
                self.prize_distribution[driver_id] = prizes[position]
            else:
                self.prize_distribution[driver_id] = 0
    
    def get_prize_for_driver(self, driver_id):
        """Get prize for a driver."""
        return self.prize_distribution.get(driver_id, 0)


class Ranking:
    """Represents a driver's ranking."""
    
    def __init__(self, driver_id, driver_name):
        """
        Initialize ranking.
        
        Args:
            driver_id: ID of the driver
            driver_name: Name of the driver
        """
        self.driver_id = driver_id
        self.driver_name = driver_name
        self.races_completed = 0
        self.wins = 0
        self.total_prize_money = 0
        self.points = 0
    
    def add_race(self, position, prize_money):
        """Update ranking with race result."""
        self.races_completed += 1
        if position == 1:
            self.wins += 1
            self.points += 10
        elif position == 2:
            self.points += 6
        elif position == 3:
            self.points += 3
        else:
            self.points += 1
        
        self.total_prize_money += prize_money
    
    def __repr__(self):
        return f"Ranking(driver={self.driver_name}, races={self.races_completed}, wins={self.wins}, points={self.points}, prize={self.total_prize_money})"


class ResultsModule:
    """Manages race results and rankings."""
    
    def __init__(self, crew_management):
        """
        Initialize results module.
        
        Args:
            crew_management: CrewManagementModule instance
        """
        self.crew_management = crew_management
        self.race_results = {}  # race_id -> RaceResult
        self.rankings = {}  # driver_id -> Ranking
    
    def record_race_result(self, race_id, results_list, prize_pool):
        """
        Record results for a completed race.
        
        Args:
            race_id: ID of the race
            results_list: List of (driver_id, position) tuples in order
            prize_pool: Total prize money for race
        """
        # Create race result
        race_result = RaceResult(race_id, results_list)
        race_result.calculate_prizes(prize_pool)
        self.race_results[race_id] = race_result
        
        # Update rankings
        for driver_id, position in results_list:
            if driver_id not in self.rankings:
                # Get driver name from crew management
                member = self.crew_management.registration.get_member(driver_id)
                if member:
                    self.rankings[driver_id] = Ranking(driver_id, member.name)
                else:
                    self.rankings[driver_id] = Ranking(driver_id, f"Driver {driver_id}")
            
            prize = race_result.get_prize_for_driver(driver_id)
            self.rankings[driver_id].add_race(position, prize)
    
    def get_race_result(self, race_id):
        """Get result for a specific race."""
        return self.race_results.get(race_id)
    
    def get_driver_ranking(self, driver_id):
        """Get ranking for a specific driver."""
        return self.rankings.get(driver_id)
    
    def get_all_rankings(self):
        """Get all driver rankings."""
        # Sort by points (descending), then by wins (descending)
        sorted_rankings = sorted(
            self.rankings.values(),
            key=lambda r: (-r.points, -r.wins)
        )
        return sorted_rankings
    
    def get_top_drivers(self, count=5):
        """Get top N drivers by points."""
        all_rankings = self.get_all_rankings()
        return all_rankings[:count]
    
    def get_driver_stats(self, driver_id):
        """Get detailed stats for a driver."""
        ranking = self.get_driver_ranking(driver_id)
        if not ranking:
            return None
        
        return {
            "driver_id": driver_id,
            "driver_name": ranking.driver_name,
            "races_completed": ranking.races_completed,
            "wins": ranking.wins,
            "points": ranking.points,
            "total_prize_money": ranking.total_prize_money,
            "win_rate": (ranking.wins / ranking.races_completed * 100) if ranking.races_completed > 0 else 0
        }
    
    def update_cash_balance_from_race(self, inventory, driver_id, race_id):
        """
        Update inventory cash balance with race prize.
        
        Args:
            inventory: InventoryModule instance
            driver_id: Driver who won prize
            race_id: Race ID
        """
        race_result = self.get_race_result(race_id)
        if not race_result:
            raise ValueError(f"Race result {race_id} not found")
        
        prize = race_result.get_prize_for_driver(driver_id)
        if prize > 0:
            inventory.add_cash(prize)
