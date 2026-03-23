"""White-box tests for complete MoneyPoly code paths and edge cases."""

import unittest
from unittest.mock import MagicMock, patch

import main as app_main
from moneypoly import config, ui
from moneypoly.bank import Bank
from moneypoly.board import Board, SPECIAL_TILES
from moneypoly.cards import CardDeck
from moneypoly.dice import Dice
from moneypoly.game import Game
from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup


class TestConfigSanity(unittest.TestCase):
    """Sanity checks for global constants used by game logic."""

    def test_core_config_values_are_sensible(self):
        self.assertGreater(config.STARTING_BALANCE, 0)
        self.assertGreater(config.GO_SALARY, 0)
        self.assertGreater(config.BOARD_SIZE, 0)
        self.assertGreater(config.MAX_TURNS, 0)
        self.assertGreater(config.BANK_STARTING_FUNDS, 0)


class TestBankWhiteBox(unittest.TestCase):
    """Branch and state tests for Bank."""

    def test_collect_increases_funds_and_totals(self):
        bank = Bank()
        start = bank.get_balance()
        bank.collect(100)
        self.assertEqual(bank.get_balance(), start + 100)
        self.assertEqual(bank._total_collected, 100)

    def test_collect_negative_amount_is_ignored(self):
        bank = Bank()
        start = bank.get_balance()
        bank.collect(-50)
        self.assertEqual(bank.get_balance(), start)
        self.assertEqual(bank._total_collected, 0)

    def test_pay_out_non_positive_returns_zero(self):
        bank = Bank()
        self.assertEqual(bank.pay_out(0), 0)
        self.assertEqual(bank.pay_out(-5), 0)

    def test_pay_out_raises_when_insufficient_funds(self):
        bank = Bank()
        with self.assertRaises(ValueError):
            bank.pay_out(bank.get_balance() + 1)

    def test_pay_out_success_path(self):
        bank = Bank()
        start = bank.get_balance()
        paid = bank.pay_out(50)
        self.assertEqual(paid, 50)
        self.assertEqual(bank.get_balance(), start - 50)

    def test_give_loan_zero_or_negative_no_effect(self):
        bank = Bank()
        player = Player("P")
        player_start = player.balance
        bank.give_loan(player, 0)
        bank.give_loan(player, -10)
        self.assertEqual(player.balance, player_start)
        self.assertEqual(bank.loan_count(), 0)

    def test_give_loan_positive_tracks_loan(self):
        bank = Bank()
        player = Player("P")
        with patch("builtins.print"):
            bank.give_loan(player, 125)
        self.assertEqual(bank.loan_count(), 1)
        self.assertEqual(bank.total_loans_issued(), 125)
        self.assertEqual(player.balance, config.STARTING_BALANCE + 125)

    def test_summary_and_repr_paths(self):
        bank = Bank()
        with patch("builtins.print") as mock_print:
            bank.summary()
        self.assertEqual(mock_print.call_count, 3)
        self.assertIn("Bank(funds=", repr(bank))


class TestCardsWhiteBox(unittest.TestCase):
    """Branch and edge tests for CardDeck."""

    def test_draw_empty_returns_none(self):
        deck = CardDeck([])
        self.assertIsNone(deck.draw())

    def test_draw_cycles_through_cards(self):
        deck = CardDeck([{"x": 1}, {"x": 2}])
        self.assertEqual(deck.draw()["x"], 1)
        self.assertEqual(deck.draw()["x"], 2)
        self.assertEqual(deck.draw()["x"], 1)

    def test_peek_empty_returns_none(self):
        deck = CardDeck([])
        self.assertIsNone(deck.peek())

    def test_peek_non_empty_does_not_advance(self):
        deck = CardDeck([{"x": 1}, {"x": 2}])
        self.assertEqual(deck.peek()["x"], 1)
        self.assertEqual(deck.peek()["x"], 1)
        self.assertEqual(deck.index, 0)

    def test_reshuffle_calls_shuffle_and_resets_index(self):
        deck = CardDeck([{"x": 1}, {"x": 2}])
        deck.index = 5
        with patch("moneypoly.cards.random.shuffle") as mock_shuffle:
            deck.reshuffle()
        mock_shuffle.assert_called_once_with(deck.cards)
        self.assertEqual(deck.index, 0)

    def test_cards_remaining_non_empty(self):
        deck = CardDeck([{"x": 1}, {"x": 2}, {"x": 3}])
        deck.draw()
        self.assertEqual(deck.cards_remaining(), 2)

    def test_cards_remaining_empty_returns_zero(self):
        deck = CardDeck([])
        self.assertEqual(deck.cards_remaining(), 0)

    def test_repr_empty_deck_safe(self):
        deck = CardDeck([])
        self.assertIn("CardDeck(0 cards", repr(deck))


class TestDiceWhiteBox(unittest.TestCase):
    """Branch/state tests for Dice including edge constraints."""

    def test_reset_zeroes_values_and_streak(self):
        dice = Dice()
        dice.die1 = 3
        dice.die2 = 4
        dice.doubles_streak = 2
        dice.reset()
        self.assertEqual((dice.die1, dice.die2, dice.doubles_streak), (0, 0, 0))

    def test_roll_doubles_increments_streak_and_total(self):
        dice = Dice()
        with patch("moneypoly.dice.random.randint", side_effect=[4, 4]):
            total = dice.roll()
        self.assertEqual(total, 8)
        self.assertTrue(dice.is_doubles())
        self.assertEqual(dice.doubles_streak, 1)

    def test_roll_non_doubles_resets_streak(self):
        dice = Dice()
        dice.doubles_streak = 2
        with patch("moneypoly.dice.random.randint", side_effect=[2, 5]):
            total = dice.roll()
        self.assertEqual(total, 7)
        self.assertFalse(dice.is_doubles())
        self.assertEqual(dice.doubles_streak, 0)

    def test_roll_uses_full_six_sided_range(self):
        dice = Dice()
        with patch("moneypoly.dice.random.randint", side_effect=[1, 6]) as mock_rand:
            dice.roll()
        self.assertEqual(mock_rand.call_args_list[0].args, (1, 6))
        self.assertEqual(mock_rand.call_args_list[1].args, (1, 6))

    def test_describe_branch_with_and_without_doubles(self):
        dice = Dice()
        dice.die1 = 2
        dice.die2 = 2
        self.assertIn("(DOUBLES)", dice.describe())
        dice.die2 = 3
        self.assertNotIn("(DOUBLES)", dice.describe())


class TestPlayerWhiteBox(unittest.TestCase):
    """Branch/state tests for Player."""

    def test_add_money_negative_raises(self):
        p = Player("P")
        with self.assertRaises(ValueError):
            p.add_money(-1)

    def test_add_money_success(self):
        p = Player("P")
        p.add_money(25)
        self.assertEqual(p.balance, config.STARTING_BALANCE + 25)

    def test_deduct_money_negative_raises(self):
        p = Player("P")
        with self.assertRaises(ValueError):
            p.deduct_money(-1)

    def test_deduct_money_success_and_bankrupt_state(self):
        p = Player("P", balance=10)
        p.deduct_money(10)
        self.assertTrue(p.is_bankrupt())

    def test_move_lands_on_go_collects_salary(self):
        p = Player("P")
        p.position = config.BOARD_SIZE - 3
        start = p.balance
        with patch("builtins.print"):
            new_pos = p.move(3)
        self.assertEqual(new_pos, 0)
        self.assertEqual(p.balance, start + config.GO_SALARY)

    def test_move_non_go_path_no_salary(self):
        p = Player("P")
        start = p.balance
        p.move(5)
        self.assertEqual(p.position, 5)
        self.assertEqual(p.balance, start)

    def test_go_to_jail_sets_jail_state(self):
        p = Player("P")
        p.go_to_jail()
        self.assertEqual(p.position, config.JAIL_POSITION)
        self.assertTrue(p.in_jail)
        self.assertEqual(p.jail_turns, 0)

    def test_add_remove_property_and_count(self):
        p = Player("P")
        prop = Property("A", 1, 60, 2)
        p.add_property(prop)
        p.add_property(prop)
        self.assertEqual(p.count_properties(), 1)
        p.remove_property(prop)
        self.assertEqual(p.count_properties(), 0)

    def test_status_line_with_and_without_jail_tag(self):
        p = Player("P")
        self.assertNotIn("[JAILED]", p.status_line())
        p.in_jail = True
        self.assertIn("[JAILED]", p.status_line())


class TestPropertyAndGroupWhiteBox(unittest.TestCase):
    """Branch/state tests for Property and PropertyGroup."""

    def test_property_get_rent_mortgaged_returns_zero(self):
        prop = Property("A", 1, 100, 10)
        prop.is_mortgaged = True
        self.assertEqual(prop.get_rent(), 0)

    def test_property_get_rent_full_group_doubles(self):
        owner = Player("Owner")
        group = PropertyGroup("Brown", "brown")
        p1 = Property("A", 1, 60, 2)
        p2 = Property("B", 3, 60, 4)
        group.add_property(p1)
        group.add_property(p2)
        p1.owner = owner
        p2.owner = owner
        self.assertEqual(p1.get_rent(), 4)

    def test_property_get_rent_base_case(self):
        prop = Property("A", 1, 100, 10)
        self.assertEqual(prop.get_rent(), 10)

    def test_mortgage_and_unmortgage_paths(self):
        prop = Property("A", 1, 100, 10)
        self.assertEqual(prop.mortgage(), 50)
        self.assertEqual(prop.mortgage(), 0)
        self.assertEqual(prop.unmortgage(), 55)
        self.assertEqual(prop.unmortgage(), 0)

    def test_is_available_paths(self):
        prop = Property("A", 1, 100, 10)
        self.assertTrue(prop.is_available())
        prop.owner = Player("P")
        self.assertFalse(prop.is_available())
        prop.owner = None
        prop.is_mortgaged = True
        self.assertFalse(prop.is_available())

    def test_group_add_property_no_duplicates_sets_backlink(self):
        group = PropertyGroup("Brown", "brown")
        prop = Property("A", 1, 100, 10)
        group.add_property(prop)
        group.add_property(prop)
        self.assertEqual(group.size(), 1)
        self.assertIs(prop.group, group)

    def test_group_all_owned_by_paths(self):
        group = PropertyGroup("Brown", "brown")
        p1 = Property("A", 1, 100, 10)
        p2 = Property("B", 3, 120, 12)
        group.add_property(p1)
        group.add_property(p2)
        owner = Player("Owner")
        p1.owner = owner
        self.assertFalse(group.all_owned_by(owner))
        p2.owner = owner
        self.assertTrue(group.all_owned_by(owner))
        self.assertFalse(group.all_owned_by(None))

    def test_group_owner_counts_and_repr(self):
        group = PropertyGroup("Brown", "brown")
        a = Player("A")
        b = Player("B")
        p1 = Property("A", 1, 100, 10)
        p2 = Property("B", 3, 120, 12)
        p3 = Property("C", 5, 140, 14)
        for p in (p1, p2, p3):
            group.add_property(p)
        p1.owner = a
        p2.owner = a
        p3.owner = b
        counts = group.get_owner_counts()
        self.assertEqual(counts[a], 2)
        self.assertEqual(counts[b], 1)
        self.assertIn("PropertyGroup", repr(group))


class TestBoardWhiteBox(unittest.TestCase):
    """Branch/state tests for Board APIs."""

    def test_board_has_expected_group_and_property_counts(self):
        board = Board()
        self.assertEqual(len(board.groups), 8)
        self.assertEqual(len(board.properties), 22)

    def test_get_property_at_found_and_not_found(self):
        board = Board()
        self.assertIsNotNone(board.get_property_at(1))
        self.assertIsNone(board.get_property_at(0))

    def test_get_tile_type_paths(self):
        board = Board()
        special_pos = next(iter(SPECIAL_TILES.keys()))
        self.assertEqual(board.get_tile_type(special_pos), SPECIAL_TILES[special_pos])
        self.assertEqual(board.get_tile_type(1), "property")
        self.assertEqual(board.get_tile_type(12), "blank")

    def test_is_purchasable_paths(self):
        board = Board()
        self.assertFalse(board.is_purchasable(0))

        prop = board.get_property_at(1)
        self.assertTrue(board.is_purchasable(1))

        prop.is_mortgaged = True
        self.assertFalse(board.is_purchasable(1))

        prop.is_mortgaged = False
        prop.owner = Player("Owner")
        self.assertFalse(board.is_purchasable(1))

    def test_is_special_tile_paths(self):
        board = Board()
        self.assertTrue(board.is_special_tile(0))
        self.assertFalse(board.is_special_tile(1))

    def test_properties_owned_by_and_unowned(self):
        board = Board()
        owner = Player("Owner")
        p1 = board.get_property_at(1)
        p2 = board.get_property_at(3)
        p1.owner = owner
        p2.owner = owner

        owned = board.properties_owned_by(owner)
        unowned = board.unowned_properties()
        self.assertIn(p1, owned)
        self.assertIn(p2, owned)
        self.assertNotIn(p1, unowned)

    def test_board_repr(self):
        board = Board()
        self.assertIn("Board(22 properties", repr(board))


class TestUiWhiteBox(unittest.TestCase):
    """Branch/state tests for UI helper functions."""

    def test_print_banner_calls_print(self):
        with patch("builtins.print") as mock_print:
            ui.print_banner("X")
        self.assertGreaterEqual(mock_print.call_count, 3)

    def test_print_player_card_branches(self):
        p = Player("P")
        with patch("builtins.print") as mock_print:
            ui.print_player_card(p)
        self.assertTrue(any("Properties: none" in str(c) for c in mock_print.call_args_list))

        prop = Property("A", 1, 100, 10)
        p.add_property(prop)
        p.in_jail = True
        p.jail_turns = 1
        p.get_out_of_jail_cards = 1
        with patch("builtins.print") as mock_print:
            ui.print_player_card(p)
        self.assertGreater(mock_print.call_count, 5)

    def test_print_standings_sorts_descending_net_worth(self):
        p1 = Player("A", 10)
        p2 = Player("B", 100)
        with patch("builtins.print") as mock_print:
            ui.print_standings([p1, p2])
        lines = "\n".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("1. B", lines)

    def test_print_board_ownership_marks_mortgaged(self):
        board = Board()
        prop = board.get_property_at(1)
        prop.is_mortgaged = True
        with patch("builtins.print") as mock_print:
            ui.print_board_ownership(board)
        lines = "\n".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("(* = mortgaged)", lines)

    def test_format_currency(self):
        self.assertEqual(ui.format_currency(1500), "$1,500")

    def test_safe_int_input_valid_and_invalid(self):
        with patch("builtins.input", return_value="42"):
            self.assertEqual(ui.safe_int_input("x"), 42)
        with patch("builtins.input", return_value="nope"):
            self.assertEqual(ui.safe_int_input("x", default=7), 7)

    def test_confirm_yes_and_no_paths(self):
        with patch("builtins.input", return_value=" y "):
            self.assertTrue(ui.confirm("x"))
        with patch("builtins.input", return_value="n"):
            self.assertFalse(ui.confirm("x"))


class TestGameWhiteBox(unittest.TestCase):
    """Branch/state tests for game flow and decisions."""

    def setUp(self):
        self.game = Game(["A", "B", "C"])

    def test_current_player_and_advance_turn_wrap(self):
        self.assertEqual(self.game.current_player().name, "A")
        self.game.advance_turn()
        self.assertEqual(self.game.current_player().name, "B")
        self.game._turn_state["current_index"] = 2
        self.game.advance_turn()
        self.assertEqual(self.game.current_index, 0)

    def test_play_turn_jail_branch(self):
        player = self.game.current_player()
        player.in_jail = True
        with patch.object(self.game, "_handle_jail_turn") as h_jail, patch.object(
            self.game, "advance_turn"
        ) as adv:
            self.game.play_turn()
        h_jail.assert_called_once_with(player)
        adv.assert_called_once()

    def test_play_turn_three_doubles_goes_to_jail(self):
        player = self.game.current_player()
        self.game.dice.roll = MagicMock(return_value=4)
        self.game.dice.describe = MagicMock(return_value="2 + 2 = 4")
        self.game.dice.doubles_streak = 3
        with patch.object(player, "go_to_jail") as to_jail, patch.object(
            self.game, "advance_turn"
        ) as adv:
            self.game.play_turn()
        to_jail.assert_called_once()
        adv.assert_called_once()

    def test_play_turn_doubles_grants_extra_turn(self):
        self.game.dice.roll = MagicMock(return_value=4)
        self.game.dice.describe = MagicMock(return_value="2 + 2 = 4")
        self.game.dice.doubles_streak = 0
        self.game.dice.is_doubles = MagicMock(return_value=True)
        with patch.object(self.game, "_move_and_resolve") as mmr, patch.object(
            self.game, "advance_turn"
        ) as adv:
            self.game.play_turn()
        mmr.assert_called_once()
        adv.assert_not_called()

    def test_play_turn_normal_advances(self):
        self.game.dice.roll = MagicMock(return_value=5)
        self.game.dice.describe = MagicMock(return_value="2 + 3 = 5")
        self.game.dice.doubles_streak = 0
        self.game.dice.is_doubles = MagicMock(return_value=False)
        with patch.object(self.game, "_move_and_resolve") as mmr, patch.object(
            self.game, "advance_turn"
        ) as adv:
            self.game.play_turn()
        mmr.assert_called_once()
        adv.assert_called_once()

    def test_move_and_resolve_go_to_jail_branch(self):
        player = self.game.current_player()
        with patch.object(player, "move") as move, patch.object(
            self.game.board, "get_tile_type", return_value="go_to_jail"
        ), patch.object(player, "go_to_jail") as to_jail, patch.object(
            self.game, "_check_bankruptcy"
        ) as chk:
            player.position = 30
            self.game._move_and_resolve(player, 3)
        move.assert_called_once_with(3)
        to_jail.assert_called_once()
        chk.assert_called_once_with(player)

    def test_move_and_resolve_income_and_luxury_tax_branches(self):
        player = self.game.current_player()
        with patch.object(player, "move"), patch.object(
            self.game.board, "get_tile_type", return_value="income_tax"
        ), patch.object(player, "deduct_money") as deduct, patch.object(
            self.game.bank, "collect"
        ) as collect, patch.object(self.game, "_check_bankruptcy"):
            self.game._move_and_resolve(player, 1)
        deduct.assert_called_with(config.INCOME_TAX_AMOUNT)
        collect.assert_called_with(config.INCOME_TAX_AMOUNT)

        with patch.object(player, "move"), patch.object(
            self.game.board, "get_tile_type", return_value="luxury_tax"
        ), patch.object(player, "deduct_money") as deduct, patch.object(
            self.game.bank, "collect"
        ) as collect, patch.object(self.game, "_check_bankruptcy"):
            self.game._move_and_resolve(player, 1)
        deduct.assert_called_with(config.LUXURY_TAX_AMOUNT)
        collect.assert_called_with(config.LUXURY_TAX_AMOUNT)

    def test_move_and_resolve_card_branches(self):
        player = self.game.current_player()
        card = {"description": "x", "action": "collect", "value": 10}
        with patch.object(player, "move"), patch.object(
            self.game.board, "get_tile_type", return_value="chance"
        ), patch.object(self.game.chance_deck, "draw", return_value=card), patch.object(
            self.game, "_apply_card"
        ) as apply_card, patch.object(self.game, "_check_bankruptcy"):
            self.game._move_and_resolve(player, 2)
        apply_card.assert_called_with(player, card)

        with patch.object(player, "move"), patch.object(
            self.game.board, "get_tile_type", return_value="community_chest"
        ), patch.object(self.game.community_deck, "draw", return_value=card), patch.object(
            self.game, "_apply_card"
        ) as apply_card, patch.object(self.game, "_check_bankruptcy"):
            self.game._move_and_resolve(player, 2)
        apply_card.assert_called_with(player, card)

    def test_move_and_resolve_property_and_railroad_branches(self):
        player = self.game.current_player()
        prop = Property("R", 5, 200, 25)

        with patch.object(player, "move"), patch.object(
            self.game.board, "get_tile_type", return_value="railroad"
        ), patch.object(self.game.board, "get_property_at", return_value=prop), patch.object(
            self.game, "_handle_property_tile"
        ) as hp, patch.object(self.game, "_check_bankruptcy"):
            self.game._move_and_resolve(player, 4)
        hp.assert_called_with(player, prop)

        with patch.object(player, "move"), patch.object(
            self.game.board, "get_tile_type", return_value="property"
        ), patch.object(self.game.board, "get_property_at", return_value=prop), patch.object(
            self.game, "_handle_property_tile"
        ) as hp, patch.object(self.game, "_check_bankruptcy"):
            self.game._move_and_resolve(player, 4)
        hp.assert_called_with(player, prop)

    def test_handle_property_tile_paths(self):
        player = self.game.current_player()
        prop = Property("P", 1, 100, 10)

        with patch("builtins.input", return_value="b"), patch.object(
            self.game, "buy_property"
        ) as buy:
            self.game._handle_property_tile(player, prop)
        buy.assert_called_once_with(player, prop)

        with patch("builtins.input", return_value="a"), patch.object(
            self.game, "auction_property"
        ) as auc:
            self.game._handle_property_tile(player, prop)
        auc.assert_called_once_with(prop)

        with patch("builtins.input", return_value="s"), patch("builtins.print") as mock_print:
            self.game._handle_property_tile(player, prop)
        self.assertTrue(any("passes on" in str(c) for c in mock_print.call_args_list))

        prop.owner = player
        with patch("builtins.print") as mock_print:
            self.game._handle_property_tile(player, prop)
        self.assertTrue(any("No rent due" in str(c) for c in mock_print.call_args_list))

        other = self.game.players[1]
        prop.owner = other
        with patch.object(self.game, "pay_rent") as pr:
            self.game._handle_property_tile(player, prop)
        pr.assert_called_once_with(player, prop)

    def test_buy_property_success_and_fail_paths(self):
        player = self.game.current_player()
        prop = Property("P", 1, 100, 10)
        player.balance = 150
        with patch("builtins.print"):
            self.assertTrue(self.game.buy_property(player, prop))
        self.assertIs(prop.owner, player)
        self.assertIn(prop, player.properties)

        poor = self.game.players[1]
        poor.balance = 50
        prop2 = Property("Q", 3, 100, 10)
        with patch("builtins.print"):
            self.assertFalse(self.game.buy_property(poor, prop2))

    def test_buy_property_allows_exact_balance(self):
        player = self.game.current_player()
        prop = Property("Exact", 9, 100, 12)
        player.balance = 100
        with patch("builtins.print"):
            self.assertTrue(self.game.buy_property(player, prop))

    def test_pay_rent_paths(self):
        tenant = self.game.current_player()
        owner = self.game.players[1]
        prop = Property("P", 1, 100, 10)

        prop.is_mortgaged = True
        with patch("builtins.print") as mock_print:
            self.game.pay_rent(tenant, prop)
        self.assertTrue(any("no rent" in str(c).lower() for c in mock_print.call_args_list))

        prop.is_mortgaged = False
        prop.owner = None
        tenant_start = tenant.balance
        self.game.pay_rent(tenant, prop)
        self.assertEqual(tenant.balance, tenant_start)

        prop.owner = owner
        owner_start = owner.balance
        tenant.balance = 100
        self.game.pay_rent(tenant, prop)
        self.assertEqual(tenant.balance, 90)
        self.assertEqual(owner.balance, owner_start + 10)

    def test_mortgage_property_paths(self):
        player = self.game.current_player()
        other = self.game.players[1]
        prop = Property("P", 1, 100, 10)
        prop.owner = other
        with patch("builtins.print"):
            self.assertFalse(self.game.mortgage_property(player, prop))

        prop.owner = player
        prop.is_mortgaged = True
        with patch("builtins.print"):
            self.assertFalse(self.game.mortgage_property(player, prop))

        prop.is_mortgaged = False
        start = player.balance
        with patch("builtins.print"):
            self.assertTrue(self.game.mortgage_property(player, prop))
        self.assertEqual(player.balance, start + prop.mortgage_value)

    def test_unmortgage_property_paths(self):
        player = self.game.current_player()
        other = self.game.players[1]
        prop = Property("P", 1, 100, 10)
        prop.owner = other
        with patch("builtins.print"):
            self.assertFalse(self.game.unmortgage_property(player, prop))

        prop.owner = player
        prop.is_mortgaged = False
        with patch("builtins.print"):
            self.assertFalse(self.game.unmortgage_property(player, prop))

        prop.is_mortgaged = True
        player.balance = 10
        with patch("builtins.print"):
            self.assertFalse(self.game.unmortgage_property(player, prop))

        prop.is_mortgaged = True
        player.balance = 1000
        with patch("builtins.print"):
            self.assertTrue(self.game.unmortgage_property(player, prop))

    def test_trade_paths(self):
        seller = self.game.current_player()
        buyer = self.game.players[1]
        prop = Property("P", 1, 100, 10)

        prop.owner = buyer
        with patch("builtins.print"):
            self.assertFalse(self.game.trade(seller, buyer, prop, 10))

        prop.owner = seller
        seller.add_property(prop)
        buyer.balance = 5
        with patch("builtins.print"):
            self.assertFalse(self.game.trade(seller, buyer, prop, 10))

        buyer.balance = 100
        seller_count = len(seller.properties)
        with patch("builtins.print"):
            self.assertTrue(self.game.trade(seller, buyer, prop, 20))
        self.assertEqual(len(seller.properties), seller_count - 1)
        self.assertIn(prop, buyer.properties)

    def test_auction_property_no_bids_and_winner(self):
        prop = Property("Auction", 11, 120, 12)

        with patch("moneypoly.ui.safe_int_input", side_effect=[0, 0, 0]), patch(
            "builtins.print"
        ) as mock_print:
            self.game.auction_property(prop)
        self.assertIsNone(prop.owner)
        self.assertTrue(any("No bids" in str(c) for c in mock_print.call_args_list))

        p1, p2, p3 = self.game.players
        p1.balance = 100
        p2.balance = 100
        p3.balance = 100
        prop2 = Property("Auction2", 12, 130, 13)
        with patch("moneypoly.ui.safe_int_input", side_effect=[5, 150, 20]), patch(
            "builtins.print"
        ):
            self.game.auction_property(prop2)
        self.assertIs(prop2.owner, p3)
        self.assertIn(prop2, p3.properties)
        self.assertEqual(p3.balance, 80)

    def test_handle_jail_turn_paths(self):
        player = self.game.current_player()
        player.in_jail = True
        player.get_out_of_jail_cards = 1
        self.game.dice.roll = MagicMock(return_value=4)
        self.game.dice.describe = MagicMock(return_value="2 + 2 = 4")

        with patch("moneypoly.ui.confirm", side_effect=[True]), patch.object(
            self.game, "_move_and_resolve"
        ) as mmr:
            self.game._handle_jail_turn(player)
        self.assertFalse(player.in_jail)
        self.assertEqual(player.get_out_of_jail_cards, 0)
        mmr.assert_called_once()

        player.in_jail = True
        player.jail_turns = 0
        player.get_out_of_jail_cards = 0
        with patch("moneypoly.ui.confirm", side_effect=[True]), patch.object(
            self.game, "_move_and_resolve"
        ) as mmr:
            self.game._handle_jail_turn(player)
        self.assertFalse(player.in_jail)
        mmr.assert_called_once()

        player.in_jail = True
        player.jail_turns = 1
        with patch("moneypoly.ui.confirm", side_effect=[False]), patch.object(
            self.game, "_move_and_resolve"
        ) as mmr:
            self.game._handle_jail_turn(player)
        self.assertEqual(player.jail_turns, 2)
        mmr.assert_not_called()

        player.in_jail = True
        player.jail_turns = 2
        with patch("moneypoly.ui.confirm", side_effect=[False]), patch.object(
            self.game, "_move_and_resolve"
        ) as mmr:
            self.game._handle_jail_turn(player)
        self.assertFalse(player.in_jail)
        self.assertEqual(player.jail_turns, 0)
        mmr.assert_called_once()

    def test_apply_card_dispatch_paths(self):
        player = self.game.current_player()
        self.game._apply_card(player, None)

        with patch.object(self.game, "_card_collect") as h:
            self.game._apply_card(player, {"description": "x", "action": "collect", "value": 5})
        h.assert_called_once_with(player, 5)

        with patch.object(self.game, "_card_pay") as h:
            self.game._apply_card(player, {"description": "x", "action": "pay", "value": 5})
        h.assert_called_once_with(player, 5)

        with patch.object(self.game, "_card_jail") as h:
            self.game._apply_card(player, {"description": "x", "action": "jail", "value": 0})
        h.assert_called_once_with(player, 0)

        with patch.object(self.game, "_card_jail_free") as h:
            self.game._apply_card(player, {"description": "x", "action": "jail_free", "value": 0})
        h.assert_called_once_with(player, 0)

        with patch.object(self.game, "_card_move_to") as h:
            self.game._apply_card(player, {"description": "x", "action": "move_to", "value": 39})
        h.assert_called_once_with(player, 39)

        with patch.object(self.game, "_card_birthday") as h:
            self.game._apply_card(player, {"description": "x", "action": "birthday", "value": 10})
        h.assert_called_once_with(player, 10)

        with patch.object(self.game, "_card_collect_from_all") as h:
            self.game._apply_card(
                player,
                {"description": "x", "action": "collect_from_all", "value": 50},
            )
        h.assert_called_once_with(player, 50)

        with patch.object(self.game, "_card_collect") as h:
            self.game._apply_card(player, {"description": "x", "action": "unknown", "value": 1})
        h.assert_not_called()

    def test_individual_card_handlers(self):
        player = self.game.current_player()
        with patch.object(self.game.bank, "pay_out", return_value=25) as po:
            self.game._card_collect(player, 25)
        po.assert_called_once_with(25)

        with patch.object(player, "deduct_money") as dm, patch.object(
            self.game.bank, "collect"
        ) as collect:
            self.game._card_pay(player, 20)
        dm.assert_called_once_with(20)
        collect.assert_called_once_with(20)

        with patch.object(player, "go_to_jail") as to_jail:
            self.game._card_jail(player, 0)
        to_jail.assert_called_once()

        cards_before = player.get_out_of_jail_cards
        self.game._card_jail_free(player, 0)
        self.assertEqual(player.get_out_of_jail_cards, cards_before + 1)

    def test_card_move_to_branches(self):
        player = self.game.current_player()
        player.position = 39
        with patch.object(self.game.board, "get_tile_type", return_value="blank"), patch.object(
            player, "add_money"
        ) as add_money:
            self.game._card_move_to(player, 1)
        add_money.assert_called_once_with(config.GO_SALARY)

        prop = Property("P", 5, 100, 10)
        with patch.object(self.game.board, "get_tile_type", return_value="property"), patch.object(
            self.game.board, "get_property_at", return_value=prop
        ), patch.object(self.game, "_handle_property_tile") as hp:
            self.game._card_move_to(player, 5)
        hp.assert_called_once_with(player, prop)

    def test_birthday_and_collect_from_all_transfer_only_if_affordable(self):
        player = self.game.current_player()
        other1 = self.game.players[1]
        other2 = self.game.players[2]
        other1.balance = 20
        other2.balance = 5

        start = player.balance
        self.game._card_birthday(player, 10)
        self.assertEqual(player.balance, start + 10)
        self.assertEqual(other1.balance, 10)
        self.assertEqual(other2.balance, 5)

        start2 = player.balance
        self.game._card_collect_from_all(player, 10)
        self.assertEqual(player.balance, start2 + 10)

    def test_check_bankruptcy_paths(self):
        survivor = self.game.players[0]
        bust = self.game.players[1]
        prop = Property("P", 1, 100, 10)
        bust.add_property(prop)
        prop.owner = bust
        prop.is_mortgaged = True
        bust.balance = 0

        self.game._turn_state["current_index"] = len(self.game.players) - 1
        self.game._check_bankruptcy(bust)
        self.assertTrue(bust.is_eliminated)
        self.assertNotIn(bust, self.game.players)
        self.assertIsNone(prop.owner)
        self.assertFalse(prop.is_mortgaged)
        self.assertEqual(self.game.current_index, 0)
        self.assertIn(survivor, self.game.players)

        before = list(self.game.players)
        healthy = self.game.players[0]
        healthy.balance = 10
        self.game._check_bankruptcy(healthy)
        self.assertEqual(before, self.game.players)

    def test_find_winner_paths(self):
        empty_game = Game(["A", "B"])
        empty_game.players = []
        self.assertIsNone(empty_game.find_winner())

        g = Game(["A", "B"])
        g.players[0].balance = 100
        g.players[1].balance = 200
        self.assertIs(g.find_winner(), g.players[1])

    def test_run_paths(self):
        g = Game(["A", "B"])
        g._turn_state["running"] = False
        with patch("moneypoly.ui.print_banner"), patch("builtins.print") as mock_print:
            g.run()
        self.assertTrue(any("wins" in str(c) for c in mock_print.call_args_list))

        g2 = Game(["A", "B"])
        g2.players = []
        g2._turn_state["running"] = False
        with patch("moneypoly.ui.print_banner"), patch("builtins.print") as mock_print:
            g2.run()
        self.assertTrue(any("no players remaining" in str(c).lower() for c in mock_print.call_args_list))

    def test_interactive_menu_and_submenus(self):
        player = self.game.current_player()
        with patch("moneypoly.ui.safe_int_input", side_effect=[1, 2, 3, 4, 5, 6, 100, 0]), patch.object(
            self.game, "_menu_mortgage"
        ) as mm, patch.object(self.game, "_menu_unmortgage") as mu, patch.object(
            self.game, "_menu_trade"
        ) as mt, patch.object(self.game.bank, "give_loan") as gl, patch(
            "moneypoly.ui.print_standings"
        ) as ps, patch("moneypoly.ui.print_board_ownership") as pbo:
            self.game.interactive_menu(player)
        ps.assert_called_once()
        pbo.assert_called_once()
        mm.assert_called_once_with(player)
        mu.assert_called_once_with(player)
        mt.assert_called_once_with(player)
        gl.assert_called_once_with(player, 100)

        p = self.game.current_player()
        p.properties = []
        with patch("builtins.print") as mock_print:
            self.game._menu_mortgage(p)
        self.assertTrue(any("No properties" in str(c) for c in mock_print.call_args_list))

        with patch("builtins.print") as mock_print:
            self.game._menu_unmortgage(p)
        self.assertTrue(any("No mortgaged" in str(c) for c in mock_print.call_args_list))

        self.game.players = [p]
        with patch("builtins.print") as mock_print:
            self.game._menu_trade(p)
        self.assertTrue(any("No other players" in str(c) for c in mock_print.call_args_list))


class TestMainModuleWhiteBox(unittest.TestCase):
    """White-box tests for top-level CLI main.py file."""

    def test_get_player_names_parsing(self):
        with patch("builtins.input", return_value=" Alice, Bob , , Charlie "):
            names = app_main.get_player_names()
        self.assertEqual(names, ["Alice", "Bob", "Charlie"])

    def test_main_success_path(self):
        fake_game = MagicMock()
        with patch.object(app_main, "get_player_names", return_value=["A", "B"]), patch.object(
            app_main, "Game", return_value=fake_game
        ):
            app_main.main()
        fake_game.run.assert_called_once()

    def test_main_keyboard_interrupt_path(self):
        with patch.object(app_main, "get_player_names", return_value=["A", "B"]), patch.object(
            app_main, "Game", side_effect=KeyboardInterrupt
        ), patch("builtins.print") as mock_print:
            app_main.main()
        self.assertTrue(any("interrupted" in str(c).lower() for c in mock_print.call_args_list))

    def test_main_value_error_path(self):
        with patch.object(app_main, "get_player_names", return_value=["A", "B"]), patch.object(
            app_main, "Game", side_effect=ValueError("bad setup")
        ), patch("builtins.print") as mock_print:
            app_main.main()
        self.assertTrue(any("Setup error" in str(c) for c in mock_print.call_args_list))


class TestAdditionalFailingCases(unittest.TestCase):
    """Additional white-box bug-finding tests expected to fail currently."""

    def test_bank_give_loan_should_reduce_bank_funds(self):
        bank = Bank()
        player = Player("Borrower")
        start_funds = bank.get_balance()
        with patch("builtins.print"):
            bank.give_loan(player, 200)
        self.assertEqual(bank.get_balance(), start_funds - 200)

    def test_player_move_passing_go_should_collect_salary(self):
        player = Player("Runner")
        player.position = config.BOARD_SIZE - 1
        start_balance = player.balance
        player.move(2)
        self.assertEqual(player.position, 1)
        self.assertEqual(player.balance, start_balance + config.GO_SALARY)

    def test_unowned_property_should_not_charge_rent(self):
        prop = Property("Free Lot", 12, 140, 14)
        self.assertEqual(prop.owner, None)
        self.assertEqual(prop.get_rent(), 0)

    def test_trade_negative_cash_should_fail_gracefully(self):
        game = Game(["A", "B"])
        seller = game.players[0]
        buyer = game.players[1]
        prop = Property("P", 1, 100, 10)
        prop.owner = seller
        seller.add_property(prop)
        result = game.trade(seller, buyer, prop, -50)
        self.assertFalse(result)

    def test_game_should_require_at_least_two_players(self):
        with self.assertRaises(ValueError):
            Game(["Solo"])

    def test_get_player_names_should_enforce_minimum_two(self):
        with patch("builtins.input", return_value="Solo"):
            names = app_main.get_player_names()
        self.assertGreaterEqual(len(names), 2)

    def test_bank_should_reject_loan_larger_than_reserves(self):
        bank = Bank()
        player = Player("Borrower")
        with self.assertRaises(ValueError):
            bank.give_loan(player, bank.get_balance() + 1)

    def test_trade_with_zero_cash_should_fail(self):
        game = Game(["A", "B"])
        seller = game.players[0]
        buyer = game.players[1]
        prop = Property("P", 1, 100, 10)
        prop.owner = seller
        seller.add_property(prop)
        result = game.trade(seller, buyer, prop, 0)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
