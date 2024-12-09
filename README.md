
# SEO Link Analyzer

SEO Link Analyzer is a Python-based tool designed to analyze and audit SEO-related aspects of web pages. It crawls internal links, checks metadata, evaluates broken links, and generates detailed reports in Google Sheets.

## Features
- **Crawl Internal Links**: Extracts and analyzes internal links from a given URL.
- **Metadata Analysis**: Collects metadata like titles, descriptions, and H1 tags.
- **Broken Link Checker**: Identifies and reports broken or non-responsive links.
- **Sitemap Integration**: Checks for sitemap files and validates URLs against them.
- **Google Sheets Integration**: Exports results directly to a Google Spreadsheet for easy sharing and review.

## Prerequisites
- Python 3.7 or higher.
- A Google Service Account JSON file for Sheets API authentication.
- Required Python libraries (install using `requirements.txt`).

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/felixsandstrom/seo-link-analyzer.git
cd seo-link-analyzer
```

### 2. Create a Virtual Environment
```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Update the Environment Variables
A `.env` file is already included in the project with placeholder values. You need to update this file with your own credentials.

#### Steps:
1. **Locate the `.env` File**:
   In the root directory of the project, you'll find a file named `.env`.

2. **Update the Variables**:
   Open the `.env` file and replace the placeholder values with your own:

   ```plaintext
   SERVICE_ACCOUNT_FILE=/path/to/your/service-account.json
   DEFAULT_EMAIL=your-email@example.com

Replace the placeholders with the path to your Google Service Account JSON file and your email address.

### 5. Run the Application
```bash
python seo_link_analyzer.py
```

## Usage
1. Enter the URL of the page you want to scan. You can start the URL with `www`, or use `http://` or `https://`.
2. Enter the email address to share the Google Spreadsheet containing the results. If no email is provided, the default email from `.env` will be used.
3. The tool will:
   - Extract internal links.
   - Analyze metadata for each link.
   - Check for broken links.
   - Generate a Google Spreadsheet with the results.

## Output
- A Google Spreadsheet with two sheets:
  1. **SEO Analysis**: Contains metadata and sitemap information for all crawled links.
  2. **Broken Links**: Lists all broken or non-responsive links.

## Example Commands
### Default URL and Default Email:
```bash
python seo_link_analyzer.py
```

### Custom URL and Email:
```bash
Enter the URL of the page to scan: www.example.com
Enter email to share the spreadsheet with: your-email@example.com
```

## License
This project is licensed under the MIT License.

## Author
**Felix Sandström**  
Specialist in Web Development and Data Analysis.

For any inquiries, feel free to contact me!
