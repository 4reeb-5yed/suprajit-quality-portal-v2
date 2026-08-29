"""
PAIRWISE COMBINATORIAL BOUNDARY TESTING FOR SEARCH QUERY FILTERS
Generated using AllPairs combinatorial coverage across multi-parameter boundaries.
"""

import pytest
from allpairspy import AllPairs
from app.database import get_connection, ensure_schema

# -----------------------------------------------------------------------------
# Parameter Boundary Dimensions
# -----------------------------------------------------------------------------
RECIPE_PARAM = [
    "",                     # Empty / omitted
    "EV_THROTTLE",          # Exact match
    "NONEXISTENT_RECIPE",   # Valid string, zero match
    "'; DROP TABLE reports; --", # SQL Injection payload
    "RECIPE_WITH_UNDERSCORES_AND_HYPHENS-123", # Boundary length / characters
    "ev_throttle"           # Lowercase match
]

SERIAL_PARAM = [
    "",                     # Empty / omitted
    "0001",                 # Standard padded 4-digit
    "1",                    # Unpadded single digit
    "SN-XYZ-999999",        # Long alphanumeric
    "%' OR 1=1 --",         # SQL Injection wildcard
    "9999"                  # High boundary
]

DATE_FROM_PARAM = [
    "",                     # Empty
    "2026-06-01",           # Start of range
    "2026-06-13",           # Exact target date
    "2026-06-30",           # Future / after target date
    "invalid-date-format",  # Malformed string
    "1900-01-01"            # Far past boundary
]

DATE_TO_PARAM = [
    "",                     # Empty
    "2026-06-01",           # Past / before target date
    "2026-06-13",           # Exact target date
    "2026-06-30",           # End of range
    "invalid-date-format",  # Malformed string
    "2099-12-31"            # Far future boundary
]

USER_ROLE = [
    "admin",                # System Administrator (Access all)
    "customer_admin",       # Customer Tenant Admin (Scoped to company)
    "customer_viewer",      # Customer Viewer (Scoped to company)
    "custom_user"           # Custom User (Scoped to explicit user_recipes table)
]

# Generate minimal pairwise test vectors covering all 2-way interactions
PAIRWISE_PARAMETERS = [
    RECIPE_PARAM,
    SERIAL_PARAM,
    DATE_FROM_PARAM,
    DATE_TO_PARAM,
    USER_ROLE
]

PAIRWISE_TEST_CASES = list(AllPairs(PAIRWISE_PARAMETERS))

@pytest.mark.parametrize("recipe, serial, date_from, date_to, role", PAIRWISE_TEST_CASES)
def test_pairwise_search_filtering(client, app, recipe, serial, date_from, date_to, role):
    """
    Executes all pairwise combinatorial interactions against the search endpoint.
    Verifies that no combination causes 500 server errors or unhandled exceptions.
    """
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)
        # Seed test data
        conn.execute("INSERT OR REPLACE INTO customers (id, company_name) VALUES ('tvs', 'TVS Motor')")
        conn.execute("INSERT OR REPLACE INTO customer_recipes (customer_id, recipe_name) VALUES ('tvs', 'EV_THROTTLE')")
        conn.execute("""
            INSERT OR REPLACE INTO users (id, username, password_hash, display_name, email, role, customer_id, access_mode, is_active)
            VALUES (999, 'pairwise_user', 'hash', 'Pairwise User', 'pair@example.com', ?, 'tvs', ?, 1)
        """, (role, 'CUSTOM' if role == 'custom_user' else 'COMPANY'))
        if role == 'custom_user':
            conn.execute("INSERT OR REPLACE INTO user_recipes (user_id, recipe_name) VALUES (999, 'EV_THROTTLE')")
        conn.execute("""
            INSERT OR IGNORE INTO reports (recipe_name, report_date, report_time, serial_raw, serial_normalized, original_filename, file_path, file_hash)
            VALUES ('EV_THROTTLE', '2026-06-13', '12:00:00', '0001', '0001', 'file.xlsx', 'path', 'hash_pw')
        """)
        conn.commit()
        conn.close()

    with client.session_transaction() as sess:
        sess['_user_id'] = '999'
        sess['user_id'] = 999
        sess['role'] = role
        sess['customer_id'] = 'tvs'

    query_url = f"/search/results?recipe={recipe}&serial={serial}&date_from={date_from}&date_to={date_to}"
    res = client.get(query_url)

    # Server must gracefully handle all combinations with HTTP 200 or clean validation
    assert res.status_code == 200
    assert b"<tr>" in res.data or b"<!DOCTYPE html>" in res.data or b"table" in res.data or b"No quality reports found" in res.data
