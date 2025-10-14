# HD Contract Outlook Agent

Automatically monitors your Outlook inbox for HD contract emails, extracts PDF attachments, parses contract data, and writes results to Google Sheets.

## Features

- Monitors Outlook/Microsoft 365 mailbox via Microsoft Graph API
- Searches for emails by subject (e.g., "HD contract")
- Downloads and parses PDF attachments
- Extracts contract data (number, customer name, phone, email, address, etc.)
- Writes structured data to Google Sheets
- Runs continuously or on a schedule
- Marks processed emails as read (optional)
- Deploy to Render.com with one click

## Architecture

```
Outlook Inbox → Microsoft Graph API → PDF Parser → Google Sheets
     ↓
  HD Contract PDFs
```

## Quick Start

### 1. Clone & Install

```bash
cd hd-contract-agent
pip install -r requirements.txt
```

### 2. Setup Azure App Registration

You need to register an app in Azure to access Outlook via Microsoft Graph API.

#### Step-by-Step Azure Setup

1. Go to [Azure Portal](https://portal.azure.com) → **App registrations**

2. Click **New registration**
   - **Name**: HDContractAgent
   - **Supported account types**: Single tenant (or Multi-tenant if needed)
   - **Redirect URI**: Web → `http://localhost:5000`
   - Click **Register**

3. **Note these values** (you'll need them):
   - Application (client) ID
   - Directory (tenant) ID

4. Create a **client secret**:
   - Go to **Certificates & secrets** → **Client secrets**
   - Click **New client secret**
   - Description: "HDContractAgent secret"
   - Expires: 24 months (or your preference)
   - Click **Add**
   - **Copy the secret value immediately** (you won't see it again!)

5. Set **API permissions**:
   - Go to **API permissions** → **Add a permission**
   - Select **Microsoft Graph** → **Delegated permissions**
   - Add these permissions:
     - `Mail.Read`
     - `Mail.ReadWrite`
     - `offline_access`
   - Click **Add permissions**
   - Click **Grant admin consent** (if you're an admin)

### 3. Setup Google Sheets

#### Option A: Service Account (Recommended for Production)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or select existing)
3. Enable **Google Sheets API**
4. Create **Service Account**:
   - Go to **IAM & Admin** → **Service Accounts**
   - Click **Create Service Account**
   - Name: "HD Contract Agent"
   - Click **Create and Continue**
   - Role: None needed (we'll share the sheet directly)
   - Click **Done**
5. Create **JSON key**:
   - Click on the service account
   - Go to **Keys** → **Add Key** → **Create new key**
   - Select **JSON** format
   - Download the JSON file
6. **Share your Google Sheet** with the service account email:
   - Open your Google Sheet
   - Click **Share**
   - Add the service account email (looks like: `name@project.iam.gserviceaccount.com`)
   - Give **Editor** access

#### Option B: OAuth (For Local Development)

1. Create OAuth credentials in Google Cloud Console
2. Download `credentials.json`
3. Run the setup script to get `token.json`

### 4. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Microsoft Graph API (from Azure Portal)
MS_CLIENT_ID=your-client-id-from-azure
MS_CLIENT_SECRET=your-client-secret-from-azure
MS_TENANT_ID=your-tenant-id-from-azure

# Email search configuration
SEARCH_QUERY=subject:"HD contract"

# Google Sheets
SPREADSHEET_ID=your-spreadsheet-id-from-url

# Google credentials (paste entire JSON on one line, or use file)
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}

# Optional settings
MARK_AS_READ=true
```

**Finding your Spreadsheet ID:**
From the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`

### 5. Setup Sheet Headers

```bash
python outlook_agent.py --setup-headers
```

This creates column headers in your sheet.

### 6. Test Locally

```bash
# Run once
python outlook_agent.py

# Run continuously (checks every 5 minutes)
python outlook_agent.py --loop --interval 300
```

## Authentication Notes

### Microsoft Graph Authentication

The agent uses **client credentials flow** (app-only authentication) which is best for automated background processes.

**First-time setup:**
- You may need to authenticate interactively once
- The agent will cache your credentials
- Subsequent runs will use the cached token

**For headless servers:**
- Use client credentials with `MS_CLIENT_SECRET`
- Or use device code flow (uncomment in `graph_auth.py`)

### Google Sheets Authentication

**Service Account (Recommended):**
- No user interaction needed
- Perfect for automation
- Share the sheet with service account email

**OAuth Token:**
- Requires initial user login
- Token expires after 7 days
- Good for local development

## Deployment

### Deploy to Render.com

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/your-username/hd-contract-agent.git
   git push -u origin main
   ```

2. **Create Render Service:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click **New** → **Background Worker** (or **Cron Job**)
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`

3. **Set Environment Variables:**
   In Render dashboard, add:
   - `MS_CLIENT_ID`
   - `MS_CLIENT_SECRET`
   - `MS_TENANT_ID`
   - `SPREADSHEET_ID`
   - `GOOGLE_CREDENTIALS_JSON` (paste entire JSON)

4. **Deploy:**
   - Click **Create Service**
   - Render will build and start your agent

### Deploy with Docker

```bash
docker build -t hd-contract-agent .
docker run -d \
  -e MS_CLIENT_ID=your-id \
  -e MS_CLIENT_SECRET=your-secret \
  -e MS_TENANT_ID=your-tenant \
  -e SPREADSHEET_ID=your-sheet-id \
  -e GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}' \
  hd-contract-agent
```

## Usage

### Command Line Options

```bash
# Run once and exit
python outlook_agent.py

# Run continuously (loop mode)
python outlook_agent.py --loop

# Custom check interval (seconds)
python outlook_agent.py --loop --interval 600

# Custom search query
python outlook_agent.py --search 'subject:"contracts"'

# Mark processed emails as read
python outlook_agent.py --mark-read

# Setup sheet headers
python outlook_agent.py --setup-headers
```

### Configuration Options

**Environment Variables:**

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MS_CLIENT_ID` | Azure app client ID | Yes | - |
| `MS_CLIENT_SECRET` | Azure app secret | Yes* | - |
| `MS_TENANT_ID` | Azure tenant ID | Yes | - |
| `SPREADSHEET_ID` | Google Sheet ID | Yes | - |
| `GOOGLE_CREDENTIALS_JSON` | Service account JSON | Yes* | - |
| `SEARCH_QUERY` | Email search query | No | `subject:"HD contract"` |
| `MARK_AS_READ` | Mark processed emails | No | `false` |

\* Either client secret or interactive auth required for Graph API
\* Either credentials JSON or token.json required for Sheets

## Customizing PDF Parsing

The PDF parser in `pdf_parser.py` uses regex patterns to extract data. Customize for your contract format:

```python
self.patterns = {
    'contract_number': [
        r'Contract\s*#?\s*:?\s*([A-Z0-9\-]+)',
        # Add your patterns here
    ],
    # Add more fields...
}
```

## Monitoring & Logs

### Render Logs

View logs in Render dashboard:
- Go to your service
- Click **Logs** tab
- Real-time streaming logs

### Local Logs

The agent prints detailed logs:
- Email processing status
- PDF parsing results
- Sheets writing confirmations
- Error messages

## Troubleshooting

### Authentication Issues

**Microsoft Graph 401 Unauthorized:**
- Check client ID, secret, and tenant ID
- Verify API permissions in Azure Portal
- Ensure admin consent was granted
- Token may have expired - restart the agent

**Google Sheets 403 Forbidden:**
- Verify spreadsheet is shared with service account
- Check SPREADSHEET_ID is correct
- Ensure service account has Editor access

### No Emails Found

- Check SEARCH_QUERY matches your email subjects
- Verify emails exist in the mailbox
- Try simpler query: `subject:"contract"`
- Check email is in Inbox (not Archive/Spam)

### PDF Parsing Errors

- Ensure PDFs are text-based (not scanned images)
- Customize patterns in `pdf_parser.py` for your format
- Check PDF structure with: `python pdf_parser.py sample.pdf`

### Deployment Issues

**Render build fails:**
- Check Python version (3.11+ recommended)
- Verify requirements.txt is correct
- Check environment variables are set

**Agent crashes in production:**
- Check logs for errors
- Verify credentials are valid
- Test authentication locally first

## File Structure

```
hd-contract-agent/
├── outlook_agent.py       # Main agent script
├── graph_auth.py          # Microsoft Graph authentication
├── pdf_parser.py          # PDF parsing logic
├── sheets_writer.py       # Google Sheets integration
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment config
├── Dockerfile            # Docker container config
├── .env.example          # Environment template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## Development

### Run Tests

```bash
# Test Graph authentication
python graph_auth.py

# Test Sheets integration
python sheets_writer.py

# Test PDF parser
python pdf_parser.py sample.pdf
```

### Debug Mode

Add debug prints in the code, or use Python debugger:

```bash
python -m pdb outlook_agent.py
```

## Security Notes

- Never commit `.env` or credential files to Git
- Use environment variables for secrets
- Rotate client secrets regularly
- Review API permissions (principle of least privilege)
- Enable MFA on Azure and Google accounts

## Support & Contributing

Found a bug? Have a feature request? Open an issue!

## License

MIT License - feel free to use and modify
