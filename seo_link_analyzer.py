import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import json


# Load environment variables from .env file
load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')  # Path to your Google service account JSON file
DEFAULT_EMAIL = os.getenv('DEFAULT_EMAIL')  # Default email to share the spreadsheet

if not SERVICE_ACCOUNT_FILE or not DEFAULT_EMAIL:
    raise ValueError("Please set SERVICE_ACCOUNT_FILE and DEFAULT_EMAIL in your .env file.")


def extract_clickable_links_recursive(base_url, max_depth=2, visited=None, depth=0):
    if visited is None:
        visited = set()  # Track visited URLs to avoid loops

    links = []
    base_domain = urlparse(base_url).netloc  # Extract the domain from the base URL

    # If already visited this URL, return to avoid revisiting
    if base_url in visited:
        # print(f"Skipping already visited URL: {base_url}")
        return links
    visited.add(base_url)  # Mark the current URL as visited

    # print(f"Visiting: {base_url} at depth {depth}")

    # Fetch the page
    try:
        response = requests.get(base_url, allow_redirects=True)
        if response.status_code != 200:
            # print(f"Unable to access {base_url}")
            return links
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract links from the current page
        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href']

            # Exclude internal anchor links (those containing "#")
            if "#" in link:
                continue

            # Use urljoin to handle relative URLs
            full_link = urljoin(base_url, link)
            link_domain = urlparse(full_link).netloc  # Extract the domain from the link

            # Only include internal links (i.e., links that share the same domain as the base URL)
            if link_domain == base_domain and full_link not in visited:
                # print(f"Found internal link: {full_link}")
                links.append((full_link, base_url))

        # If max depth is not reached, recursively fetch links from these internal links
        if max_depth > 0:
            for internal_link, parent_url in links.copy():  # Use a copy of links to avoid modifying the list while iterating
                more_links = extract_clickable_links_recursive(internal_link, max_depth - 1, visited, depth + 1)
                links.extend(more_links)

    except requests.RequestException as e:
        print(f"Error accessing {base_url}: {e}")

    return links


def get_meta_data(link):
    response = requests.get(link)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Extract the title
    title = soup.find("title").get_text() if soup.find("title") else None
    # print(f"Title: {title}")
    
    # Handle the case when title is None
    title_length = len(title) if title else 0
    
    # Extract the meta description
    meta_description = soup.find("meta", {"name": "description"})
    meta_description = meta_description.get("content") if meta_description else None
    # print(f"Meta Description: {meta_description}")
    meta_description_length = len(meta_description) if meta_description else 0
    
    # Extract H1 title
    h1_title = soup.find("h1").get_text() if soup.find("h1") else None
    # print(f"H1 Title: {h1_title}")

    # Extract canonical tag
    canonical_link = soup.find("link", {"rel": "canonical"})
    canonical_url = canonical_link.get("href") if canonical_link else None
    # print(f"Canonical URL: {canonical_url}")

    # Extract Breadcrumbs from all JSON-LD blocks
    breadcrumbs = []
    json_ld_scripts = soup.find_all("script", {"type": "application/ld+json"})
    
    for script in json_ld_scripts:
        try:
            json_ld_data = json.loads(script.string)
            # print(f"Parsed JSON-LD data: {json_ld_data}")
            if json_ld_data.get("@type") == "BreadcrumbList":
                for item in json_ld_data["itemListElement"]:
                    position = item.get("position")
                    name = item.get("name")
                    url = item.get("item")  # Get the URL of the breadcrumb
                    # print(f"Breadcrumb position: {position}, name: {name}, URL: {url}")
                    breadcrumbs.append(f"{position}: {name} ({url})")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON-LD: {e}")
    
    # Fallback: Check for HTML-based breadcrumbs
    if not breadcrumbs:
        # print("Attempting to extract breadcrumbs from HTML structure.")
        breadcrumb_container = soup.find('nav', {'aria-label': 'breadcrumb'}) or soup.find('ul', class_='breadcrumb')
        if breadcrumb_container:
            breadcrumb_items = breadcrumb_container.find_all('li')
            for index, item in enumerate(breadcrumb_items, 1):
                breadcrumb_link = item.find('a')  # Look for <a> tag inside <li>
                if breadcrumb_link:
                    breadcrumb_name = breadcrumb_link.get_text(strip=True)
                    breadcrumb_url = breadcrumb_link.get('href')
                else:
                    breadcrumb_name = item.get_text(strip=True)
                    breadcrumb_url = None
                # print(f"Found HTML breadcrumb: {breadcrumb_name}, URL: {breadcrumb_url}")
                breadcrumbs.append(f"{index}: {breadcrumb_name} ({breadcrumb_url if breadcrumb_url else 'No URL'})")
        else:
            print("No breadcrumbs found in HTML.")
    
    breadcrumbs_text = " > ".join(breadcrumbs) if breadcrumbs else None
    # print(f"Breadcrumbs: {breadcrumbs_text}")

    return title, title_length, meta_description, meta_description_length, h1_title, canonical_url, breadcrumbs_text



def get_sitemap_urls(base_url):
    sitemap_paths = ["/sitemap.xml", "/en/sitemap.xml", "/es/sitemap.xml"]  # List of possible sitemap locations
    all_urls = set()  # To store the URLs from all sitemaps

    for sitemap_path in sitemap_paths:
        sitemap_url = urljoin(base_url, sitemap_path)
        # print(f"Checking sitemap at: {sitemap_url}")
        try:
            response = requests.get(sitemap_url)
            if response.status_code != 200:
                # print(f"Error fetching sitemap at {sitemap_url}, status code: {response.status_code}")
                continue  # Move to the next sitemap in the list if the current one is not found

            soup = BeautifulSoup(response.content, 'xml')

            # Extract the URLs from the sitemap, handling both absolute and relative URLs
            urls = set()
            for url in soup.find_all("url"):
                loc = url.loc.get_text()
                full_url = urljoin(base_url, loc)  # Join with base URL to handle relative paths
                urls.add(full_url)
            
            # print(f"Found URLs in {sitemap_url}: {urls}")
            all_urls.update(urls)  # Add the URLs from this sitemap to the set
        except requests.RequestException as e:
            print(f"Error accessing sitemap at {sitemap_url}: {e}")
            continue  # Move to the next sitemap in case of a request error

    print(f"Collected URLs: {all_urls}")
    return all_urls

def check_for_error_links(links):
    broken_links = []  # Track broken links with their parent URL and status

    for link, parent_url in links:
        try:
            response = requests.get(link)
            if response.status_code == 404:
                print(f"Found 404 error link: {link} on page: {parent_url}")
                broken_links.append((link, parent_url, 404))  # Track broken link, parent URL, and status
            elif response.status_code != 200:
                print(f"Error: {response.status_code} on link: {link} found on page: {parent_url}")
                broken_links.append((link, parent_url, response.status_code))
        except requests.RequestException as e:
            print(f"Request error for link {link} found on page {parent_url}: {e}")
            broken_links.append((link, parent_url, f"Request error: {e}"))

    return broken_links

def scan_and_check_links(url, max_depth=2):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return f"Error: Unable to access {url}"

        clickable_links = extract_clickable_links_recursive(url, max_depth)

        # Check each link for errors and collect broken links
        broken_links = check_for_error_links(clickable_links)

        # Print broken links
        if broken_links:
            print("Broken Links Found:")
            for link, parent_url, status in broken_links:
                print(f"Broken link: {link} (Parent URL: {parent_url}, Status: {status})")
        else:
            print("No broken links found.")


        sitemap_urls = get_sitemap_urls(url)
        main_url_path = urlparse(url).path
        sitemap_relative_paths = {urlparse(sitemap_url).path for sitemap_url in sitemap_urls}

        results = {}
        
        title, title_length, meta_description, meta_description_length, h1_title, canonical_url, breadcrumbs = get_meta_data(url)
        
        results[url] = {
            'link': url,
            'title': title,
            'title_length': title_length,
            'meta_description': meta_description,
            'meta_description_length': meta_description_length,
            'h1_title': h1_title,
            'canonical_url': canonical_url,
            'breadcrumbs': breadcrumbs,
            'in_sitemap': main_url_path in sitemap_relative_paths
        }

        for link_tuple in clickable_links:
            link = link_tuple[0]
            if link not in results:
                title, title_length, meta_description, meta_description_length, h1_title, canonical_url, breadcrumbs = get_meta_data(link)
                link_path = urlparse(link).path
                results[link] = {
                    'link': link,
                    'title': title,
                    'title_length': title_length,
                    'meta_description': meta_description,
                    'meta_description_length': meta_description_length,
                    'h1_title': h1_title,
                    'canonical_url': canonical_url,
                    'breadcrumbs': breadcrumbs,
                    'in_sitemap': link_path in sitemap_relative_paths
                }

        return list(results.values()), broken_links

    except requests.exceptions.RequestException as e:
        return f"Error: {e}"


column_config = {
    "Link": 250,
    "Title": 250,
    "Title Characters": 100,
    "Meta Description": 300,
    "Meta Description Characters": 100,
    "H1 Title": 300,
    "Canonical URL": 250,
    "Breadcrumbs": 300,
    "In Sitemap": 100
}


# Prepare the dynamic requests for column width adjustment
def create_column_width_requests(column_config):
    requests = []
    for index, (column_name, width) in enumerate(column_config.items()):
        request = {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": 0,
                    "dimension": "COLUMNS",
                    "startIndex": index,  # Start index of the column
                    "endIndex": index + 1  # End index of the column
                },
                "properties": {
                    "pixelSize": width  # Set custom width
                },
                "fields": "pixelSize"
            }
        }
        requests.append(request)
    return requests


def create_google_spreadsheet(data, broken_links, email_to_share_with):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    # Step 1: Create the spreadsheet
    spreadsheet = {
        'properties': {
            'title': 'SEO Analysis Results'
        }
    }
    
    spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId,sheets.properties').execute()
    spreadsheet_id = spreadsheet.get('spreadsheetId')
    print(f"Spreadsheet created: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

    # Get the default sheet ID (SEO Analysis sheet)
    sheets = spreadsheet.get('sheets', [])
    meta_data_sheet_id = sheets[0]['properties']['sheetId']  # Default sheet

    # Step 2: Rename the first sheet (default Sheet 1)
    rename_sheets_request = {
        'requests': [
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': meta_data_sheet_id,  # Default sheet id
                        'title': 'SEO Analysis'
                    },
                    'fields': 'title'
                }
            }
        ]
    }
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=rename_sheets_request).execute()

    # Step 3: Add a second sheet 'Broken Links'
    add_sheets_request = {
        'requests': [
            {
                'addSheet': {
                    'properties': {
                        'title': 'Broken Links',
                    }
                }
            }
        ]
    }
    response = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=add_sheets_request).execute()
    
    # Get the ID of the newly created 'Broken Links' sheet
    broken_links_sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']

    # Step 4: Prepare SEO Analysis sheet content
    sheet_data = [["Link", "Title", "Title Characters", "Meta Description", "Meta Description Characters", "H1 Title", "Canonical URL", "Breadcrumbs", "In Sitemap"]]
    for result in data:
        sheet_data.append([
            result['link'],
            result['title'],
            result['title_length'],
            result['meta_description'],
            result['meta_description_length'],
            result['h1_title'],
            result['canonical_url'],
            result['breadcrumbs'],
            'Yes' if result['in_sitemap'] else 'No'
        ])

    # Write the SEO Analysis to the 'SEO Analysis' sheet
    body = {'values': sheet_data}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='SEO Analysis!A1',
        valueInputOption='RAW',
        body=body
    ).execute()

    # Step 5: Prepare Broken Links sheet content
    broken_links_data = [["Broken Link", "Parent URL", "Status"]]
    for link, parent_url, status in broken_links:
        broken_links_data.append([link, parent_url, status])

    # Write broken links data to 'Broken Links' sheet
    body = {'values': broken_links_data}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='Broken Links!A1',
        valueInputOption='RAW',
        body=body
    ).execute()

    # Step 6: Format both sheets (SEO Analysis and Broken Links)
    requests = create_column_width_requests(column_config)

    # Text wrapping and formatting for 'SEO Analysis' sheet
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": meta_data_sheet_id,  # First sheet (SEO Analysis)
                "startRowIndex": 0,
                "endRowIndex": len(sheet_data),
                "startColumnIndex": 0,
                "endColumnIndex": len(column_config)
            },
            "cell": {
                "userEnteredFormat": {
                    "wrapStrategy": "WRAP"
                }
            },
            "fields": "userEnteredFormat.wrapStrategy"
        }
    })

    # Text wrapping and formatting for 'Broken Links' sheet
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": broken_links_sheet_id,  # Second sheet (Broken Links)
                "startRowIndex": 0,
                "endRowIndex": len(broken_links_data),
                "startColumnIndex": 0,
                "endColumnIndex": 3
            },
            "cell": {
                "userEnteredFormat": {
                    "wrapStrategy": "WRAP"
                }
            },
            "fields": "userEnteredFormat.wrapStrategy"
        }
    })

    # Header formatting (center alignment, bold, background color) for both sheets
    for sheet_id in [meta_data_sheet_id, broken_links_sheet_id]:
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,  # Header row
                    "startColumnIndex": 0,
                    "endColumnIndex": 9 if sheet_id == meta_data_sheet_id else 3  # Adjust for each sheet
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "backgroundColor": {
                            "red": 0.9,
                            "green": 0.9,
                            "blue": 0.9
                        },
                        "textFormat": {
                            "bold": True
                        }
                    }
                },
                "fields": "userEnteredFormat(textFormat,horizontalAlignment,backgroundColor)"
            }
        })

    # Freeze the first column and row for both sheets
    for sheet_id in [meta_data_sheet_id]:
        requests.append({
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {
                        "frozenColumnCount": 1,
                        "frozenRowCount": 1
                    }
                },
                "fields": "gridProperties.frozenColumnCount,gridProperties.frozenRowCount"
            }
        })

    # Apply the changes (batch update) to both sheets
    body = {'requests': requests}
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

    # Share the spreadsheet with the specified email
    share_spreadsheet_with_email(service, creds, spreadsheet_id, email_to_share_with)


# Function to share the spreadsheet with a specific email
def share_spreadsheet_with_email(service, creds, spreadsheet_id, email):
    drive_service = build('drive', 'v3', credentials=creds)

    # Define the permission
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': email
    }

    # Share the file with the specified email
    drive_service.permissions().create(
        fileId=spreadsheet_id,
        body=permission,
        fields='id'
    ).execute()

if __name__ == "__main__":
    print("Enter the URL of the page to scan.")
    print("Note: You can start the URL with 'www' (e.g., www.example.com).")
    print("If no URL is provided, http://127.0.0.1:5000 will be used as the default.")
    
    url = input("Enter the URL (Press Enter to use http://127.0.0.1:5000): ").strip()

    if not url:
        url = 'http://127.0.0.1:5000'
    elif url.startswith("www."):
        url = f"https://{url}"
    elif not (url.startswith("http://") or url.startswith("https://")):
        print("Invalid format. Adding 'https://' automatically.")
        url = f"https://{url}"

    print(f"Scanning the URL: {url}")

    email_to_share_with = input(f"Enter email to share the spreadsheet with (default: {DEFAULT_EMAIL}): ").strip()
    if not email_to_share_with:
        email_to_share_with = DEFAULT_EMAIL
    
    link_results, broken_links = scan_and_check_links(url)

    # If results were found, create a Google Spreadsheet and share it
    if isinstance(link_results, list):
        print("\nMeta Title and Description for Main URL and Each Link:")

        create_google_spreadsheet(link_results, broken_links, email_to_share_with)
    else:
        print(link_results)


