# import requests
# from bs4 import BeautifulSoup
# import re # Import regular expressions for parsing text
# import json # To pretty-print the output dictionary

# def get_amazon_ratings(product_url):
#     """
#     Fetches and extracts rating information from an Amazon product page.

#     Args:
#         product_url (str): The URL of the Amazon product page.

#     Returns:
#         dict: A dictionary containing rating information (overall rating,
#               total ratings count, percentage breakdown per star),
#               or None if scraping fails.
#     """
#     headers = {
#         # Mimic a browser request to reduce chances of being blocked
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
#         'Accept-Language': 'en-US,en;q=0.9',
#         'Accept-Encoding': 'gzip, deflate, br',
#         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
#         'Connection': 'keep-alive',
#         'DNT': '1', # Do Not Track Request Header
#         'Upgrade-Insecure-Requests': '1'
#     }

#     ratings_data = {
#         'overall_rating': None,
#         'total_ratings_count': None,
#         'star_percentages': {} # To store { '5': 52, '4': 25, ... }
#     }

#     try:
#         print(f"Attempting to fetch: {product_url}")
#         response = requests.get(product_url, headers=headers, timeout=15)
#         response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
#         print("Successfully fetched page.")

#         soup = BeautifulSoup(response.content, 'html.parser')

#         # --- 1. Extract Overall Rating ---
#         # Often found in a span within an element with data-hook="average-star-rating"
#         rating_element = soup.find('i', {'data-hook': 'average-star-rating'})
#         if rating_element:
#             rating_span = rating_element.find('span', class_='a-icon-alt')
#             if rating_span:
#                 # Extract text like "4.0 out of 5 stars" and parse it
#                 match = re.search(r'([\d.]+)\s+out\s+of\s+5', rating_span.text.strip())
#                 if match:
#                     ratings_data['overall_rating'] = float(match.group(1))
#                     print(f"Found overall rating: {ratings_data['overall_rating']}")
#         else:
#              # Fallback: sometimes it's in a span with data-hook directly
#              rating_span_alt = soup.find('span', {'data-hook': 'rating-out-of-text'})
#              if rating_span_alt:
#                  match = re.search(r'([\d.]+)\s+out\s+of\s+5', rating_span_alt.text.strip())
#                  if match:
#                     ratings_data['overall_rating'] = float(match.group(1))
#                     print(f"Found overall rating (alt): {ratings_data['overall_rating']}")


#         # --- 2. Extract Total Ratings Count ---
#         # Often found in a span with data-hook="total-review-count"
#         count_element = soup.find('span', {'data-hook': 'total-review-count'})
#         if count_element:
#             # Extract text like "1,213 global ratings" and parse it
#             count_text = count_element.text.strip().split()[0] # Get the first part (number)
#             count_text = count_text.replace(',', '') # Remove commas
#             if count_text.isdigit():
#                 ratings_data['total_ratings_count'] = int(count_text)
#                 print(f"Found total ratings count: {ratings_data['total_ratings_count']}")

#         # --- 3. Extract Star Rating Percentages ---
#         # Look for the histogram table rows (often <tr> or <a> tags within a specific container)
#         # Using 'a' tags with 'a-link-normal' inside the histogram table is common
#         histogram_table = soup.find('table', {'id': 'histogramTable'})
#         if histogram_table:
#             percentage_rows = histogram_table.find_all('tr', {'class': 'a-histogram-row'}) # More specific if possible
#             print(f"Found {len(percentage_rows)} potential percentage rows in histogram table.")

#             for row in percentage_rows:
#                 # Find the link which usually contains the star level and percentage info
#                 link = row.find('a', class_='a-link-normal')
#                 if link and link.has_attr('title'):
#                      # Title often looks like "XX% of reviews have Y stars"
#                      title_text = link['title'].strip()
#                      # Extract star level (e.g., '5')
#                      star_match = re.search(r'have\s+(\d+)\s+stars?', title_text, re.IGNORECASE)
#                      # Extract percentage (e.g., '52')
#                      percent_match = re.search(r'^(\d+)%', title_text)

#                      if star_match and percent_match:
#                          star_level = star_match.group(1)
#                          percentage = int(percent_match.group(1))
#                          ratings_data['star_percentages'][f'{star_level}_star'] = percentage
#                          print(f"Found percentage: {star_level} star = {percentage}%")
#         else:
#             print("Could not find histogram table (id='histogramTable'). Trying alternative selectors...")
#             # Fallback: Sometimes percentages are in divs or spans directly, look for patterns
#             # This requires more inspection of the specific product page if the table isn't found
#             # Example (highly dependent on current structure):
#             # review_section = soup.find('div', {'id': 'reviewsMedley'})
#             # if review_section:
#             #    percentage_elements = review_section.select('div.a-meter + span.a-size-base') # Example selector, likely needs adjustment
#             #    # Further logic to map these percentages back to star levels would be needed


#         # Check if we found *any* data
#         if ratings_data['overall_rating'] is None and ratings_data['total_ratings_count'] is None and not ratings_data['star_percentages']:
#             print("Warning: Failed to extract any rating data. The page structure might have changed or the product has no ratings.")
#             return None # Indicate failure

#         return ratings_data

#     except requests.exceptions.RequestException as e:
#         print(f"Error during requests to {product_url}: {e}")
#         return None
#     except AttributeError as e:
#         print(f"Error parsing HTML (likely element not found): {e}")
#         return None
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         return None

# # --- Example Usage ---
# if __name__ == "__main__":
#     # product_url = input("Enter the Amazon product URL: ")
#     # Example URLs (replace with actual, current ones for testing):
#     product_url = "https://www.amazon.in/Whirlpool-Refrigerator-205-WDE-CLS/dp/B0BSRW3N14/ref=sr_1_2_sspa?_encoding=UTF8&rps=1&s=kitchen&sr=1-2-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGZfYnJvd3Nl"
#     # product_url = "https://www.amazon.com/dp/B08N5WRWNW" # Example: Fire TV Stick
#     # product_url = "YOUR_PRODUCT_URL_HERE" # Paste URL here

#     if not product_url.startswith(("http://", "https://")):
#         print("Invalid URL format. Please include http:// or https://")
#     else:
#         scraped_data = get_amazon_ratings(product_url)

#         if scraped_data:
#             print("\n--- Scraped Rating Information ---")
#             print(json.dumps(scraped_data, indent=4))
#             print("--------------------------------")
#         else:
#             print("\nCould not retrieve rating information for the given URL.")







import requests
from bs4 import BeautifulSoup
import re # Import regular expressions for parsing text
import json # To pretty-print the output dictionary

def get_amazon_ratings(product_url):
    """
    Fetches and extracts rating information from an Amazon product page.
    Updated to handle variations in histogram structure.

    Args:
        product_url (str): The URL of the Amazon product page.

    Returns:
        dict: A dictionary containing rating information (overall rating,
              total ratings count, percentage breakdown per star),
              or None if scraping fails.
    """
    headers = {
        # Mimic a browser request to reduce chances of being blocked
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Connection': 'keep-alive',
        'DNT': '1', # Do Not Track Request Header
        'Upgrade-Insecure-Requests': '1'
    }

    ratings_data = {
        'overall_rating': None,
        'total_ratings_count': None,
        'star_percentages': {} # To store { '5_star': 52, '4_star': 25, ... }
    }

    try:
        print(f"Attempting to fetch: {product_url}")
        response = requests.get(product_url, headers=headers, timeout=20) # Increased timeout slightly
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        print("Successfully fetched page.")

        soup = BeautifulSoup(response.content, 'html.parser')

        # --- 1. Extract Overall Rating ---
        # Try finding the icon first
        rating_element = soup.find('i', {'data-hook': 'average-star-rating'})
        rating_text = None
        if rating_element:
             rating_span = rating_element.find('span', class_='a-icon-alt')
             if rating_span:
                 rating_text = rating_span.text.strip()

        # Fallback: Try finding the text container directly
        if not rating_text:
            rating_span_alt = soup.find('span', {'data-hook': 'rating-out-of-text'})
            if rating_span_alt:
                rating_text = rating_span_alt.text.strip()

        if rating_text:
            match = re.search(r'([\d.]+)\s+out\s+of\s+5', rating_text)
            if match:
                ratings_data['overall_rating'] = float(match.group(1))
                print(f"Found overall rating: {ratings_data['overall_rating']}")
        else:
            print("Could not find overall rating element.")


        # --- 2. Extract Total Ratings Count ---
        count_element = soup.find('span', {'data-hook': 'total-review-count'})
        if count_element:
            # Extract text like "1,213 global ratings" and parse it
            count_text_match = re.search(r'([\d,]+)\s+global\s+ratings?', count_element.text.strip(), re.IGNORECASE)
            if count_text_match:
                count_text = count_text_match.group(1).replace(',', '') # Remove commas
                if count_text.isdigit():
                    ratings_data['total_ratings_count'] = int(count_text)
                    print(f"Found total ratings count: {ratings_data['total_ratings_count']}")
            else:
                # Fallback if "global ratings" isn't present, just grab digits
                count_text_match = re.search(r'([\d,]+)', count_element.text.strip())
                if count_text_match:
                    count_text = count_text_match.group(1).replace(',', '') # Remove commas
                    if count_text.isdigit():
                        ratings_data['total_ratings_count'] = int(count_text)
                        print(f"Found total ratings count (fallback parse): {ratings_data['total_ratings_count']}")

        else:
             print("Could not find total ratings count element.")


        # --- 3. Extract Star Rating Percentages (NEW APPROACH) ---
        print("Attempting to extract star percentages using aria-label or specific classes...")

        # Try finding links with informative aria-labels first (often the most reliable)
        # Regex: Finds "XX percent of reviews have Y stars"
        percentage_links = soup.find_all('a', {'aria-label': re.compile(r'\d+\s*percent of reviews have \d+ stars?', re.IGNORECASE)})

        if percentage_links:
            print(f"Found {len(percentage_links)} links with aria-label for percentages.")
            for link in percentage_links:
                aria_label_text = link.get('aria-label', '').strip()
                # Extract star level (e.g., '5')
                star_match = re.search(r'have\s+(\d+)\s+stars?', aria_label_text, re.IGNORECASE)
                # Extract percentage (e.g., '52')
                percent_match = re.search(r'^(\d+)\s*percent', aria_label_text, re.IGNORECASE)

                if star_match and percent_match:
                    star_level = star_match.group(1)
                    percentage = int(percent_match.group(1))
                    key = f'{star_level}_star'
                    ratings_data['star_percentages'][key] = percentage
                    print(f"Found percentage via aria-label: {key} = {percentage}%")
                else:
                    print(f"Could not parse aria-label: {aria_label_text}")

        else:
            # Fallback: If aria-label method fails, try finding the percentage rows/bars differently
            # This often involves finding a container and then rows within it.
            # Common container IDs: 'reviewsMedley', 'cm_cr-review_list', 'cr-widget-desktop-review-histogram'
            # Common row classes: 'a-histogram-row', sometimes custom classes like the one in your original HTML
            print("Did not find percentage links via aria-label. Trying fallback selectors...")
            histogram_rows = soup.select('tr.a-histogram-row') # Common structure
            if not histogram_rows:
                # Try the structure from your initial HTML snippet (more specific, might break easily)
                histogram_rows = soup.select('ul[class*="_histogram"] > li span.a-list-item > a[class*="_histogram-row-container"]') # More complex selector


            if histogram_rows:
                 print(f"Found {len(histogram_rows)} potential percentage rows using fallback selectors.")
                 for row in histogram_rows:
                     star_text_element = row.find('span', class_='a-size-base') # Find the 'X star' text
                     percentage_text_element = row.find('span', class_='a-text-right') # Find the 'XX%' text

                     if star_text_element and percentage_text_element:
                         star_text = star_text_element.text.strip()
                         percentage_text = percentage_text_element.text.strip()

                         star_match = re.search(r'(\d+)\s+star', star_text, re.IGNORECASE)
                         percent_match = re.search(r'(\d+)%', percentage_text)

                         if star_match and percent_match:
                             star_level = star_match.group(1)
                             percentage = int(percent_match.group(1))
                             key = f'{star_level}_star'
                             ratings_data['star_percentages'][key] = percentage
                             print(f"Found percentage via fallback: {key} = {percentage}%")
                         else:
                            print(f"Could not parse fallback row: star='{star_text}', percent='{percentage_text}'")
            else:
                 print("Could not find percentage rows using fallback selectors either.")


        # Check if we found *any* data
        if ratings_data['overall_rating'] is None and ratings_data['total_ratings_count'] is None and not ratings_data['star_percentages']:
            print("\nWarning: Failed to extract any rating data. The page structure might have changed, the product might have no ratings, or scraping could be blocked.")
            # You might want to print some soup content here for debugging if this happens often
            # print(soup.prettify()[:2000]) # Print first 2000 chars of HTML
            return None # Indicate failure
        elif not ratings_data['star_percentages']:
             print("\nWarning: Successfully extracted overall rating and count, but failed to get star percentages. Histogram structure might be unrecognized.")


        return ratings_data

    except requests.exceptions.Timeout:
        print(f"Error: Request timed out for {product_url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error during requests to {product_url}: {e}")
        return None
    except AttributeError as e:
        print(f"Error parsing HTML (likely an element was not found or NoneType): {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # import traceback
        # traceback.print_exc() # Uncomment for detailed traceback
        return None

# --- Example Usage ---
if __name__ == "__main__":
    # Get URL from user or use a default
    # product_url = input("Enter the Amazon product URL: ").strip()
    # Example URLs (replace with actual, current ones for testing):
    # product_url = "https://www.amazon.com/dp/B07VGRJDFY" # Example: Echo Dot 3rd Gen
    # product_url = "https://www.amazon.com/dp/B08N5WRWNW" # Example: Fire TV Stick 4K
    product_url = input("enter url: ") # The ASIN from your original HTML snippet (assuming .com)

    if not product_url:
        print("No URL entered.")
    elif not product_url.startswith(("http://", "https://")):
        print("Invalid URL format. Please include http:// or https://")
    else:
        scraped_data = get_amazon_ratings(product_url)

        if scraped_data:
            print("\n--- Scraped Rating Information ---")
            # Sort percentages if needed
            if scraped_data.get('star_percentages'):
                 sorted_percentages = dict(sorted(scraped_data['star_percentages'].items(), key=lambda item: int(item[0].split('_')[0]), reverse=True))
                 scraped_data['star_percentages'] = sorted_percentages
            print(json.dumps(scraped_data, indent=4))
            print("--------------------------------")
        else:
            print("\nCould not retrieve complete rating information for the given URL.")