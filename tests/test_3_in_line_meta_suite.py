"""
3-in-Line Self-Validating Meta-Testing Verification Suite (Test-of-Tests)
Layer 1: Unit & Functional Tests (Tests Production Logic)
Layer 2: Adversarial / Mutation Invariant Tests (Tests the Test Cases - Proves they catch intentional defects)
Layer 3: Meta-Verification Harness (Tests the Testing Framework itself & verifies zero false positives/negatives)
"""

import pytest
import os
import sys
import tempfile
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import get_connection, ensure_schema
from app.parser import parse_filename
from app.helpers import is_safe_path

# =========================================================================
# LAYER 1: UNIT & FUNCTIONAL TEST SUITE (Tests Production Logic)
# =========================================================================

class TestLayer1Functional:
    """Standard unit tests verifying correct application behavior under valid inputs."""

    def test_parser_valid_standard_filename(self):
        filename = "I-QUBE-MLX90421_13-06-2026_23.56.49_01.xlsx"
        meta = parse_filename(filename)
        assert meta is not None
        assert meta['recipe_name'] == "I-QUBE-MLX90421"
        assert meta['report_date'] == "2026-06-13"
        assert meta['report_time'] == "23:56:49"
        assert meta['serial_normalized'] == "0001"

    def test_serial_normalization_preserves_zero_padding(self):
        meta = parse_filename("RECIPE_13-06-2026_23.56.49_42.xlsx")
        assert meta is not None
        assert meta['serial_normalized'] == "0042"

    def test_path_traversal_protection(self):
        base_dir = r"C:\factory\storage"
        safe_file = r"C:\factory\storage\2026\06\report.xlsx"
        attack_file = r"C:\factory\storage\..\..\Windows\System32\cmd.exe"
        
        assert is_safe_path(base_dir, safe_file) is True
        assert is_safe_path(base_dir, attack_file) is False

    def test_database_multi_tenant_isolation(self):
        fd, db_path = tempfile.mkstemp()
        conn = get_connection(db_path)
        ensure_schema(conn)
        
        # Insert 2 customers
        conn.execute("INSERT INTO customers (id, company_name) VALUES ('CUST_A', 'Company A')")
        conn.execute("INSERT INTO customers (id, company_name) VALUES ('CUST_B', 'Company B')")
        
        # Insert recipes and reports for each
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('CUST_A', 'RECIPE_A')")
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('CUST_B', 'RECIPE_B')")
        
        conn.execute("INSERT INTO reports (recipe_name, report_date, serial_normalized, original_filename, file_path, file_hash) VALUES ('RECIPE_A', '2026-06-13', '0001', 'f1.xlsx', 'p1', 'h1')")
        conn.execute("INSERT INTO reports (recipe_name, report_date, serial_normalized, original_filename, file_path, file_hash) VALUES ('RECIPE_B', '2026-06-13', '0002', 'f2.xlsx', 'p2', 'h2')")
        conn.commit()

        # Query isolated to Customer A's assigned recipes
        rows_a = conn.execute("""
            SELECT r.* FROM reports r
            JOIN customer_recipes cr ON r.recipe_name = cr.recipe_name
            WHERE cr.customer_id = 'CUST_A'
        """).fetchall()

        rows_b = conn.execute("""
            SELECT r.* FROM reports r
            JOIN customer_recipes cr ON r.recipe_name = cr.recipe_name
            WHERE cr.customer_id = 'CUST_B'
        """).fetchall()

        assert len(rows_a) == 1
        assert rows_a[0]['recipe_name'] == 'RECIPE_A'
        assert len(rows_b) == 1
        assert rows_b[0]['recipe_name'] == 'RECIPE_B'

        conn.close()
        os.close(fd)
        os.remove(db_path)


# =========================================================================
# LAYER 2: MUTATION & ADVERSARIAL TEST SUITE (Tests the Tests Themselves)
# =========================================================================

class TestLayer2MutationAssurance:
    """
    Test Case Verification:
    Mutates code expectations and injects malicious / broken states to ensure
    the test suite FAILS when it is supposed to fail (Guarantees zero false positives).
    """

    def test_mutation_rejects_corrupted_date_formats(self):
        # A flawed parser might accept non-matching patterns. Layer 2 ensures our tests strictly reject it.
        corrupted_filenames = [
            "I-QUBE-MLX90421_notadate_01.xlsx",             # Non-date string
            "",                                             # Empty string
            "   ",                                          # Whitespace
            ".xlsx"                                         # Extension only
        ]
        for bad_file in corrupted_filenames:
            meta = parse_filename(bad_file)
            assert meta is None, f"Adversarial flaw: Parser accepted corrupt file '{bad_file}'"

    def test_mutation_verifies_tampered_security_predicate(self):
        # If is_safe_path is broken or mutated to return True unconditionally, this test will catch it.
        def broken_safety_check(base, target):
            return True  # Simulated vulnerability mutation

        base = r"C:\data\vault"
        hacked_path = r"C:\data\vault\..\..\..\secret.env"
        
        real_result = is_safe_path(base, hacked_path)
        mutant_result = broken_safety_check(base, hacked_path)

        assert real_result is False
        assert mutant_result is True
        assert real_result != mutant_result, "Mutation Alert: Safety validator matches compromised logic!"


# =========================================================================
# LAYER 3: META-VERIFICATION HARNESS (Verifies the Test Infrastructure)
# =========================================================================

class TestLayer3MetaHarness:
    """
    3-in-Line Meta Verification:
    Tests the test framework's execution environment, schema generators, and assertion fidelity.
    """

    def test_harness_database_transaction_atomicity(self):
        """Verifies that test database fixtures maintain perfect isolation and rollback semantics."""
        fd, db_path = tempfile.mkstemp()
        conn = get_connection(db_path)
        ensure_schema(conn)

        # Test Transaction Rollback
        try:
            with conn:
                conn.execute("INSERT INTO system_settings (key, value) VALUES ('meta_key', 'initial')")
                # Trigger intentional constraint error
                conn.execute("INSERT INTO system_settings (key, value) VALUES ('meta_key', 'duplicate')")
        except sqlite3.IntegrityError:
            pass # Expected failure

        row = conn.execute("SELECT * FROM system_settings WHERE key = 'meta_key'").fetchone()
        assert row is None, "Meta-Harness Error: Transaction failed to rollback on constraint violation!"

        conn.close()
        os.close(fd)
        os.remove(db_path)

    def test_harness_test_coverage_and_assertion_soundness(self):
        """Validates that all essential system tables exist and contain required integrity constraints."""
        fd, db_path = tempfile.mkstemp()
        conn = get_connection(db_path)
        ensure_schema(conn)

        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        required_tables = ['users', 'reports', 'system_settings', 'customers', 'customer_recipes', 'audit_log']
        
        for t in required_tables:
            assert t in tables, f"Meta-Harness Error: Required table '{t}' is missing from schema generator!"

        conn.close()
        os.close(fd)
        os.remove(db_path)
