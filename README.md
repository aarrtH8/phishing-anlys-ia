# PhishHunter

Automated Phishing Analysis Engine using Playwright and Python.

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
   *Note: For the full analysis features, you need `java` installed for the Java forensics module.*

2. **External Tools:**
   - **CFR Decompiler**: Download `cfr.jar` (e.g., from [cfr.org](https://www.benf.org/other/cfr/)) and place it in `tools/cfr.jar`.
   
3. **Resources:**
   - **Logos**: Place brand logos (PNG/JPG) in `resources/logos/` for visual brand detection (e.g., `paypal.png`, `microsoft.png`).

## Usage

### Running Locally
```bash
python main.py https://example-phishing-site.com
```

### Running with Docker
1. Build the image:
   ```bash
   docker build -t phishhunter .
   ```
2. Run analysis:
   ```bash
   docker run -v $(pwd)/output:/app/output phishhunter https://example-phishing-site.com
   ```

## Output
Results are saved to `output/report.json`.
- Redirect chain
- Extracted files (JARs, JS) in `output/dump/`
- Screenshot `output/screenshot.png`
- Visual analysis and obfuscation flags
