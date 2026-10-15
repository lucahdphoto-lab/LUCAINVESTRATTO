"""
Unit tests for PortfolioSnapshot model, database repository,
and monthly reconciliation (Quadratura) & trend analytics.
"""
import unittest
import os
import json
import tempfile
from datetime import date, timedelta

from lucainvestratto.models import PortfolioSnapshot, Holding, BankAccount, Transaction
from lucainvestratto.db import Database
from lucainvestratto.analytics.snapshots import (
    reconcile_snapshot_with_actual,
    calculate_snapshot_trends,
    parse_raw_text_to_allocations
)


class TestPortfolioSnapshots(unittest.TestCase):
    def setUp(self):
        # Create a temporary SQLite database for test isolation
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_snapshots.db")
        self.db = Database(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_snapshot_model_serialization(self):
        snap = PortfolioSnapshot(
            id="snap_test_1",
            account_id="all",
            snapshot_date="2026-03-31",
            total_wealth=150000.0,
            liquid_cash=30000.0,
            invested_amount=120000.0,
            notes="Snapshot di fine trimestre"
        )
        allocs = [
            {"asset_class": "Azioni", "amount": 80000.0, "weight_pct": 53.33},
            {"asset_class": "Obbligazioni", "amount": 40000.0, "weight_pct": 26.67},
            {"asset_class": "Liquidità", "amount": 30000.0, "weight_pct": 20.0}
        ]
        snap.set_allocations(allocs)

        data = snap.to_dict()
        self.assertEqual(data["id"], "snap_test_1")
        self.assertEqual(data["total_wealth"], 150000.0)

        restored = PortfolioSnapshot.from_dict(data)
        self.assertEqual(restored.id, "snap_test_1")
        self.assertEqual(len(restored.get_allocations()), 3)
        self.assertEqual(restored.get_allocations()[0]["asset_class"], "Azioni")

    def test_snapshot_db_crud(self):
        snap = PortfolioSnapshot(
            id="s1",
            account_id="acc1",
            snapshot_date="2026-01-31",
            total_wealth=100000.0,
            liquid_cash=20000.0,
            invested_amount=80000.0,
            notes="Primo snapshot"
        )
        self.db.save_snapshot(snap)

        all_snaps = self.db.get_snapshots()
        self.assertEqual(len(all_snaps), 1)
        self.assertEqual(all_snaps[0].id, "s1")
        self.assertEqual(all_snaps[0].total_wealth, 100000.0)

        single = self.db.get_snapshot_by_id("s1")
        self.assertIsNotNone(single)
        self.assertEqual(single.notes, "Primo snapshot")

        # Delete
        self.db.delete_snapshot("s1")
        self.assertEqual(len(self.db.get_snapshots()), 0)

    def test_reconcile_perfect_match(self):
        accounts = [
            BankAccount(id="acc_main", name="Main Bank", initial_balance=25000.0)
        ]
        holdings = [
            Holding(id="h1", account_id="acc_main", symbol="ETF1", name="ETF World", quantity=100, current_price=100.0, asset_class="Azionario"),
            Holding(id="h2", account_id="acc_main", symbol="BOND1", name="Gov Bond", quantity=50, current_price=100.0, asset_class="Obbligazionario")
        ]
        # Total internal: cash 25,000 + holdings (10,000 + 5,000) = 40,000.0
        snap = PortfolioSnapshot(
            id="snap_exact",
            account_id="acc_main",
            snapshot_date="2026-03-31",
            total_wealth=40000.0,
            liquid_cash=25000.0,
            invested_amount=15000.0
        )
        snap.set_allocations([
            {"asset_class": "Azionario", "amount": 10000.0, "weight_pct": 25.0},
            {"asset_class": "Obbligazionario", "amount": 5000.0, "weight_pct": 12.5},
            {"asset_class": "Liquidità & Conti", "amount": 25000.0, "weight_pct": 62.5}
        ])

        recon = reconcile_snapshot_with_actual(snap, holdings, accounts)
        self.assertEqual(recon["status"], "PERFETTAMENTE_QUADRATO")
        self.assertAlmostEqual(recon["delta_total"], 0.0, places=2)
        self.assertAlmostEqual(recon["delta_cash"], 0.0, places=2)
        self.assertAlmostEqual(recon["delta_invested"], 0.0, places=2)

    def test_reconcile_with_discrepancy(self):
        accounts = [
            BankAccount(id="acc_main", name="Main Bank", initial_balance=20000.0)
        ]
        holdings = [
            Holding(id="h1", account_id="acc_main", symbol="ETF1", name="ETF World", quantity=100, current_price=100.0, asset_class="Azionario")
        ]
        # Internal total: 30,000.0
        # External snapshot: 32,500.0 (delta = +2,500.0)
        snap = PortfolioSnapshot(
            id="snap_disc",
            account_id="acc_main",
            snapshot_date="2026-03-31",
            total_wealth=32500.0,
            liquid_cash=22500.0,
            invested_amount=10000.0
        )
        recon = reconcile_snapshot_with_actual(snap, holdings, accounts)
        self.assertEqual(recon["status"], "DISCREPANZA_SIGNIFICATIVA")
        self.assertEqual(recon["delta_total"], 2500.0)

    def test_calculate_snapshot_trends(self):
        s1 = PortfolioSnapshot(
            id="s1",
            snapshot_date="2026-01-31",
            total_wealth=100000.0,
            liquid_cash=20000.0,
            invested_amount=80000.0
        )
        s1.set_allocations([{"asset_class": "Azioni", "amount": 80000.0, "weight_pct": 80.0}])

        s2 = PortfolioSnapshot(
            id="s2",
            snapshot_date="2026-02-28",
            total_wealth=105000.0,
            liquid_cash=21000.0,
            invested_amount=84000.0
        )
        s2.set_allocations([{"asset_class": "Azioni", "amount": 84000.0, "weight_pct": 80.0}])

        s3 = PortfolioSnapshot(
            id="s3",
            snapshot_date="2026-03-31",
            total_wealth=110000.0,
            liquid_cash=22000.0,
            invested_amount=88000.0
        )
        s3.set_allocations([{"asset_class": "Azioni", "amount": 88000.0, "weight_pct": 80.0}])

        trends = calculate_snapshot_trends([s3, s1, s2]) # Pass unsorted
        self.assertTrue(trends["has_data"])
        self.assertEqual(trends["count"], 3)
        self.assertEqual(trends["earliest_wealth"], 100000.0)
        self.assertEqual(trends["latest_wealth"], 110000.0)
        self.assertEqual(trends["total_gain"], 10000.0)
        self.assertEqual(trends["total_gain_pct"], 10.0)
        self.assertGreater(trends["cagr"], 0.0)

    def test_parse_raw_text_to_allocations(self):
        raw = """
        Azionario Globale: 50.000,00 € (50%)
        Obbligazioni Sovrane: 30.000 € (30%)
        Liquidità Bancaria: 20000 (20%)
        """
        parsed = parse_raw_text_to_allocations(raw)
        self.assertEqual(len(parsed), 3)
        self.assertIn("Azionario Globale", parsed[0]["asset_class"])
        self.assertEqual(parsed[0]["amount"], 50000.0)
        self.assertEqual(parsed[0]["weight_pct"], 50.0)
        self.assertEqual(parsed[1]["amount"], 30000.0)
        self.assertEqual(parsed[2]["amount"], 20000.0)


if __name__ == "__main__":
    unittest.main()
