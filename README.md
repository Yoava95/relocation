# Job Search Automation

This project scrapes multiple job boards for product management roles in Israel.

## Requirements
- Python 3.10+
- Dependencies from `requirements.txt`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage
Adjust environment variables as needed by copying `config.example.env` to `.env` and editing the values.
Run the main script:

```bash
python main.py
```

The script collects new job postings, sends a summary via Telegram and allows responding with the indices of interesting jobs.
