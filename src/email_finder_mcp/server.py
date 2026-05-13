"""Email Finder MCP Server - Main entry point with MCP tools."""

import sys
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)

from .email_utils import find_email, verify_email, find_company_emails
from .rate_limiter import check_rate_limit, increment_usage, FREE_LIMIT, STRIPE_LINK


server = Server("email-finder")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available email finding tools."""
    return [
        Tool(
            name="find_email",
            description="Find the most likely email address for a person given their name and company domain. "
                        f"Free limit: {FREE_LIMIT} lookups. See https://rumblingb.github.io/email-finder-mcp for pro access.",
            inputSchema={
                "type": "object",
                "properties": {
                    "first_name": {
                        "type": "string",
                        "description": "First name of the person",
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Last name of the person",
                    },
                    "domain": {
                        "type": "string",
                        "description": "Company domain (e.g., example.com)",
                    },
                    "api_key": {
                        "type": "string",
                        "description": "Optional PRO API key for rate limit bypass. Get one at " + STRIPE_LINK,
                    },
                },
                "required": ["first_name", "last_name", "domain"],
            },
        ),
        Tool(
            name="verify_email",
            description="Verify if an email address exists using MX record lookup and SMTP verification. "
                        f"Free limit: {FREE_LIMIT} verifications. See https://rumblingb.github.io/email-finder-mcp for pro access.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Email address to verify",
                    },
                    "api_key": {
                        "type": "string",
                        "description": "Optional PRO API key for rate limit bypass. Get one at " + STRIPE_LINK,
                    },
                },
                "required": ["email"],
            },
        ),
        Tool(
            name="find_company_emails",
            description="Find common email patterns and formats used at a company domain. "
                        f"Free limit: {FREE_LIMIT} lookups. See https://rumblingb.github.io/email-finder-mcp for pro access.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Company name (e.g., Acme Corp)",
                    },
                    "domain": {
                        "type": "string",
                        "description": "Company domain (optional - will guess from name if not provided)",
                    },
                    "api_key": {
                        "type": "string",
                        "description": "Optional PRO API key for rate limit bypass. Get one at " + STRIPE_LINK,
                    },
                },
                "required": ["company_name"],
            },
        ),
        Tool(
            name="check_rate_limit",
            description=f"Check remaining free API calls. Free limit is {FREE_LIMIT}. Upgrade at {STRIPE_LINK}",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_info": {
                        "type": "string",
                        "description": "Client identifier (IP, username, or session ID) for tracking usage",
                    },
                    "api_key": {
                        "type": "string",
                        "description": "Optional PRO API key. If valid, shows unlimited access.",
                    },
                },
                "required": ["client_info"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    client_info = arguments.get("client_info", "anonymous")
    api_key = arguments.get("api_key", None)

    # Check rate limit for all non-check_rate_limit tools
    if name != "check_rate_limit":
        # Use client_id from api_key if provided, otherwise from arguments
        rl_client = api_key or str(arguments)
        rate_result = check_rate_limit(rl_client, api_key)

        if not rate_result["allowed"]:
            return [TextContent(
                type="text",
                text=f"Rate limit exceeded. {rate_result['message']}\n\n"
                     f"Upgrade to PRO at: {STRIPE_LINK}\n"
                     f"Free limit: {FREE_LIMIT} lookups"
            )]

        # Track usage for free tier
        if not rate_result["is_pro"]:
            increment_usage(rl_client)

    if name == "find_email":
        return await handle_find_email(arguments)
    elif name == "verify_email":
        return await handle_verify_email(arguments)
    elif name == "find_company_emails":
        return await handle_find_company_emails(arguments)
    elif name == "check_rate_limit":
        return await handle_check_rate_limit(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def handle_find_email(args: dict) -> list[TextContent]:
    """Handle find_email tool call."""
    first_name = args.get("first_name", "")
    last_name = args.get("last_name", "")
    domain = args.get("domain", "")

    result = find_email(first_name, last_name, domain)

    if result.get("error"):
        return [TextContent(type="text", text=f"Error: {result['error']}")]

    output = (
        f"Email Finder Results\n"
        f"{'=' * 50}\n"
        f"Name: {first_name} {last_name}\n"
        f"Domain: {domain}\n"
        f"Most Likely Email: {result['email']}\n"
        f"Confidence: {result['confidence']}\n\n"
        f"All Generated Patterns:\n"
    )
    for i, pattern in enumerate(result.get("all_patterns", []), 1):
        marker = "  ->" if pattern == result["email"] else "    "
        output += f"{marker} {i}. {pattern}\n"

    return [TextContent(type="text", text=output)]


async def handle_verify_email(args: dict) -> list[TextContent]:
    """Handle verify_email tool call."""
    email = args.get("email", "")

    result = verify_email(email)

    status_icon = {
        "valid": "VALID",
        "invalid": "INVALID",
        "unknown": "UNKNOWN",
    }.get(result["verdict"], "UNKNOWN")

    output = (
        f"Email Verification Results\n"
        f"{'=' * 50}\n"
        f"Email: {result['email']}\n"
        f"Verdict: {status_icon}\n"
        f"Format Valid: {'Yes' if result['format_valid'] else 'No'}\n"
        f"MX Record: {result['mx_record'] or 'Not found'}\n"
        f"SMTP Verified: {'Yes' if result['smtp_verified'] else 'No'}\n\n"
        f"Details:\n"
    )
    for detail in result["details"]:
        output += f"  - {detail}\n"

    return [TextContent(type="text", text=output)]


async def handle_find_company_emails(args: dict) -> list[TextContent]:
    """Handle find_company_emails tool call."""
    company_name = args.get("company_name", "")
    domain = args.get("domain", None)

    result = find_company_emails(company_name, domain)

    if result.get("error"):
        return [TextContent(type="text", text=f"Error: {result['error']}")]

    output = (
        f"Company Email Patterns\n"
        f"{'=' * 50}\n"
        f"Company: {result['company']}\n"
        f"Domain: {result['domain']}\n"
        f"MX Active: {'Yes' if result['mx_record']['exists'] else 'No/Unknown'}\n\n"
        f"Common Email Patterns:\n"
    )
    for p in result["patterns"]:
        output += f"  [{p['frequency']}] {p['example']}\n"
    output += (
        f"\nPro Tip: Use find_email with first/last name + domain to get exact addresses.\n"
        f"Upgrade to PRO at: {STRIPE_LINK}"
    )

    return [TextContent(type="text", text=output)]


async def handle_check_rate_limit(args: dict) -> list[TextContent]:
    """Handle check_rate_limit tool call."""
    client_info = args.get("client_info", "anonymous")
    api_key = args.get("api_key", None)

    result = check_rate_limit(client_info, api_key)

    if result["is_pro"]:
        output = (
            f"Rate Limit Status\n"
            f"{'=' * 50}\n"
            f"Status: PRO (Unlimited)\n"
            f"Thank you for being a PRO subscriber!\n"
        )
    else:
        output = (
            f"Rate Limit Status\n"
            f"{'=' * 50}\n"
            f"Tier: Free\n"
            f"Remaining: {result['remaining']}/{FREE_LIMIT}\n"
            f"Upgrade to PRO at: {STRIPE_LINK}\n"
        )

    return [TextContent(type="text", text=output)]
