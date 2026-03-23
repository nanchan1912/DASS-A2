"""Command-line entry point for running a MoneyPoly game."""

from moneypoly.game import Game


def get_player_names():
    """Read and return cleaned player names from input."""
    print("Enter player names separated by commas (minimum 2 players):")
    raw = input("> ").strip()
    names = [n.strip() for n in raw.split(",") if n.strip()]
    if len(names) < 2:
        raise ValueError("At least two players are required.")
    return names


def main():
    """Create and run the game, handling setup and interrupts."""
    names = get_player_names()
    try:
        game = Game(names)
        game.run()
    except KeyboardInterrupt:
        print("\n\n  Game interrupted. Goodbye!")
    except ValueError as exc:
        print(f"Setup error: {exc}")


if __name__ == "__main__":
    main()
