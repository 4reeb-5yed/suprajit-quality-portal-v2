"""
RECURSIVE 3-IN-LINE META-TESTING ENGINE (Test -> Test-of-Test -> Meta-Verifier of Test-of-Test)

Chain of Trust:
1. Level 1: Application Test (Does the app work?)
2. Level 2: Test-Validator (Is the Level 1 test actually valid, or is it a tautology/dummy test?)
3. Level 3: Meta-Auditor (Does the Level 2 test-validator itself properly flag bad tests and pass good tests?)
"""

import pytest
import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.parser import parse_filename
from app.helpers import is_safe_path

# =========================================================================
# LEVEL 1: APPLICATION UNIT TEST (The Target Test)
# =========================================================================

def level1_test_target_parser(parser_func):
    """
    Level 1 Test Function:
    Tests whether a given parser parses the filename correctly.
    """
    valid_file = "I-QUBE-MLX90421_13-06-2026_23.56.49_01.xlsx"
    result = parser_func(valid_file)
    assert result is not None, "Parser returned None for valid file"
    assert result['recipe_name'] == "I-QUBE-MLX90421", "Recipe name mismatch"
    assert result['report_date'] == "2026-06-13", "Date mismatch"
    assert result['serial_normalized'] == "0001", "Serial normalization mismatch"
    return True

def level1_test_target_security_path(safety_func):
    """
    Level 1 Test Function:
    Tests whether a path checker blocks traversal.
    """
    base = r"C:\factory\storage"
    attack = r"C:\factory\storage\..\..\Windows\cmd.exe"
    safe = r"C:\factory\storage\2026\06\report.xlsx"
    
    assert safety_func(base, safe) is True, "False rejection of safe path"
    assert safety_func(base, attack) is False, "Allowed path traversal attack"
    return True


# =========================================================================
# LEVEL 2: TEST-VALIDATOR (Tests if Level 1 Test is Genuine and Catches Bugs)
# =========================================================================

def level2_validate_test_detects_broken_implementations(test_func_to_validate):
    """
    Level 2 Test-Validator:
    Runs `test_func_to_validate` against deliberately broken/mutated implementations.
    PROVES that the test will actually FAIL when production code has a bug.
    If the test still passes on broken code, the test is a FAKE (tautology) and this validator FAILS.
    """
    # 1. Mutated Parser that always returns empty dict (Fake success)
    def mutant_always_empty(fn):
        return {}

    # 2. Mutated Parser that returns wrong serial
    def mutant_wrong_serial(fn):
        return {"recipe_name": "I-QUBE-MLX90421", "report_date": "2026-06-13", "serial_normalized": "9999"}

    # 3. Mutated Parser that always returns None
    def mutant_always_none(fn):
        return None

    caught_count = 0
    for mutant in [mutant_always_empty, mutant_wrong_serial, mutant_always_none]:
        try:
            test_func_to_validate(mutant)
            # If the test passed on a broken mutant, the test is broken!
            return False, f"Test failed to catch mutant: {mutant.__name__}"
        except (AssertionError, KeyError, TypeError):
            # The test correctly threw an assertion error and caught the bug!
            caught_count += 1

    if caught_count == 3:
        return True, "Test successfully caught all mutants"
    return False, "Incomplete mutant detection"


def level2_validate_security_test_detects_compromised_sandbox(security_test_func):
    """
    Level 2 Test-Validator:
    Tests whether the security test actually catches a bypassed or compromised safety function.
    """
    # Mutant 1: Always returns True (Permissive bypass vulnerability)
    def mutant_always_true(b, p):
        return True

    # Mutant 2: Inverted logic
    def mutant_inverted(b, p):
        return not is_safe_path(b, p)

    for mutant in [mutant_always_true, mutant_inverted]:
        try:
            security_test_func(mutant)
            return False, f"Security test allowed compromised predicate: {mutant.__name__}"
        except AssertionError:
            pass # Correctly caught

    return True, "Security test is robust"


# =========================================================================
# LEVEL 3: META-AUDITOR (Tests if Level 2 Test-Validator itself is reliable)
# =========================================================================

class TestLevel3MetaAuditor:
    """
    Level 3: Test of the Test-Validator.
    Audits the validators to verify they distinguish genuine tests from flawed/dummy tests.
    """

    def test_level3_proves_level2_rejects_dummy_tests(self):
        """
        Level 3 Check:
        We create a fake 'dummy test' that always passes (e.g. `assert 1 == 1`).
        We pass this dummy test to Level 2.
        Level 2 MUST reject it as invalid.
        """
        def fake_dummy_test(dummy_parser):
            # A meaningless test that always passes without checking the parser
            assert 1 == 1
            return True

        # Level 2 runs against the dummy test
        is_valid, reason = level2_validate_test_detects_broken_implementations(fake_dummy_test)
        
        # Level 3 verifies: Did Level 2 successfully catch that this test was fake?
        assert is_valid is False, "Meta-Failure: Level 2 failed to detect a fake/dummy test!"
        assert "Test failed to catch mutant" in reason

    def test_level3_proves_level2_accepts_our_real_tests(self):
        """
        Level 3 Check:
        We pass our actual Level 1 test to Level 2.
        Level 2 MUST confirm that our real test is mathematically sound and catches bugs.
        """
        is_valid, reason = level2_validate_test_detects_broken_implementations(level1_test_target_parser)
        assert is_valid is True, f"Meta-Failure: Real test was rejected by validator: {reason}"

    def test_level3_proves_level2_security_auditor_soundness(self):
        """
        Level 3 Check:
        Verifies that Level 2 accurately audits security test cases.
        """
        # 1. Fake security test that asserts nothing
        def dummy_security_test(fn):
            return True

        is_fake_valid, _ = level2_validate_security_test_detects_compromised_sandbox(dummy_security_test)
        assert is_fake_valid is False, "Meta-Failure: Level 2 allowed dummy security test"

        # 2. Genuine security test
        is_real_valid, reason = level2_validate_security_test_detects_compromised_sandbox(level1_test_target_security_path)
        assert is_real_valid is True, f"Meta-Failure: Real security test was rejected: {reason}"


# =========================================================================
# PYTEST EXECUTORS FOR PYTEST DISCOVERY
# =========================================================================

def test_execute_level1_on_production_code():
    """Runs Level 1 test on production parser."""
    assert level1_test_target_parser(parse_filename) is True

def test_execute_level2_on_level1_tests():
    """Runs Level 2 validator on Level 1 tests."""
    valid, reason = level2_validate_test_detects_broken_implementations(level1_test_target_parser)
    assert valid is True, reason

def test_execute_level2_on_security_tests():
    """Runs Level 2 validator on security tests."""
    valid, reason = level2_validate_security_test_detects_compromised_sandbox(level1_test_target_security_path)
    assert valid is True, reason
