import argparse
import sys
import requests
from bs4 import BeautifulSoup # Although not strictly used for validation in this version, it's good practice if parsing is needed later.
from tqdm import tqdm # Import tqdm

# Define a user-agent to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
# Define a timeout for requests
REQUEST_TIMEOUT = 2 # seconds

def check_website_accessibility(domain):
    """
    Checks if a domain is accessible by attempting HTTP/HTTPS GET requests.
    Returns True if a 2xx status code is received, False otherwise.
    Uses tqdm.write for output compatible with the progress bar.
    """
    urls_to_try = [f"https://{domain}", f"http://{domain}"]
    for url in urls_to_try:
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            # Check for successful status codes (200-299)
            if response.status_code >= 200 and response.status_code < 300:
                # Use tqdm.write for output during loop
                tqdm.write(f"  Success: {url} (Status: {response.status_code})")
                # Optional: Basic check if content looks like HTML
                # soup = BeautifulSoup(response.text, 'html.parser')
                # if soup.find('html'):
                #    return True
                return True
            else:
                # Use tqdm.write for output during loop
                tqdm.write(f"  Failed: {url} (Status: {response.status_code})")
        except requests.exceptions.Timeout:
            # Use tqdm.write for output during loop
            tqdm.write(f"  Failed: {url} (Timeout after {REQUEST_TIMEOUT}s)")
        except requests.exceptions.RequestException as e:
            # Catches connection errors, SSL errors, too many redirects, etc.
            # Use tqdm.write for output during loop
            tqdm.write(f"  Failed: {url} (Error: {type(e).__name__})") # Keep error concise
        except Exception as e:
            # Catch potential unexpected errors during request/processing
            # Use tqdm.write for output during loop
            tqdm.write(f"  Failed: {url} (Unexpected Error: {type(e).__name__})")

    return False # Tried all URLs, none worked

def process_domains(input_filepath, output_filepath="cleaned.txt"):
    """
    Reads domains from input_filepath, checks their accessibility via HTTP/S,
    and writes the accessible ones to output_filepath. Includes a progress bar.
    """
    valid_domains = set()
    total_lines = 0
    invalid_lines = [] # Keep track of lines that failed validation

    # First count total lines for progress indication
    try:
        with open(input_filepath, 'r', encoding='utf-8') as infile:
            total_lines = sum(1 for line in infile if line.strip())
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_filepath}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while reading '{input_filepath}': {e}", file=sys.stderr)
        sys.exit(1)

    if total_lines == 0:
        print(f"Input file '{input_filepath}' is empty or contains no processable lines.")
        return

    print(f"Reading domains from: {input_filepath} ({total_lines} lines found)")

    try:
        # Wrap the infile enumeration with tqdm for a progress bar
        with open(input_filepath, 'r', encoding='utf-8') as infile:
            # Use tqdm directly on the enumerated infile
            for i, line in enumerate(tqdm(infile, total=total_lines, unit="domain", desc="Processing domains")):
                domain = line.strip().lower()
                if not domain: # Skip empty lines
                    continue

                # Use tqdm.write for intermittent messages
                tqdm.write(f"Checking: {domain}")

                # Use the new accessibility check
                if check_website_accessibility(domain):
                    valid_domains.add(domain)
                else:
                    # Store original line content for reporting invalid ones
                    invalid_lines.append((i + 1, line.strip()))
                    # Use tqdm.write for output during loop
                    tqdm.write(f"  Result: {domain} is NOT accessible or valid.")

    except FileNotFoundError:
        # This case is already handled above, but keep for safety
        print(f"Error: Input file not found at '{input_filepath}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while processing '{input_filepath}': {e}", file=sys.stderr)
        sys.exit(1)

    # Add a newline after tqdm finishes
    print()

    if not valid_domains:
        print("\nNo accessible domains found.")
        if invalid_lines:
             print("\nDomains/Lines that failed the accessibility check:")
             for line_num, content in invalid_lines:
                 print(f"  Line {line_num}: '{content}'")
        return

    try:
        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            print(f"\nWriting {len(valid_domains)} accessible domains to: {output_filepath}")
            # Sort domains alphabetically before writing
            for domain in sorted(list(valid_domains)):
                outfile.write(domain + '\n')
        print("Processing complete.")

        if invalid_lines:
            print("\nDomains/Lines that failed the accessibility check:")
            for line_num, content in invalid_lines:
                print(f"  Line {line_num}: '{content}'")

    except Exception as e:
        print(f"An error occurred while writing to '{output_filepath}': {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check website accessibility from a file and save accessible domains.")
    # Changed input_file to be optional with a default
    parser.add_argument("-i", "--input", default="whitelist.txt",
                        help="Path to the input text file containing domains (one per line, default: whitelist.txt).")
    parser.add_argument("-o", "--output", default="cleaned.txt",
                        help="Path to the output text file for accessible domains (default: cleaned.txt).")

    args = parser.parse_args()

    # Pass the input filename from args
    process_domains(args.input, args.output)
