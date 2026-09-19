# Mini URL Shortener (CLI & Flask Web App)

A robust, full-featured URL Shortener built in Python supporting both **Track A: 1st Year (CLI-based)** and **Track B: 2nd Year (Flask Web App)** with persistent SQLite storage, analytics, custom aliases, and zero-dependency core CLI.

---

## Features

### Track A: CLI Core Requirements
- **URL Shortening (`shorten`)**: Generates clean, unique Base62 short codes (e.g., `PeeF3m`) for valid web URLs.
- **Persistent Storage**: Uses Python's built-in `sqlite3` database (`urls.db`). URL mappings persist across application and terminal sessions.
- **URL Resolution (`resolve`)**: Looks up short codes and returns original destination URLs.
- **Listing (`list`)**: Displays all shortened URLs in a formatted, aligned ASCII table.
- **Input Validation & Error Handling**: Strict URL format checking, invalid protocol rejection, and graceful handling of missing or duplicate codes.
- **Zero External Dependencies for CLI**: Implemented entirely with the Python Standard Library (`sqlite3`, `argparse`, `urllib`, `webbrowser`, `secrets`, `json`, `csv`, `unittest`).

### Track B: Flask Web Application & Deployment
- **Interactive Modern UI**: Beautiful responsive web interface at `http://localhost:5000` (`templates/index.html`).
- **HTTP 302 Redirection**: Accessing `http://localhost:5000/<short_code>` immediately redirects to the original destination.
- **RESTful API**: Endpoints for `/api/shorten`, `/api/stats/<short_code>`, and `/api/urls`.
- **Cloud Deployment Ready**: Includes `requirements.txt` and `Procfile` ready for free 1-click deployment on Render, Railway, or PythonAnywhere.

### Bonus Features (Included)
- **Custom Alias Support (`--alias`)**: Create user-defined aliases (e.g., `shorten https://github.com --alias gh`). Checks for length, character validity, and prevents collision with existing codes.
- **Click Tracking**: Automatically tracks the total number of times each short code has been resolved, including timestamps.

### Creative Additions (Extra Points)
- **Direct Browser Opening (`--open`)**: Option to automatically launch the resolved URL in the user's default web browser using `webbrowser`.
- **Analytics & Statistics (`stats`)**: Detailed breakdown for any code (click count, creation timestamp, last accessed timestamp).
- **Interactive REPL Shell (`interactive`)**: Run commands continuously in an interactive prompt (`shortener>`) without restarting the CLI.
- **Data Export (`export`)**: Export your URL registry into structured JSON or CSV format.
- **Record Deletion (`delete`)**: Easily remove outdated or temporary short codes from storage.
- **Automated Test Suite**: 13 unit tests covering unit logic, validation, edge cases, cross-session persistence, and web routes.

---

## Project Structure

```
mini-url-shortener/
├── main.py              # CLI entry point, argument parsing & interactive REPL
├── app.py               # Flask Web Application & HTTP 302 Redirect Server
├── templates/
│   └── index.html       # Responsive web interface
├── shortener.py         # Business logic: validation, Base62 generator, alias rules
├── storage.py           # SQLite database persistence layer (urls.db)
├── test_shortener.py    # CLI automated test suite using unittest
├── test_app.py          # Flask web app test suite
├── requirements.txt     # Dependencies for optional web app deployment
├── Procfile             # Process file for Render / Railway cloud hosting
├── urls.db              # SQLite database (auto-generated on first run)
├── .gitignore           # Git ignore file
└── README.md            # Project documentation and usage guide
```

---

## Installation & Setup

### Prerequisites
- Python 3.8+ installed.
- No external packages (`pip`) required!

### Setup
Clone or navigate to the repository directory:
```bash
git clone <your-repo-url>
cd mini-url-shortener
```

Verify Python is available:
```bash
python --version
```

---

## Usage Guide & Sample Outputs

### 1. Shorten a URL
Accepts any valid URL and outputs a 6-character short code.

```bash
python main.py shorten "https://www.python.org"
```
**Sample Output:**
```
[SUCCESS] Short Code: PeeF3m
          Original URL: https://www.python.org
```

### 2. Shorten with Custom Alias (Bonus)
Pass `--alias` or `-a` to assign a custom short code:

```bash
python main.py shorten "https://github.com" --alias gh
```
**Sample Output:**
```
[SUCCESS] Short Code: gh
          Original URL: https://github.com
          Custom Alias: Yes
```

### 3. Resolve a Short Code
Looks up the short code, returns the original destination URL, and increments its click counter:

```bash
python main.py resolve gh
```
**Sample Output:**
```
[RESOLVED] https://github.com
```

#### Open in Default Browser (Creative Feature)
Add `--open` or `-o` to launch the link directly in your browser:
```bash
python main.py resolve gh --open
```
**Sample Output:**
```
[RESOLVED] https://github.com
Opening 'https://github.com' in your default browser...
```

### 4. List All Stored URLs
Renders an aligned ASCII table of all mappings. You can sort by `created_at`, `clicks`, or `code`.

```bash
python main.py list
```
**Sample Output:**
```
Stored URLs (2 total, sorted by created_at desc):
+------------+--------+---------------------+------------------------+
| Short Code | Clicks | Created At (UTC)    | Original URL           |
+------------+--------+---------------------+------------------------+
| gh         | 2      | 2026-09-19 07:30:29 | https://github.com     |
| PeeF3m     | 0      | 2026-09-19 07:29:41 | https://www.python.org |
+------------+--------+---------------------+------------------------+
```

Sort by click popularity:
```bash
python main.py list --sort clicks
```

### 5. Inspect Statistics & Analytics (Creative Feature)
Inspect click count and access timestamps for any specific code:

```bash
python main.py stats gh
```
**Sample Output:**
```
=============================================
 Statistics for Code: gh
=============================================
 Original URL  : https://github.com
 Total Clicks  : 2
 Created At    : 2026-09-19 07:30:29 UTC
 Last Accessed : 2026-09-19 07:30:57
=============================================
```

### 6. Delete a URL
Remove an unwanted mapping:
```bash
python main.py delete PeeF3m
```
**Sample Output:**
```
[SUCCESS] Successfully deleted short code 'PeeF3m'.
```

### 7. Export Database to JSON or CSV
Export all records to a file for backup or external reporting:

```bash
# Export to JSON
python main.py export --format json --output urls_backup.json

# Export to CSV
python main.py export --format csv --output urls_backup.csv
```

---

## Interactive REPL Mode

For quick successive operations without repeatedly typing `python main.py`, start the interactive shell by running `main.py` without arguments:

```bash
python main.py
```
or:
```bash
python main.py interactive
```

**Interactive Session Example:**
```
============================================================
  Welcome to Mini URL Shortener (Interactive Shell)
  Type 'help' for available commands or 'exit' / 'quit' to close.
============================================================

shortener> shorten https://docs.python.org/3/ --alias pydocs
[SUCCESS] Short Code: pydocs

shortener> resolve pydocs
[RESOLVED] https://docs.python.org/3/

shortener> stats pydocs

=============================================
 Statistics for Code: pydocs
=============================================
 Original URL  : https://docs.python.org/3/
 Total Clicks  : 1
 Created At    : 2026-09-19 07:35:10 UTC
 Last Accessed : 2026-09-19 07:35:15
=============================================

shortener> exit
Goodbye!
```

---

## Error Handling & Edge Cases

| Scenario | Behavior / Response |
|---|---|
| **Invalid URL format** | Rejects malformed strings (`[ERROR] Invalid domain name: '...'`) |
| **Missing protocol** | Auto-prefixes `https://` if valid domain is provided |
| **Duplicate Custom Alias** | Blocks collision (`[ERROR] Alias 'gh' is already in use.`) |
| **Reserved Alias Word** | Disallows system names (`shorten`, `resolve`, `admin`, etc.) |
| **Non-existent Short Code** | Cleanly reports missing code (`[ERROR] Short code '...' not found.`) |
| **Empty inputs** | Graceful prompt explaining proper argument usage |

---

## Database Schema (`urls.db`)

The SQLite database table `urls` is automatically created on first execution:

```sql
CREATE TABLE IF NOT EXISTS urls (
    code TEXT PRIMARY KEY,
    original_url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    clicks INTEGER NOT NULL DEFAULT 0,
    last_accessed TEXT
);

CREATE INDEX IF NOT EXISTS idx_urls_original ON urls(original_url);
```

---

## Running Automated Tests

Run the full unit test suite using Python's built-in test runner:

```bash
python -m unittest discover -s . -p "test_*.py" -v
```

**Test Output:**
```
test_alias_validation (test_shortener.TestURLShortener.test_alias_validation) ... ok
test_clicks_tracking (test_shortener.TestURLShortener.test_clicks_tracking) ... ok
test_custom_alias (test_shortener.TestURLShortener.test_custom_alias) ... ok
test_delete_url (test_shortener.TestURLShortener.test_delete_url) ... ok
test_duplicate_alias_rejected (test_shortener.TestURLShortener.test_duplicate_alias_rejected) ... ok
test_list_urls (test_shortener.TestURLShortener.test_list_urls) ... ok
test_persistence_across_connections (test_shortener.TestURLShortener.test_persistence_across_connections) ... ok
test_shorten_and_resolve (test_shortener.TestURLShortener.test_shorten_and_resolve) ... ok
test_url_validation_invalid (test_shortener.TestURLShortener.test_url_validation_invalid) ... ok
test_url_validation_valid (test_shortener.TestURLShortener.test_url_validation_valid) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.410s

OK
```
