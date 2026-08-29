"""
PROPERTY-BASED HYPOTHESIS TEST SUITE FOR FILENAME PARSING
Verifies algebraic invariants of the filename parser across arbitrary generated inputs.
"""

from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from app.parser import parse_filename

# -----------------------------------------------------------------------------
# Strategy Generators
# -----------------------------------------------------------------------------

# Valid tokens
recipe_names = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_', max_codepoint=127),
    min_size=1, max_size=30
).filter(lambda s: not s.startswith('-') and not s.endswith('-'))

serial_numbers = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_', max_codepoint=127),
    min_size=1, max_size=15
)

# Valid calendar dates (Leap-year aware via st.dates)
valid_dates = st.dates(min_value=datetime(2000, 1, 1).date(), max_value=datetime(2099, 12, 31).date())

# Valid times
valid_times = st.times()

extensions = st.sampled_from(['.xlsx', '.csv', '.XLSX', '.CSV'])
copy_suffixes = st.sampled_from(['', ' (1)', ' (2)', ' (99)', ' - Copy', ' - Copy (1)'])

# -----------------------------------------------------------------------------
# Properties
# -----------------------------------------------------------------------------

@settings(max_examples=250, suppress_health_check=[HealthCheck.too_slow])
@given(
    recipe=recipe_names,
    d=valid_dates,
    t=valid_times,
    sn=serial_numbers,
    ext=extensions,
    suffix=copy_suffixes
)
def test_property_well_formed_filenames_always_parse(recipe, d, t, sn, ext, suffix):
    """
    PROPERTY 1 (Round-trip & Grammar Acceptance):
    Any filename constructed from the valid grammar with real calendar dates
    MUST parse successfully into exactly its constituent metadata components.
    """
    date_str = d.strftime('%d-%m-%Y')
    time_str = t.strftime('%H.%M.%S')
    filename = f"{recipe}_{date_str}_{time_str}_{sn}{suffix}{ext}"
    
    parsed = parse_filename(filename)
    assert parsed is not None, f"Failed to parse valid filename: {filename}"
    assert parsed['recipe_name'] == recipe
    assert parsed['report_date'] == d.strftime('%Y-%m-%d')
    assert parsed['report_time'] == t.strftime('%H:%M:%S')
    
    # Serial normalization: numeric strings padded to at least 4 digits, alphanumeric preserved
    if sn.isdigit():
        assert parsed['serial_normalized'] == sn.zfill(4)
    else:
        assert parsed['serial_normalized'] == sn


@settings(max_examples=250)
@given(st.text(min_size=0, max_size=100))
def test_property_arbitrary_fuzz_never_crashes(random_string):
    """
    PROPERTY 2 (Total Function / Crash Freedom):
    parse_filename must NEVER raise an uncaught exception (IndexError, TypeError, ValueError)
    for ANY arbitrary string input. It must either return a valid dict or None.
    """
    res = parse_filename(random_string)
    assert res is None or isinstance(res, dict)
    if isinstance(res, dict):
        assert 'recipe_name' in res
        assert 'report_date' in res
        assert 'report_time' in res
        assert 'serial_normalized' in res


@settings(max_examples=200)
@given(
    recipe=recipe_names,
    bad_month=st.integers().filter(lambda m: m < 1 or m > 12),
    bad_day=st.integers(min_value=1, max_value=31),
    sn=serial_numbers
)
def test_property_invalid_calendar_months_strictly_rejected(recipe, bad_month, bad_day, sn):
    """
    PROPERTY 3 (Calendar Strictness):
    Filenames with impossible calendar months (e.g. month 00 or 13-99) must ALWAYS return None.
    """
    filename = f"{recipe}_{bad_day:02d}-{bad_month:02d}-2026_12.00.00_{sn}.xlsx"
    assert parse_filename(filename) is None


@settings(max_examples=150)
@given(
    recipe=recipe_names,
    bad_hour=st.integers().filter(lambda h: h < 0 or h > 23),
    sn=serial_numbers
)
def test_property_invalid_hours_strictly_rejected(recipe, bad_hour, sn):
    """
    PROPERTY 4 (Clock Strictness):
    Filenames with impossible hours (e.g. 24:00:00 to 99:00:00) must ALWAYS return None.
    """
    filename = f"{recipe}_13-06-2026_{bad_hour:02d}.00.00_{sn}.xlsx"
    assert parse_filename(filename) is None
