# Payroll Automation for Water Filtration Sales

Automated system to process signed water filtration contracts from Google Drive and update sales rep spreadsheets.

## Features

- **Automatic Contract Processing**: Monitors Google Drive folder for new signed contracts
- **PDF Data Extraction**: Extracts customer info, equipment, pricing, and sales rep from contracts
- **Fuzzy Name Matching**: Intelligently matches sales rep names (handles nicknames and variations)
- **Multi-Sheet Updates**: Updates individual rep sheets, main tracking sheet, and backup sheet
- **Continuous Monitoring**: Runs automatically to process new contracts as they arrive

## Workflow

1. Signed contract PDF is deposited into Google Drive folder
2. System detects new contract
3. Extracts data: sales rep, customer name, phone, address, equipment, price, financing
4. Matches sales rep name to existing spreadsheet
5. Updates rep's individual spreadsheet
6. Updates main tracking spreadsheet
7. If rep not found, adds to backup spreadsheet

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Google Cloud Project with Drive and Sheets APIs enabled
- Google OAuth credentials

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Google API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Google Drive API** and **Google Sheets API**
4. Create OAuth 2.0 credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Download the JSON file and save as `credentials.json` in project root
5. On first run, you'll be prompted to authorize the application

### 4. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
DRIVE_FOLDER_ID=115Pg2idzGItjkxamjwV5jP4UFExrmcHL
MAIN_SPREADSHEET_ID=  # Will be auto-generated on first run
BACKUP_SPREADSHEET_ID=  # Will be auto-generated on first run
CHECK_INTERVAL=300  # Check every 5 minutes
```

### 5. Run the Automation

**Test with a single contract:**
```bash
python main.py /path/to/contract.pdf
```

**Run continuous monitoring:**
```bash
python main.py
```

## Project Structure

```
payroll-automation/
├── main.py                 # Main orchestrator
├── pdf_parser.py          # Contract PDF parser
├── drive_monitor.py       # Google Drive monitoring
├── sheets_updater.py      # Google Sheets updater
├── name_matcher.py        # Fuzzy name matching
├── google_auth.py         # Google API authentication
├── config.py              # Configuration (rep mappings)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── credentials.json       # Google OAuth credentials (download from Cloud Console)
├── token.pickle          # Auto-generated OAuth token
└── processed_files.txt   # Tracks processed contracts
```

## Spreadsheet Formats

### Individual Rep Spreadsheet
| Date | Customer Name | Phone Number | Customer Address | Equipment | Sold Price | Installed | Fin By | Fin Status | Comments | Commission | Date | Contract |
|------|--------------|-------------|-----------------|-----------|-----------|----------|--------|-----------|----------|-----------|------|----------|

### Main Spreadsheet
| Date | Sales Rep | Customer Name | Equipment | Sale Price | Lead/PO# | Contract Link |
|------|-----------|--------------|-----------|-----------|----------|---------------|

### Backup Spreadsheet
Same as individual rep sheet plus "Sales Rep Name" column for unmatched reps.

## Sales Rep Mapping

Edit `config.py` to add/modify sales rep to spreadsheet mappings:

```python
REP_SPREADSHEETS = {
    "Rep Name": "Google_Sheets_ID_Here",
    # ...
}
```

## Running as a Service

### Using systemd (Linux)

Create `/etc/systemd/system/payroll-automation.service`:

```ini
[Unit]
Description=Payroll Automation Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/matt/payroll-automation
ExecStart=/usr/bin/python3 /home/matt/payroll-automation/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable payroll-automation
sudo systemctl start payroll-automation
sudo systemctl status payroll-automation
```

### Using cron

Add to crontab:
```bash
*/5 * * * * cd /home/matt/payroll-automation && python3 main.py >> /var/log/payroll-automation.log 2>&1
```

## Troubleshooting

### Authentication Issues
- Delete `token.pickle` and re-authenticate
- Ensure `credentials.json` is in project root
- Check API is enabled in Google Cloud Console

### PDF Parsing Issues
- Verify contract format matches expected structure
- Check PDF is not encrypted or password-protected
- Update regex patterns in `pdf_parser.py` if format changes

### Name Matching Issues
- Check rep name spelling in contract
- Adjust fuzzy matching threshold in `name_matcher.py`
- Add name variations to `config.py`

## Logs

View logs:
```bash
# If running as systemd service
sudo journalctl -u payroll-automation -f

# If running manually
python main.py 2>&1 | tee automation.log
```

## Development

### Test PDF Parser
```bash
python pdf_parser.py /path/to/contract.pdf
```

### Test Name Matcher
```bash
python name_matcher.py
```

### Test Sheets Updater
```bash
python sheets_updater.py
```

### Monitor Drive Folder
```bash
python drive_monitor.py <FOLDER_ID>
```

## License

Proprietary - Internal Use Only
