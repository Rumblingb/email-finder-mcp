"""Direct test script for Email Finder MCP core functions."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from email_finder_mcp.rate_limiter import check_rate_limit, FREE_LIMIT, STRIPE_LINK
from email_finder_mcp.email_utils import find_email, find_company_emails


def test():
    print("=== Email Finder MCP Core Test ===\n")

    # Test rate limiter
    print("1) Testing check_rate_limit()...")
    result = check_rate_limit("test-client-001")
    assert result["allowed"] == True, "Should be allowed"
    assert result["remaining"] == FREE_LIMIT, f"Should have {FREE_LIMIT} remaining"
    assert result["is_pro"] == False
    print(f"   PASS: Allowed={result['allowed']}, Remaining={result['remaining']}, IsPRO={result['is_pro']}")

    # Test PRO key
    print("2) Testing PRO key bypass...")
    result = check_rate_limit("test-client-001", "demo-pro-key-001")
    assert result["allowed"] == True
    assert result["is_pro"] == True
    assert result["remaining"] is None
    print(f"   PASS: Allowed={result['allowed']}, IsPRO={result['is_pro']}, Unlimited={result['remaining']}")

    # Test find_email
    print("3) Testing find_email('John', 'Doe', 'acme.com')...")
    result = find_email("John", "Doe", "acme.com")
    assert result["email"] is not None
    assert "@" in result["email"]
    assert "acme.com" in result["email"]
    print(f"   PASS: Email={result['email']}, Confidence={result['confidence']}, Patterns={len(result['all_patterns'])}")

    # Test find_email error case
    print("4) Testing find_email with empty params...")
    result = find_email("", "", "")
    assert result["email"] is None
    assert result.get("error") is not None
    print(f"   PASS: Error={result['error']}")

    # Test find_company_emails
    print("5) Testing find_company_emails('Acme Corp')...")
    result = find_company_emails("Acme Corp")
    assert result["domain"] is not None
    assert len(result["patterns"]) > 0
    print(f"   PASS: Domain={result['domain']}, Patterns={len(result['patterns'])}")

    # Test server imports
    print("6) Testing server imports...")
    from email_finder_mcp.server import server
    print(f"   PASS: Server={server.name}")

    # Verify __main__ imports
    print("7) Testing __main__ imports...")
    from email_finder_mcp.__main__ import main
    print(f"   PASS: main function OK")

    print(f"\n=== ALL 7 TESTS PASSED ===")
    print(f"\nPRO Keys: demo-pro-key-001, demo-pro-key-002, demo-pro-key-003")
    print(f"FREE_LIMIT: {FREE_LIMIT}")
    print(f"STRIPE_LINK: {STRIPE_LINK}")


if __name__ == "__main__":
    test()
