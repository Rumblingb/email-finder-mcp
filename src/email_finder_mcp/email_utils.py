"""Email finding and verification utilities using free/pattern-based methods."""

import re
import smtplib
import socket
import dns.resolver
from typing import Optional


# Common email patterns for different name formats
def _generate_patterns(first_name: str, last_name: str, domain: str) -> list[str]:
    """Generate possible email addresses based on common naming patterns."""
    fn = first_name.lower().strip()
    ln = last_name.lower().strip()
    d = domain.lower().strip().lstrip("@")
    patterns = [
        f"{fn}.{ln}@{d}",        # john.doe@domain.com
        f"{fn}{ln}@{d}",         # johndoe@domain.com
        f"{fn}@{d}",             # john@domain.com
        f"{ln}.{fn}@{d}",       # doe.john@domain.com
        f"{fn[0]}{ln}@{d}",     # jdoe@domain.com
        f"{fn}.{ln[0]}@{d}",    # john.d@domain.com
        f"{fn[0]}.{ln}@{d}",    # j.doe@domain.com
        f"{fn}_{ln}@{d}",       # john_doe@domain.com
        f"{ln}{fn[0]}@{d}",     # doej@domain.com
        f"{fn[0]}{ln[0]}@{d}",  # jd@domain.com
    ]
    return patterns


def _validate_email_format(email: str) -> bool:
    """Basic email format validation using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def find_email(first_name: str, last_name: str, domain: str) -> dict:
    """Find likely email address for a person using pattern guessing.

    Returns:
        dict with:
            - email (str or None): the most likely email
            - confidence (str): high/medium/low
            - all_patterns (list): all generated candidates
    """
    if not all([first_name, last_name, domain]):
        return {
            "email": None,
            "confidence": "low",
            "all_patterns": [],
            "error": "first_name, last_name, and domain are required",
        }

    domain = domain.lower().strip().lstrip("@")

    if not _validate_email_format(f"test@{domain}"):
        return {
            "email": None,
            "confidence": "low",
            "all_patterns": [],
            "error": f"Invalid domain format: {domain}",
        }

    patterns = _generate_patterns(first_name, last_name, domain)

    # Most common patterns (first two) get higher confidence
    likely_email = patterns[0]  # john.doe@domain.com - most common pattern
    confidence = "high"

    return {
        "email": likely_email,
        "confidence": confidence,
        "all_patterns": patterns,
        "pattern_used": patterns[0],
    }


def verify_email(email: str, timeout: int = 5) -> dict:
    """Verify if an email address exists using SMTP and MX record checks.

    This performs:
    1. Format validation
    2. MX record lookup for the domain
    3. SMTP handshake to verify the mailbox (non-delivery)

    Note: SMTP verification is not 100% reliable as many servers
    have catch-all addresses or block verification attempts.
    """
    result = {
        "email": email,
        "format_valid": False,
        "mx_record": None,
        "mx_valid": False,
        "smtp_verified": False,
        "verdict": "invalid",
        "details": [],
    }

    # Step 1: Format check
    if not _validate_email_format(email):
        result["details"].append("Invalid email format")
        return result

    result["format_valid"] = True
    result["details"].append("Format valid")

    # Step 2: Extract domain and check MX records
    _, domain = email.split("@", 1)

    try:
        mx_records = dns.resolver.resolve(domain, "MX", lifetime=timeout)
        mx_record = str(mx_records[0].exchange).rstrip(".")
        result["mx_record"] = mx_record
        result["mx_valid"] = True
        result["details"].append(f"MX record found: {mx_record}")
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN,
            dns.resolver.LifetimeTimeout, dns.exception.DNSException) as e:
        result["details"].append(f"MX lookup failed: {str(e)}")
        # If no MX records, domain likely doesn't accept email
        return result

    # Step 3: SMTP verification
    try:
        # Use a real-looking sender to avoid being blocked
        sender = "verify@example.com"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        server = smtplib.SMTP(timeout=timeout)
        server.set_debuglevel(0)
        server.connect(mx_record, 25)
        server.ehlo(name="mail.example.com")

        # Start TLS if supported
        try:
            server.starttls()
            server.ehlo(name="mail.example.com")
        except (smtplib.SMTPException, OSError):
            pass  # TLS not available, continue with plain SMTP

        server.mail(sender)
        code, message = server.rcpt(email)
        server.quit()

        # SMTP code 250 means the server accepted the RCPT (mailbox exists)
        # Some servers return 450 (temporary failure) to prevent probing
        if code == 250:
            result["smtp_verified"] = True
            result["verdict"] = "valid"
            result["details"].append(f"SMTP: mailbox exists (code {code})")
        elif code in (450, 451, 452):
            result["smtp_verified"] = False
            result["verdict"] = "unknown"
            result["details"].append(
                f"SMTP: temporary failure (code {code}) - mailbox may exist"
            )
        else:
            result["smtp_verified"] = False
            result["verdict"] = "invalid"
            result["details"].append(f"SMTP: mailbox rejected (code {code})")

    except (smtplib.SMTPConnectError, socket.timeout,
            ConnectionRefusedError, OSError) as e:
        result["details"].append(f"SMTP connection failed: {str(e)}")
        # Domain has MX but SMTP rejected - could be valid but protected
        if result["mx_valid"]:
            result["verdict"] = "unknown"
            result["details"].append("MX exists but SMTP unreachable (anti-probe protection)")

    return result


def find_company_emails(company_name: str, domain: str = None) -> dict:
    """Find common email patterns for a company domain.

    Returns commonly used email formats and patterns at a company.
    Useful for sales prospecting and outreach.
    """
    if not domain:
        domain = _guess_domain(company_name)

    if not domain:
        return {
            "company": company_name,
            "domain": None,
            "patterns": [],
            "error": "Could not determine domain",
        }

    # Common patterns used at companies
    patterns = [
        {"pattern": "{first}.{last}@{domain}", "example": f"john.doe@{domain}", "frequency": "very_common"},
        {"pattern": "{first}@{domain}", "example": f"john@{domain}", "frequency": "common"},
        {"pattern": "{first}{last}@{domain}", "example": f"johndoe@{domain}", "frequency": "common"},
        {"pattern": "{f}{last}@{domain}", "example": f"jdoe@{domain}", "frequency": "common"},
        {"pattern": "{first}.{l}@{domain}", "example": f"john.d@{domain}", "frequency": "less_common"},
        {"pattern": "{f}{l}@{domain}", "example": f"jd@{domain}", "frequency": "less_common"},
    ]

    return {
        "company": company_name,
        "domain": domain,
        "patterns": patterns,
        "mx_record": _check_mx(domain),
    }


def _guess_domain(company_name: str) -> Optional[str]:
    """Guess company domain from name."""
    name = company_name.lower().strip()
    # Remove common suffixes and make a best guess
    name = re.sub(r'\b(inc|llc|ltd|corp|corporation|co|company|technologies|tech|solutions|group|services|software)\b', '', name)
    name = name.replace(" ", "").replace("-", "")
    return f"{name}.com" if name else None


def _check_mx(domain: str) -> dict:
    """Quick MX record check for a domain."""
    try:
        mx_records = dns.resolver.resolve(domain, "MX", lifetime=5)
        return {
            "exists": True,
            "mx": str(mx_records[0].exchange).rstrip("."),
        }
    except Exception:
        return {"exists": False, "mx": None}
