# Email Finder MCP Server

Find and verify email addresses using MCP (Model Context Protocol).

Part of the [Pickaxes](https://github.com/Rumblingb/email-finder-mcp) suite — one-trick-pony MCP servers that each solve one problem well.

## 🚀 Features

- **find_email** — Find likely email addresses from name + domain using pattern guessing
- **verify_email** — Verify email addresses via MX lookup + SMTP handshake
- **find_company_emails** — Discover email patterns used at any company
- **check_rate_limit** — Check remaining free API calls

## 🎯 Pricing

- **Free**: 50 lookups/month
- **PRO**: $19/month — unlimited lookups + priority support

## 🛠 Installation

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
git clone https://github.com/Rumblingb/email-finder-mcp.git
cd email-finder-mcp
python3 -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env  # Edit with your config
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "email-finder": {
      "command": "python3",
      "args": ["-m", "email_finder_mcp"],
      "cwd": "/path/to/email-finder-mcp",
      "env": {
        "STRIPE_LINK": "https://buy.stripe.com/your_link",
        "PRO_KEYS": "your-pro-key-here"
      }
    }
  }
}
```

### Cursor Configuration

In Cursor settings > MCP Servers, add:

```
Command: python3 -m email_finder_mcp
Working Directory: /path/to/email-finder-mcp
```

## 🔧 Usage

```python
# Find an email
find_email(first_name="John", last_name="Doe", domain="acme.com")

# Verify an email
verify_email(email="john.doe@acme.com")

# Find company patterns
find_company_emails(company_name="Acme Corp", domain="acme.com")

# Check limits
check_rate_limit(client_info="user@example.com")
```

## 💰 PRO Access

Get unlimited access by subscribing at [buy.stripe.com](https://buy.stripe.com/fZu14p8XtgAk6DKa791oI0D)

Then pass your API key to any tool:
```python
find_email(first_name="John", last_name="Doe", domain="acme.com", api_key="your-pro-key")
```

## 🏗 Project Structure

```
email-finder-mcp/
├── src/
│   └── email_finder_mcp/
│       ├── __init__.py
│       ├── __main__.py      # Entry point
│       ├── server.py         # MCP server & tools
│       ├── email_utils.py    # Email finding & verification
│       └── rate_limiter.py   # Rate limiting & PRO keys
├── index.html               # Landing page
├── .env.example
├── pyproject.toml
└── README.md
```

## 📄 License

MIT
