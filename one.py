# import requests
# from bs4 import BeautifulSoup
# import streamlit as st
# import matplotlib.pyplot as plt
# from dotenv import load_dotenv
# import os
# import google.generativeai as genai
# from gtts import gTTS
# import tempfile
# import re # Needed for rating extraction
# import json # Good for debugging extracted data

# load_dotenv()
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     st.error("🔴 GEMINI_API_KEY not found. Please set it in your .env file.")
#     st.stop() # Stop execution if key is missing

# try:
#     genai.configure(api_key=GEMINI_API_KEY)
#     model = genai.GenerativeModel(
#          model_name='models/gemini-1.5-flash', # Or use 'gemini-pro'
#         generation_config={
#             "temperature": 0.4,
#             "max_output_tokens": 800,
#             "top_p": 0.9,
#             "top_k": 40
#         },
#         safety_settings=[
#             {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
#             {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
#             {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
#             {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
#         ],
#         system_instruction="You are a helpful assistant that analyzes Amazon product data and answers user questions based on the provided information."
#     )
# except Exception as e:
#     st.error(f"🔴 Error configuring Gemini: {e}")
#     st.stop()

# HEADERS = {
#     'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
#                    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'), # Updated User Agent slightly
#     'Accept-Language': 'en-US,en;q=0.9', # More common Accept-Language
#     'Accept-Encoding': 'gzip, deflate, br',
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
#     'Connection': 'keep-alive',
#     'DNT': '1', # Do Not Track Request Header
#     'Upgrade-Insecure-Requests': '1'
# }

# def getdata(url):
#     """Fetches HTML content from a URL."""
#     try:
#         r = requests.get(url, headers=HEADERS, timeout=20) # Added timeout
#         r.raise_for_status() # Check for HTTP errors
#         return r.text
#     except requests.exceptions.Timeout:
#         st.warning(f"Request timed out for {url}")
#         return None
#     except requests.exceptions.RequestException as e:
#         st.warning(f"Error fetching {url}: {e}")
#         return None

# def html_code(url):
#     """Parses HTML content using BeautifulSoup."""
#     htmldata = getdata(url)
#     if htmldata:
#         try:
#             soup = BeautifulSoup(htmldata, 'html.parser')
#             return soup
#         except Exception as e:
#             st.warning(f"Error parsing HTML: {e}")
#             return None
#     return None

# def extract_product_details(soup):
#     """Extracts the main product title."""
#     if not soup: return "Product name not found"
#     try:
#         title_element = soup.find('span', id='productTitle')
#         product_name = title_element.get_text(strip=True) if title_element else "Product name not found"
#         return product_name
#     except Exception:
#         return "Product name not found"

# def extract_product_specifications(soup):
#     """Extracts product specifications, trying multiple table structures."""
#     if not soup: return {}
#     specs = {}
#     try:
#         # Look for different possible table IDs or classes
#         spec_table = soup.find("table", id="productDetails_techSpec_section_1")
#         if not spec_table:
#             spec_table = soup.find("table", id="productDetails_detailBullets_sections1")
#         if not spec_table:
#              spec_table = soup.find('table', class_='prodDetTable')
#         # Add more potential table IDs or classes if needed

#         if spec_table:
#             rows = spec_table.find_all("tr")
#             for row in rows:
#                 header_cell = row.find("th")
#                 value_cell = row.find("td")
#                 if header_cell and value_cell:
#                     key = header_cell.get_text(strip=True)
#                     value = value_cell.get_text(strip=True).replace('\n', ' ').replace('\u200e', '').replace('\u200f', '') # Clean value
#                     # Check if we already found colour/price elsewhere, prioritise those
#                     if key.lower() not in ['color', 'colour', 'price']:
#                         specs[key] = value
#             # Return specs potentially populated from table
#             # We explicitly exclude colour/price here as extract_other_product_info handles them better

#         # Fallback: Look for detail bullet points if table fails or doesn't contain desired info
#         detail_bullets = soup.find('div', id='detailBullets_feature_div')
#         if detail_bullets:
#             list_items = detail_bullets.find_all('li')
#             for item in list_items:
#                  key_span = item.find('span', class_='a-text-bold')
#                  if key_span:
#                      key = key_span.get_text(strip=True).replace(':','').strip()
#                      # Find the value part (the rest of the span content after the bold part)
#                      value_part = key_span.next_sibling
#                      value = ""
#                      if value_part and isinstance(value_part, str):
#                          value = value_part.strip()
#                      elif item.find('span', class_='a-list-item'): # If value is in another span
#                           value_span = item.find('span', class_='a-list-item')
#                           # Remove the key span's text from the full list item text
#                           full_text = value_span.get_text(strip=True)
#                           key_text_in_val = key_span.get_text(strip=True)
#                           value = full_text.replace(key_text_in_val, '').strip()

#                      if key and value and key.lower() not in ['color', 'colour', 'price']:
#                          specs[key] = value

#         return specs # Return potentially populated specs or empty dict

#     except Exception as e:
#         st.warning(f"Error extracting specifications: {e}")
#         return {}

# # --- Function to extract Price, Colour, and Review Snippet ---
# def extract_other_product_info(soup):
#     """Extracts price, colour, and a sample review snippet."""
#     if not soup:
#         return {"price": "N/A", "colour": "N/A", "review_snippet": "N/A"}

#     info = {
#         "price": "Price not found",
#         "colour": "Colour not found",
#         "review_snippet": "Review snippet not found"
#     }

#     try:
#         # --- Price Extraction ---
#         price_element = soup.select_one('span.a-price span[aria-hidden="true"]') # Common selector
#         if not price_element:
#             price_element = soup.select_one('span.a-offscreen') # Hidden span often has full price
#         if not price_element:
#             price_element = soup.find("span", class_="priceToPay") # Another possible class
#         if not price_element:
#              # Look for older IDs as fallback
#              price_element = soup.find("span", id="priceblock_ourprice")
#              if not price_element:
#                  price_element = soup.find("span", id="priceblock_dealprice")

#         if price_element:
#             info["price"] = price_element.get_text(strip=True)
#         else:
#             # Last resort: Check within potential deal price badges
#             deal_badge_price = soup.select_one('span[data-a-strike="true"] span[aria-hidden="true"]') # Strikethrough price
#             if deal_badge_price: # If strikethrough exists, the actual price might be nearby
#                 actual_price_nearby = deal_badge_price.find_next('span', class_='a-offscreen')
#                 if actual_price_nearby:
#                     info["price"] = actual_price_nearby.get_text(strip=True)


#         # --- Colour Extraction ---
#         # 1. Try selected variation swatch
#         colour_swatch = soup.select_one('div#variation_color_name span.selection')
#         if colour_swatch:
#             info["colour"] = colour_swatch.get_text(strip=True)
#         else:
#             # 2. Try detail bullets list
#             details_container = soup.find('div', id='detailBullets_feature_div') or soup.find('div', id='productDetails_feature_div')
#             if details_container:
#                 list_items = details_container.find_all('li')
#                 for item in list_items:
#                      text = item.get_text(strip=True)
#                      # Look for "Color:" or "Colour:" at the start of the line
#                      match = re.match(r"(?:Color|Colour)\s*:\s*(.*)", text, re.IGNORECASE)
#                      if match:
#                           info["colour"] = match.group(1).strip()
#                           break # Found it

#             # 3. Fallback: Look within general feature bullets (less reliable)
#             if info["colour"] == "Colour not found":
#                  feature_bullets = soup.find('div', id='feature-bullets')
#                  if feature_bullets:
#                       list_items = feature_bullets.find_all('li')
#                       for item in list_items:
#                            text = item.get_text(strip=True)
#                            if "color" in text.lower() or "colour" in text.lower():
#                                 # This is less precise, might grab unrelated text
#                                 # Try to find a plausible value nearby
#                                 parts = text.split(':')
#                                 if len(parts) > 1 and ('color' in parts[0].lower() or 'colour' in parts[0].lower()):
#                                      info["colour"] = parts[1].strip()
#                                      break

#         # --- Sample Review Snippet Extraction ---
#         review_body_element = soup.find('span', {'data-hook': 'review-body'})
#         if review_body_element:
#             # Get text and limit length for a snippet
#             full_review_text = review_body_element.get_text(strip=True)
#             info["review_snippet"] = (full_review_text[:550] + '...') if len(full_review_text) > 550 else full_review_text
#         else:
#              # Fallback: Try getting a prominent review title if body isn't found
#              review_title_link = soup.find('a', {'data-hook': 'review-title'})
#              if review_title_link:
#                   review_title_span = review_title_link.find('span', recursive=False) # Immediate child span
#                   if review_title_span:
#                       info["review_snippet"] = "Title: " + review_title_span.get_text(strip=True)

#         return info

#     except Exception as e:
#         st.warning(f"Error extracting price/colour/snippet: {e}")
#         # Return dictionary with error indicators if something went wrong
#         return {
#             "price": info.get("price", "Error extracting price"),
#             "colour": info.get("colour", "Error extracting colour"),
#             "review_snippet": info.get("review_snippet", "Error extracting snippet")
#         }

# def get_amazon_ratings_from_soup(soup):
#     """Extracts detailed rating information (overall, count, percentages)."""
#     if not soup:
#         return None

#     ratings_data = {
#         'overall_rating': None,
#         'total_ratings_count': None,
#         'star_percentages': {} # To store { 5: 52, 4: 25, ... } (Using numbers as keys)
#     }

#     try:
#         # --- Overall Rating ---
#         rating_text = None
#         # Try common hooks first
#         rating_icon_span = soup.find('i', {'data-hook': 'average-star-rating'})
#         if rating_icon_span:
#             rating_text_span = rating_icon_span.find('span', class_='a-icon-alt')
#             if rating_text_span:
#                 rating_text = rating_text_span.text.strip()
#         if not rating_text:
#             rating_span_alt = soup.find('span', {'data-hook': 'rating-out-of-text'})
#             if rating_span_alt:
#                 rating_text = rating_span_alt.text.strip()
#         # Try other common patterns
#         if not rating_text:
#              rating_element = soup.select_one('span[data-asin-review-star-rating] span.a-icon-alt') # Used on some pages
#              if rating_element:
#                   rating_text = rating_element.get_text(strip=True)
#         if not rating_text:
#              rating_element = soup.select_one('span.reviewNumericalSummary span.a-declarative a span.a-size-medium.a-color-base') # another possible structure
#              if rating_element:
#                  rating_text = rating_element.get_text(strip=True) + " out of 5" # Add context if just number found

#         if rating_text:
#             # Use regex to find digits and a decimal point before "out of 5"
#             match = re.search(r'([\d.]+)\s+out\s+of\s+5', rating_text, re.IGNORECASE)
#             if match:
#                 ratings_data['overall_rating'] = float(match.group(1))
#                 # print(f"DEBUG: Found overall rating: {ratings_data['overall_rating']}") # Keep for debugging if needed
#             else:
#                  # Handle case where only the number might be present (e.g., "4.5")
#                  match_num_only = re.search(r'^([\d.]+)$', rating_text.strip())
#                  if match_num_only:
#                       ratings_data['overall_rating'] = float(match_num_only.group(1))
#                       # print(f"DEBUG: Found overall rating (numeric only): {ratings_data['overall_rating']}")

#         else:
#             pass # print("DEBUG: Could not find overall rating element.") # Keep for debugging

#         # --- Total Ratings Count ---
#         count_element = soup.find('span', {'data-hook': 'total-review-count'})
#         if not count_element:
#             count_element = soup.find('span', id='acrCustomerReviewText') # Older ID

#         if count_element:
#             count_text_content = count_element.get_text(strip=True)
#             # Use regex to find numbers, potentially with commas
#             count_text_match = re.search(r'([\d,]+)', count_text_content)
#             if count_text_match:
#                 count_text = count_text_match.group(1).replace(',', '')
#                 if count_text.isdigit():
#                     ratings_data['total_ratings_count'] = int(count_text)
#                     # print(f"DEBUG: Found total ratings count: {ratings_data['total_ratings_count']}")
#         else:
#              pass # print("DEBUG: Could not find total ratings count element.") # Keep for debugging

#         # --- Star Percentages ---
#         # print("DEBUG: Attempting to extract star percentages...") # Keep for debugging
#         # 1. Try using aria-label on links (often reliable)
#         percentage_links = soup.find_all('a', {'aria-label': re.compile(r'\d+\s*percent of reviews have \d+ stars?', re.IGNORECASE)})
#         if percentage_links:
#             # print(f"DEBUG: Found {len(percentage_links)} links with aria-label for percentages.") # Debugging
#             for link in percentage_links:
#                 aria_label_text = link.get('aria-label', '').strip()
#                 star_match = re.search(r'have\s+(\d+)\s+stars?', aria_label_text, re.IGNORECASE)
#                 percent_match = re.search(r'^(\d+)\s*percent', aria_label_text, re.IGNORECASE)
#                 if star_match and percent_match:
#                     star_level = int(star_match.group(1))
#                     percentage = int(percent_match.group(1))
#                     ratings_data['star_percentages'][star_level] = percentage
#                     # print(f"DEBUG: Found percentage via aria-label: {star_level} star = {percentage}%") # Debugging

#         # 2. Fallback: Try common table row selectors if aria-label fails
#         if not ratings_data['star_percentages']:
#             # print("DEBUG: Did not find percentage links via aria-label. Trying fallback selectors...") # Debugging
#             histogram_rows = soup.select('table#histogramTable tr.a-histogram-row') # Common table ID
#             if not histogram_rows:
#                  # Try another common structure using ul/li
#                  histogram_rows = soup.select('tr[data-reviews-state*="histogram-row"]') # Newer attribute pattern?
#             if not histogram_rows:
#                  histogram_rows = soup.select('td.a-text-right > span.a-size-base > a[title*="%"]') # Look for percentage in title


#             if histogram_rows:
#                  # print(f"DEBUG: Found {len(histogram_rows)} potential percentage rows using fallback selectors.") # Debugging
#                  for row in histogram_rows:
#                      # Try finding star level text (e.g., "5 star")
#                      star_text_element = row.find(['span', 'a'], string=re.compile(r'\d+\s+star'), class_=re.compile(r'a-size-base|a-link-normal'))

#                      # Try finding percentage text (e.g., "52%") - often in a right-aligned element or a link title
#                      percentage_text_element = row.find(['span', 'a'], class_=re.compile(r'a-text-right|a-link-normal'), title=re.compile(r'\d+%'))
#                      if not percentage_text_element: # Check text content too
#                          percentage_text_element = row.find(['span', 'a'], string=re.compile(r'\d+%'))


#                      if star_text_element and percentage_text_element:
#                          star_text = star_text_element.get_text(strip=True)
#                          percentage_text = percentage_text_element.get_text(strip=True)
#                          percentage_title = percentage_text_element.get('title', '') # Get title attribute

#                          star_match = re.search(r'(\d+)\s+star', star_text, re.IGNORECASE)

#                          # Extract percentage preferentially from title, then from text
#                          percent_match = re.search(r'(\d+)%', percentage_title)
#                          if not percent_match:
#                               percent_match = re.search(r'(\d+)%', percentage_text)

#                          if star_match and percent_match:
#                              star_level = int(star_match.group(1))
#                              percentage = int(percent_match.group(1))
#                              ratings_data['star_percentages'][star_level] = percentage
#                              # print(f"DEBUG: Found percentage via fallback: {star_level} star = {percentage}%") # Debugging
#                          #else: # Debugging
#                              #print(f"DEBUG: Could not parse fallback row content. Star: '{star_text}', Percent: '{percentage_text}', Title: '{percentage_title}'")
#                      #else: # Debugging
#                          #print(f"DEBUG: Could not find both star and percentage elements in fallback row.")
#             #else: # Debugging
#                  # print("DEBUG: Could not find percentage rows using fallback selectors either.")

#         # --- Final Checks ---
#         if ratings_data['overall_rating'] is None and ratings_data['total_ratings_count'] is None and not ratings_data['star_percentages']:
#             # print("DEBUG: Failed to extract any rating data.") # Debugging
#             st.warning("Could not extract detailed rating information.")
#             return None # Return None if absolutely nothing was found
#         elif not ratings_data['star_percentages'] and (ratings_data['overall_rating'] is not None or ratings_data['total_ratings_count'] is not None):
#              # print("DEBUG: Failed to get star percentages, but got other rating info.") # Debugging
#              st.warning("Extracted overall rating/count, but couldn't find star percentages breakdown.")
#         elif not ratings_data['star_percentages']:
#              # print("DEBUG: No star percentage data found.") # Debugging
#              pass # Don't warn if other data also missing

#         # Sort percentages by star rating descending (5 stars first)
#         ratings_data['star_percentages'] = dict(sorted(ratings_data['star_percentages'].items(), key=lambda item: item[0], reverse=True))

#         return ratings_data

#     except Exception as e:
#         # print(f"Error during rating extraction: {e}") # Keep print for debugging
#         st.warning(f"An error occurred while extracting ratings: {e}")
#         # Return partially extracted data if possible, or None if critical failure
#         if ratings_data['overall_rating'] is None and ratings_data['total_ratings_count'] is None and not ratings_data['star_percentages']:
#              return None
#         else:
#              # Sort whatever percentages were found
#              ratings_data['star_percentages'] = dict(sorted(ratings_data['star_percentages'].items(), key=lambda item: item[0], reverse=True))
#              return ratings_data

# def get_description_score(description):
#     """Uses Gemini to score the product description."""
#     if not description or description in ["Product name not found.", "N/A"]:
#         return "Description unavailable for scoring."
#     try:
#         prompt = f"Rate this product description out of 100 based on clarity, detail, and appeal, and give a very short (1 sentence) reason for the score:\n\n---\n{description}\n---"
#         response = model.generate_content(prompt)
#         return response.text.strip() if response.text else "Error: Unable to score description (No response)"
#     except Exception as e:
#         st.error(f"Gemini Error (Scoring): {e}")
#         return f"Error scoring description: {str(e)}"

# def get_query_response(query, product_info_context):
#     """Uses Gemini to answer user queries based on extracted product data."""
#     if not query:
#         return "Please enter a question."
#     try:
#         prompt = (
#             f"Based *only* on the following product information, answer the user's query.\n"
#             f"If the information is not present, say that you cannot find that specific detail in the provided data.\n\n"
#             f"Product Information:\n{product_info_context}\n\n" # Product info context is already formatted
#             f"---\n"
#             f"User Query: {query}\n\n"
#             f"---\n"
#             f"Answer:"
#         )
#         response = model.generate_content(prompt)
#         return response.text.strip() if response.text else "Sorry, I couldn't generate a response based on the available data."
#     except Exception as e:
#         st.error(f"Gemini Error (Query): {e}")
#         return f"Error getting answer: {str(e)}"

# def text_to_speech(text, filename="output.mp3"):
#     """Generates and plays audio from text using gTTS."""
#     if not text:
#         st.warning("No text provided for speech synthesis.")
#         return
#     try:
#         tts = gTTS(text=text, lang='en', slow=False) # slow=False for normal speed
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
#             temp_filename = fp.name
#             tts.save(temp_filename)

#         audio_file = open(temp_filename, "rb")
#         audio_bytes = audio_file.read()
#         st.audio(audio_bytes, format='audio/mp3')
#         audio_file.close() # Close the file handle
#         # Ensure file is removed after playing
#         if os.path.exists(temp_filename):
#             os.remove(temp_filename)
#     except Exception as e:
#         st.error(f"Error during text-to-speech: {e}")
#         # Clean up if temp file exists and error occurred
#         if 'temp_filename' in locals() and os.path.exists(temp_filename):
#              try:
#                  os.remove(temp_filename)
#              except OSError:
#                  pass # Ignore cleanup error

# # --- Display Bar Chart for Ratings (Dynamic) ---
# def display_rating_bar_chart(star_percentages):
#     """Displays a bar chart based on the dynamically scraped star percentages."""
#     if not star_percentages or not isinstance(star_percentages, dict):
#         st.info("Rating distribution data is not available to display the chart.")
#         return

#     # Prepare data for the chart, ensuring all 5 levels are present
#     # Labels are sorted 5 Star, 4 Star, ... based on dict sorting
#     labels = [f"{i} Star{'s' if i > 1 else ''}" for i in star_percentages.keys()]
#     sizes = list(star_percentages.values())

#     # Check if we actually have any data to plot
#     if not sizes or sum(sizes) == 0:
#         st.info("Rating distribution data contains only zero or no percentages.")
#         return

#     # Define colors (can customize) - ensure length matches number of bars
#     # Green to Red gradient for 5 bars
#     base_colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336']
#     colors = base_colors[:len(labels)] # Use only as many colors as needed

#     try:
#         fig, ax = plt.subplots(figsize=(7, 4)) # Adjust figure size if needed
#         bars = ax.bar(labels, sizes, color=colors)

#         # Add percentage labels on top of bars
#         ax.bar_label(bars, fmt='%d%%', padding=3)

#         ax.set_ylabel('Percentage of Total Ratings')
#         ax.set_title('Customer Rating Distribution')
#         ax.set_ylim(0, max(105, max(sizes) + 10)) # Set y-limit based on max value + padding
#         # Improve layout
#         plt.xticks(rotation=0, ha='center') # Keep labels horizontal
#         plt.tight_layout() # Adjust layout

#         st.pyplot(fig)

#     except Exception as e:
#         st.error(f"Error generating rating chart: {e}")


# # --- Streamlit Application Layout ---
# st.set_page_config(layout="wide") # Use wider layout
# st.title("📢 Amazon Product Analyzer")

# # --- Initialize Session State ---
# if 'product_data_loaded' not in st.session_state:
#     st.session_state.product_data_loaded = False

# # User inputs the Amazon product URL
# url = st.text_input("Enter the Amazon product URL:", placeholder="e.g., https://www.amazon.com/dp/ASIN_HERE")

# # Add a submit button
# submit_button = st.button("📊 Analyze Product")

# if submit_button and url:
#     # Validate URL roughly
#     if not (url.startswith("http://") or url.startswith("https://")) or "amazon." not in url or ("/dp/" not in url and "/product/" not in url): # Allow /product/ too
#          st.error("Invalid Amazon product URL format. Please use a URL like 'https://www.amazon.com/dp/ASIN' or 'https://www.amazon.com/PRODUCT-NAME/dp/ASIN'.")
#     else:
#         with st.spinner("Fetching and analyzing product data... Please wait."):
#             soup = html_code(url)
#             if soup:
#                 # --- Perform all extractions ---
#                 st.session_state.product_name = extract_product_details(soup)
#                 st.session_state.ratings_info = get_amazon_ratings_from_soup(soup) # Detailed ratings
#                 st.session_state.other_info = extract_other_product_info(soup) # Price, color, snippet <<< THIS IS WHERE THE NEW FUNCTION IS CALLED
#                 st.session_state.product_specs = extract_product_specifications(soup) # Specs (excluding price/colour now)

#                 # --- Generate Description Score ---
#                 # Create a basic description string for scoring
#                 desc_parts = [f"Product Name: {st.session_state.product_name}"]
#                 if st.session_state.other_info.get('price') not in ["N/A", "Price not found", "Error extracting price"]:
#                      desc_parts.append(f"Price: {st.session_state.other_info['price']}")
#                 if st.session_state.other_info.get('colour') not in ["N/A", "Colour not found", "Error extracting colour"]:
#                      desc_parts.append(f"Colour: {st.session_state.other_info['colour']}")
#                 description_string = ". ".join(desc_parts) + "."
#                 # Add a few key specs if available? Be concise.
#                 if st.session_state.product_specs and isinstance(st.session_state.product_specs, dict):
#                      spec_sample = list(st.session_state.product_specs.items())[:2] # Max 2 specs for brevity
#                      if spec_sample:
#                           description_string += " Specs include: " + ", ".join([f"{k}: {v}" for k,v in spec_sample]) + "."

#                 st.session_state.description_score = get_description_score(description_string)

#                 # --- Mark data as loaded ---
#                 st.session_state.product_data_loaded = True
#                 st.success("✅ Analysis complete!")

#             else:
#                 st.error("Failed to retrieve or parse webpage. Please check the URL or try again later. Amazon might be blocking the request.")
#                 st.session_state.product_data_loaded = False # Reset flag on failure

# # Clear data if URL is cleared or submit wasn't pressed this time
# elif not url and 'product_data_loaded' in st.session_state and st.session_state.product_data_loaded:
#      st.session_state.product_data_loaded = False
#      # Optionally clear specific keys if needed
#      keys_to_clear = ['product_name', 'ratings_info', 'other_info', 'product_specs', 'description_score']
#      for key in keys_to_clear:
#           if key in st.session_state:
#                del st.session_state[key]


# # --- Display Area (only shows if data is loaded) ---
# if st.session_state.get('product_data_loaded', False):

#     # Use columns for layout
#     col1, col2 = st.columns([2, 1]) # Main content takes 2/3, sidebar-like info 1/3

#     with col1:
#         st.header(f"📊 Analysis Results for: {st.session_state.get('product_name', 'Product')}")
#         st.markdown("---")

#         # --- Display Rating Summary ---
#         st.subheader("⭐ Customer Ratings")
#         if st.session_state.get('ratings_info') and isinstance(st.session_state.ratings_info, dict):
#             overall_rating = st.session_state['ratings_info'].get('overall_rating', 'N/A')
#             total_ratings = st.session_state['ratings_info'].get('total_ratings_count', 'N/A')
#             total_ratings_display = "N/A"
#             if isinstance(total_ratings, int):
#                 total_ratings_display = f"{total_ratings:,}" # Format with comma
#             elif isinstance(total_ratings, str):
#                 total_ratings_display = total_ratings # Keep string if not int

#             rating_value_display = "N/A"
#             if isinstance(overall_rating, (float, int)):
#                  rating_value_display = f"{overall_rating:.1f} / 5 Stars" # Format to 1 decimal place
#             elif isinstance(overall_rating, str):
#                  rating_value_display = overall_rating # Keep string if not number


#             st.metric(label="Average Rating",
#                       value=rating_value_display,
#                       delta=f"{total_ratings_display} Global Ratings" if total_ratings_display != 'N/A' else None,
#                       delta_color="off") # Don't color delta

#             # --- Display Rating Bar Chart ---
#             display_rating_bar_chart(st.session_state['ratings_info'].get('star_percentages'))
#         else:
#             st.info("Detailed rating information could not be extracted or is unavailable.")

#         # --- Display Review Snippet Text --- <<< NEW DISPLAY SECTION
#         review_snippet = st.session_state.get('other_info', {}).get('review_snippet', 'N/A')
#         # Check if the snippet is valid and not one of the error/default messages
#         if review_snippet and review_snippet not in ["Review snippet not found", "N/A", "Error extracting snippet"]:
#              st.subheader("💬 Overall Review")
#              # Use markdown blockquote for emphasis
#              st.markdown(f"> _{review_snippet}_")


#         # --- Text-to-Speech Button ---
#         st.subheader("🔊 Audio Summary")
#         if st.button("Read Rating & Snippet"):
#              tts_text_parts = []
#              # Add rating info if available
#              if st.session_state.get('ratings_info') and isinstance(st.session_state.ratings_info, dict):
#                  overall_rating = st.session_state['ratings_info'].get('overall_rating')
#                  total_ratings = st.session_state['ratings_info'].get('total_ratings_count')
#                  if isinstance(overall_rating, (float, int)):
#                      rating_part = f"The average rating is {overall_rating:.1f} out of 5 stars"
#                      if isinstance(total_ratings, int):
#                           rating_part += f", based on {total_ratings:,} global ratings. "
#                      else:
#                           rating_part += "."
#                      tts_text_parts.append(rating_part)
#                  elif total_ratings: # If only count is available
#                       tts_text_parts.append(f"Based on {total_ratings:,} global ratings.")
#                  else:
#                      tts_text_parts.append("Rating information unavailable.")
#              else:
#                   tts_text_parts.append("Rating information unavailable.")

#              # Add review snippet if available and valid
#              if review_snippet and review_snippet not in ["Review snippet not found", "N/A", "Error extracting snippet"]:
#                  # Remove potential "Title: " prefix for cleaner speech
#                  snippet_for_speech = review_snippet.removeprefix("Title: ").strip()
#                  tts_text_parts.append(f"A review snippet says: {snippet_for_speech}")
#              else:
#                  tts_text_parts.append("No review snippet available.")

#              final_tts_text = " ".join(tts_text_parts)
#              text_to_speech(final_tts_text)


#         # --- User Query Section ---
#         st.subheader("❓ Ask Gemini about this Product")
#         user_query = st.text_input("Your question:", placeholder="e.g., What material is it made of? Is it waterproof?")

#         if st.button("💬 Get Answer") and user_query:
#             # Prepare context for Gemini - Include Price and Colour now
#             context_parts = [f"Product Name: {st.session_state.get('product_name', 'N/A')}"]
#             other_info = st.session_state.get('other_info', {})
#             price = other_info.get('price', 'N/A')
#             colour = other_info.get('colour', 'N/A')

#             if price not in ["N/A", "Price not found", "Error extracting price"]:
#                  context_parts.append(f"Price: {price}")
#             if colour not in ["N/A", "Colour not found", "Error extracting colour"]:
#                  context_parts.append(f"Colour: {colour}")

#             specs = st.session_state.get('product_specs', {})
#             if isinstance(specs, dict) and specs:
#                  # Format specs nicely for the context
#                  specs_string = "\n".join([f"- {key}: {value}" for key, value in specs.items()])
#                  context_parts.append(f"Specifications:\n{specs_string}")
#             elif isinstance(specs, str): # Handle case where specs extraction returned string error
#                  context_parts.append(f"Specifications: {specs}")
#             else:
#                  context_parts.append("Specifications: Not available")

#             product_info_context = "\n".join(context_parts)

#             with st.spinner("Asking Gemini..."):
#                 query_response = get_query_response(user_query, product_info_context)
#                 st.markdown("**Gemini's Response:**")
#                 # Use an info box for better visibility
#                 st.info(query_response)

#     with col2:
#         st.header("📦 Product Info Summary")
#         st.markdown("---")
#         # Display Name, Price, and Colour <<< ADDED PRICE AND COLOUR HERE
#         st.write(f"**🏷️ Name:** {st.session_state.get('product_name', 'N/A')}")
#         st.write(f"**💲 Price:** {st.session_state.get('other_info', {}).get('price', 'N/A')}")
#         st.subheader("🤖 Description Score")
#         # Use an info box for the score
#         st.info(f"{st.session_state.get('description_score', 'N/A')}")

#         st.subheader("⚙️ Specifications")
#         specs = st.session_state.get('product_specs', {})
#         if isinstance(specs, dict) and specs:
#             # Use an expander for potentially long spec lists
#             with st.expander("View Extracted Specifications", expanded=False):
#                  # Display as Key: Value pairs
#                  for key, value in specs.items():
#                      st.markdown(f"**{key}:** {value}")
#         elif isinstance(specs, str): # Handle case where specs extraction returned string error
#              st.write(specs)
#         else:
#             st.write("No specifications found or extracted.")

# else:
#     # Show instructions if no analysis has run yet
#     if not url:
#         st.info("☝️ Enter an Amazon product URL above and click 'Analyze Product'.")
#     # No need for an explicit else here if submit button wasn't pressed but url exists

# # Add a footer (optional)
# st.markdown("---")
# st.caption("Amazon Product Analyzer | Uses Web Scraping & Google Gemini | Accuracy depends on Amazon's page structure and may vary.")




# -*- coding: utf-8 -*-
# Add this near the other imports
import requests
from bs4 import BeautifulSoup
import streamlit as st
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os
import google.generativeai as genai
from gtts import gTTS
import tempfile
import re # Needed for rating extraction
import json # Good for debugging extracted data

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("🔴 GEMINI_API_KEY not found. Please set it in your .env file.")
    st.stop() # Stop execution if key is missing

try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Configure the model for summarization task specifically if needed,
    # or use the existing general model. Sticking with existing for now.
    model = genai.GenerativeModel(
         model_name='models/gemini-1.5-flash', # Or use 'gemini-pro'
        generation_config={
            "temperature": 0.5, # Slightly higher temp might be okay for summarization
            "max_output_tokens": 150, # Keep relatively low for a short summary
            "top_p": 0.9,
            "top_k": 40
        },
        safety_settings=[
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ],
        # System instruction could be refined for summarization, but let's keep the general one
        system_instruction="You are a helpful assistant that analyzes Amazon product data. When asked for an overall review summary based on limited data (like average rating, count, and maybe a single snippet or star distribution), provide a concise (max 3 lines) interpretation of the general customer sentiment reflected in that data. Acknowledge if the data suggests mixed opinions."
    )
except Exception as e:
    st.error(f"🔴 Error configuring Gemini: {e}")
    st.stop()

HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1'
}

def getdata(url):
    """Fetches HTML content from a URL."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.text
    except requests.exceptions.Timeout:
        st.warning(f"Request timed out for {url}")
        return None
    except requests.exceptions.RequestException as e:
        st.warning(f"Error fetching {url}: {e}")
        return None

def html_code(url):
    """Parses HTML content using BeautifulSoup."""
    htmldata = getdata(url)
    if htmldata:
        try:
            soup = BeautifulSoup(htmldata, 'html.parser')
            return soup
        except Exception as e:
            st.warning(f"Error parsing HTML: {e}")
            return None
    return None

def extract_product_details(soup):
    """Extracts the main product title."""
    if not soup: return "Product name not found"
    try:
        title_element = soup.find('span', id='productTitle')
        product_name = title_element.get_text(strip=True) if title_element else "Product name not found"
        return product_name
    except Exception:
        return "Product name not found"

def extract_product_specifications(soup):
    """Extracts product specifications, trying multiple table structures."""
    if not soup: return {}
    specs = {}
    try:
        spec_table = soup.find("table", id="productDetails_techSpec_section_1")
        if not spec_table:
            spec_table = soup.find("table", id="productDetails_detailBullets_sections1")
        if not spec_table:
             spec_table = soup.find('table', class_='prodDetTable')

        if spec_table:
            rows = spec_table.find_all("tr")
            for row in rows:
                header_cell = row.find("th")
                value_cell = row.find("td")
                if header_cell and value_cell:
                    key = header_cell.get_text(strip=True)
                    value = value_cell.get_text(strip=True).replace('\n', ' ').replace('\u200e', '').replace('\u200f', '')
                    if key.lower() not in ['color', 'colour', 'price']:
                        specs[key] = value

        detail_bullets = soup.find('div', id='detailBullets_feature_div')
        if detail_bullets:
            list_items = detail_bullets.find_all('li')
            for item in list_items:
                 key_span = item.find('span', class_='a-text-bold')
                 if key_span:
                     key = key_span.get_text(strip=True).replace(':','').strip()
                     value_part = key_span.next_sibling
                     value = ""
                     if value_part and isinstance(value_part, str):
                         value = value_part.strip()
                     elif item.find('span', class_='a-list-item'):
                          value_span = item.find('span', class_='a-list-item')
                          full_text = value_span.get_text(strip=True)
                          key_text_in_val = key_span.get_text(strip=True)
                          value = full_text.replace(key_text_in_val, '').strip()

                     if key and value and key.lower() not in ['color', 'colour', 'price', 'customer reviews', 'best sellers rank', 'date first available', 'asin']: # Exclude review links etc.
                         # Additional check to avoid adding rating summary here
                         if 'out of 5 stars' not in value.lower() and 'ratings' not in value.lower():
                            specs[key] = value
        return specs
    except Exception as e:
        st.warning(f"Error extracting specifications: {e}")
        return {}


def extract_other_product_info(soup):
    """Extracts price, colour, and a sample review snippet."""
    if not soup:
        return {"price": "N/A", "colour": "N/A", "review_snippet": "N/A"}

    info = {
        "price": "Price not found",
        "colour": "Colour not found",
        "review_snippet": "Review snippet not found"
    }
    try:
        # --- Price Extraction ---
        price_element = soup.select_one('span.a-price span[aria-hidden="true"]')
        if not price_element: price_element = soup.select_one('span.a-offscreen')
        if not price_element: price_element = soup.find("span", class_="priceToPay")
        if not price_element: price_element = soup.find("span", id="priceblock_ourprice")
        if not price_element: price_element = soup.find("span", id="priceblock_dealprice")
        if price_element:
            info["price"] = price_element.get_text(strip=True)
        else:
            deal_badge_price = soup.select_one('span[data-a-strike="true"] span[aria-hidden="true"]')
            if deal_badge_price:
                actual_price_nearby = deal_badge_price.find_next('span', class_='a-offscreen')
                if actual_price_nearby: info["price"] = actual_price_nearby.get_text(strip=True)

        # --- Colour Extraction ---
        colour_swatch = soup.select_one('div#variation_color_name span.selection')
        if colour_swatch: info["colour"] = colour_swatch.get_text(strip=True)
        else:
            details_container = soup.find('div', id='detailBullets_feature_div') or soup.find('div', id='productDetails_feature_div')
            if details_container:
                list_items = details_container.find_all('li')
                for item in list_items:
                     text = item.get_text(strip=True)
                     match = re.match(r"(?:Color|Colour)\s*:\s*(.*)", text, re.IGNORECASE)
                     if match:
                          info["colour"] = match.group(1).strip(); break
            if info["colour"] == "Colour not found":
                 feature_bullets = soup.find('div', id='feature-bullets')
                 if feature_bullets:
                      list_items = feature_bullets.find_all('li')
                      for item in list_items:
                           text = item.get_text(strip=True)
                           if "color" in text.lower() or "colour" in text.lower():
                                parts = text.split(':')
                                if len(parts) > 1 and ('color' in parts[0].lower() or 'colour' in parts[0].lower()):
                                     info["colour"] = parts[1].strip(); break

        # --- Sample Review Snippet Extraction ---
        review_body_element = soup.find('span', {'data-hook': 'review-body'})
        if review_body_element:
            full_review_text = review_body_element.get_text(strip=True)
            info["review_snippet"] = (full_review_text[:250] + '...') if len(full_review_text) > 250 else full_review_text
        else:
             review_title_link = soup.find('a', {'data-hook': 'review-title'})
             if review_title_link:
                  review_title_span = review_title_link.find('span', recursive=False)
                  if review_title_span: info["review_snippet"] = "Title: " + review_title_span.get_text(strip=True)
        return info
    except Exception as e:
        st.warning(f"Error extracting price/colour/snippet: {e}")
        return { # Return dictionary with error indicators
            "price": info.get("price", "Error extracting price"),
            "colour": info.get("colour", "Error extracting colour"),
            "review_snippet": info.get("review_snippet", "Error extracting snippet") }

def get_amazon_ratings_from_soup(soup):
    """Extracts detailed rating information (overall, count, percentages)."""
    if not soup: return None
    ratings_data = { 'overall_rating': None, 'total_ratings_count': None, 'star_percentages': {} }
    try:
        # --- Overall Rating ---
        rating_text = None
        rating_icon_span = soup.find('i', {'data-hook': 'average-star-rating'})
        if rating_icon_span: rating_text_span = rating_icon_span.find('span', class_='a-icon-alt'); rating_text = rating_text_span.text.strip() if rating_text_span else None
        if not rating_text: rating_span_alt = soup.find('span', {'data-hook': 'rating-out-of-text'}); rating_text = rating_span_alt.text.strip() if rating_span_alt else None
        if not rating_text: rating_element = soup.select_one('span[data-asin-review-star-rating] span.a-icon-alt'); rating_text = rating_element.get_text(strip=True) if rating_element else None
        if not rating_text: rating_element = soup.select_one('span.reviewNumericalSummary span.a-declarative a span.a-size-medium.a-color-base'); rating_text = (rating_element.get_text(strip=True) + " out of 5") if rating_element else None
        if rating_text:
            match = re.search(r'([\d.]+)\s+out\s+of\s+5', rating_text, re.IGNORECASE)
            if match: ratings_data['overall_rating'] = float(match.group(1))
            else: match_num_only = re.search(r'^([\d.]+)$', rating_text.strip()); ratings_data['overall_rating'] = float(match_num_only.group(1)) if match_num_only else None

        # --- Total Ratings Count ---
        count_element = soup.find('span', {'data-hook': 'total-review-count'})
        if not count_element: count_element = soup.find('span', id='acrCustomerReviewText')
        if count_element:
            count_text_content = count_element.get_text(strip=True)
            count_text_match = re.search(r'([\d,]+)', count_text_content)
            if count_text_match: count_text = count_text_match.group(1).replace(',', ''); ratings_data['total_ratings_count'] = int(count_text) if count_text.isdigit() else None

        # --- Star Percentages ---
        percentage_links = soup.find_all('a', {'aria-label': re.compile(r'\d+\s*percent of reviews have \d+ stars?', re.IGNORECASE)})
        if percentage_links:
            for link in percentage_links:
                aria_label_text = link.get('aria-label', '').strip()
                star_match = re.search(r'have\s+(\d+)\s+stars?', aria_label_text, re.IGNORECASE)
                percent_match = re.search(r'^(\d+)\s*percent', aria_label_text, re.IGNORECASE)
                if star_match and percent_match: ratings_data['star_percentages'][int(star_match.group(1))] = int(percent_match.group(1))

        if not ratings_data['star_percentages']:
            histogram_rows = soup.select('table#histogramTable tr.a-histogram-row')
            if not histogram_rows: histogram_rows = soup.select('tr[data-reviews-state*="histogram-row"]')
            if not histogram_rows: histogram_rows = soup.select('td.a-text-right > span.a-size-base > a[title*="%"]')
            if histogram_rows:
                 for row in histogram_rows:
                     star_text_element = row.find(['span', 'a'], string=re.compile(r'\d+\s+star'), class_=re.compile(r'a-size-base|a-link-normal'))
                     percentage_text_element = row.find(['span', 'a'], class_=re.compile(r'a-text-right|a-link-normal'), title=re.compile(r'\d+%'))
                     if not percentage_text_element: percentage_text_element = row.find(['span', 'a'], string=re.compile(r'\d+%'))
                     if star_text_element and percentage_text_element:
                         star_text = star_text_element.get_text(strip=True)
                         percentage_text = percentage_text_element.get_text(strip=True); percentage_title = percentage_text_element.get('title', '')
                         star_match = re.search(r'(\d+)\s+star', star_text, re.IGNORECASE)
                         percent_match = re.search(r'(\d+)%', percentage_title);
                         if not percent_match: percent_match = re.search(r'(\d+)%', percentage_text)
                         if star_match and percent_match: ratings_data['star_percentages'][int(star_match.group(1))] = int(percent_match.group(1))

        # --- Final Checks ---
        if ratings_data['overall_rating'] is None and ratings_data['total_ratings_count'] is None and not ratings_data['star_percentages']:
            st.warning("Could not extract detailed rating information.")
            return None
        elif not ratings_data['star_percentages'] and (ratings_data['overall_rating'] is not None or ratings_data['total_ratings_count'] is not None):
             st.warning("Extracted overall rating/count, but couldn't find star percentages breakdown.")
        ratings_data['star_percentages'] = dict(sorted(ratings_data['star_percentages'].items(), key=lambda item: item[0], reverse=True))
        return ratings_data
    except Exception as e:
        st.warning(f"An error occurred while extracting ratings: {e}")
        if ratings_data['overall_rating'] is None and ratings_data['total_ratings_count'] is None and not ratings_data['star_percentages']: return None
        else: ratings_data['star_percentages'] = dict(sorted(ratings_data['star_percentages'].items(), key=lambda item: item[0], reverse=True)); return ratings_data


def get_description_score(description):
    if not description or description in ["Product name not found.", "N/A"]:
        return "Description unavailable for scoring."
    try:
        prompt = f"Rate this product description out of 100 based on clarity, detail, and appeal, and give a very short (1 sentence) reason for the score:\n\n---\n{description}\n---"
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "Error: Unable to score description (No response)"
    except Exception as e:
        st.error(f"Gemini Error (Scoring): {e}")
        return f"Error scoring description: {str(e)}"

# --- NEW FUNCTION: Generate Overall Review Summary ---
def generate_overall_review_summary(product_name, ratings_info, review_snippet):
    """
    Uses Gemini to generate a concise (max 3 lines) overall review summary
    based on the limited available data (ratings, snippet).
    This is an *inferred* summary, not based on reading all reviews.
    """
    if not ratings_info and not review_snippet:
        return "Not enough data available to generate an overall summary."

    # Prepare context data
    overall_rating = "N/A"
    total_ratings = "N/A"
    star_percentages_str = "Not available"

    if ratings_info and isinstance(ratings_info, dict):
        if ratings_info.get('overall_rating') is not None:
            overall_rating = f"{ratings_info['overall_rating']:.1f}" # Format rating
        if ratings_info.get('total_ratings_count') is not None:
            total_ratings = f"{ratings_info['total_ratings_count']:,}" # Format count
        if ratings_info.get('star_percentages'):
            star_percentages_str = ", ".join([f"{k}-star: {v}%" for k, v in ratings_info['star_percentages'].items()])

   # snippet_for_prompt = review_snippet if review_snippet and review_snippet not in ["Review snippet not found", "N/A", "Error extracting snippet"] else "Not available"

    try:
        prompt = (
            f"Based ONLY on the following limited data extracted from the main product page for '{product_name}', "
            f"generate a concise (maximum 5 lines) overall review summary reflecting the likely general customer sentiment. "
            f"Mention if the data suggests mixed opinions (e.g., high rating but some low stars, or contrasting snippet).\n\n"
            f"Data:\n"
            f"- Overall Rating: {overall_rating} / 5 stars\n"
            f"- Total Ratings: {total_ratings}\n"
            f"- Rating Breakdown (%): {star_percentages_str}\n"
          #  f"- Sample Review Snippet: {snippet_for_prompt}\n\n"
            f"---\n"
            f"Inferred Overall Summary (max 3 lines):\n"
        )

        response = model.generate_content(prompt)

        # Basic cleaning: Remove potential markdown list markers if AI adds them
        summary_text = response.text.strip().replace("- ", "").replace("* ", "")
        # Ensure it's roughly 3 lines (split by newline, take first 3)
        summary_lines = summary_text.split('\n')
        final_summary = "\n".join(summary_lines[:3])

        return final_summary if final_summary else "Could not generate summary from available data."

    except Exception as e:
        st.error(f"Gemini Error (Summary Generation): {e}")
        return f"Error generating overall summary: {str(e)}"
# --- END OF NEW FUNCTION ---


def get_query_response(query, product_info_context):
    """Uses Gemini to answer user queries based on extracted product data."""
    if not query: return "Please enter a question."
    try:
        prompt = (
    f"Using *only* the information given below, answer the user's query.\n"
    f"If a specific detail is missing, clearly state that it is not available in the provided data.\n"
    f"When prices are mentioned, convert them into Indian Rupees (INR) using these fixed rates:\n"
    f"- 1 US Dollar (USD) = 85.38 Indian Rupees (INR)\n"
    f"- 1 British Pound (GBP) = 113.67 Indian Rupees (INR)\n\n"
    f"Product Details:\n{product_info_context}\n\n"
    f"---\nUser Query: {query}\n---\nResponse:"
)


        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "Sorry, I couldn't generate a response based on the available data."
    except Exception as e:
        st.error(f"Gemini Error (Query): {e}")
        return f"Error getting answer: {str(e)}"

def text_to_speech(text, filename="output.mp3"):
    """Generates and plays audio from text using gTTS."""
    if not text: st.warning("No text provided for speech synthesis."); return
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_filename = fp.name; tts.save(temp_filename)
        with open(temp_filename, "rb") as audio_file: audio_bytes = audio_file.read()
        st.audio(audio_bytes, format='audio/mp3')
        if os.path.exists(temp_filename): os.remove(temp_filename)
    except Exception as e:
        st.error(f"Error during text-to-speech: {e}")
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
             try: os.remove(temp_filename)
             except OSError: pass

def display_rating_bar_chart(star_percentages):
    """Displays a bar chart based on the dynamically scraped star percentages."""
    if not star_percentages or not isinstance(star_percentages, dict):
        st.info("Rating distribution data is not available to display the chart."); return
    labels = [f"{i} Star{'s' if i > 1 else ''}" for i in star_percentages.keys()]
    sizes = list(star_percentages.values())
    if not sizes or sum(sizes) == 0:
        st.info("Rating distribution data contains only zero or no percentages."); return
    base_colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336']; colors = base_colors[:len(labels)]
    try:
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.bar(labels, sizes, color=colors)
        ax.bar_label(bars, fmt='%d%%', padding=3)
        ax.set_ylabel('Percentage of Total Ratings'); ax.set_title('Customer Rating Distribution')
        ax.set_ylim(0, max(105, max(sizes) + 10))
        plt.xticks(rotation=0, ha='center'); plt.tight_layout(); st.pyplot(fig)
    except Exception as e: st.error(f"Error generating rating chart: {e}")


# --- Streamlit Application Layout ---
st.set_page_config(layout="wide")
st.title("📢 Amazon Product Analyzer")

# --- Initialize Session State ---
if 'product_data_loaded' not in st.session_state: st.session_state.product_data_loaded = False
if 'overall_summary' not in st.session_state: st.session_state.overall_summary = None # Initialize summary state

url = st.text_input("Enter the Amazon product URL:", placeholder="e.g., https://www.amazon.com/dp/ASIN_HERE")
submit_button = st.button("📊 Analyze Product")

if submit_button and url:
    if not (url.startswith("http://") or url.startswith("https://")) or "amazon." not in url or ("/dp/" not in url and "/product/" not in url):
         st.error("Invalid Amazon product URL format.")
    else:
        with st.spinner("Fetching and analyzing product data... Please wait."):
            soup = html_code(url)
            if soup:
                st.session_state.product_name = extract_product_details(soup)
                st.session_state.ratings_info = get_amazon_ratings_from_soup(soup)
                st.session_state.other_info = extract_other_product_info(soup)
                st.session_state.product_specs = extract_product_specifications(soup)

                # --- Generate Description Score ---
                desc_parts = [f"Product Name: {st.session_state.product_name}"]
                price = st.session_state.other_info.get('price')
                colour = st.session_state.other_info.get('colour')
                if price not in ["N/A", "Price not found", "Error extracting price"]: desc_parts.append(f"Price: {price}")
                if colour not in ["N/A", "Colour not found", "Error extracting colour"]: desc_parts.append(f"Colour: {colour}")
                description_string = ". ".join(desc_parts) + "."
                if st.session_state.product_specs and isinstance(st.session_state.product_specs, dict):
                     spec_sample = list(st.session_state.product_specs.items())[:2]
                     if spec_sample: description_string += " Specs include: " + ", ".join([f"{k}: {v}" for k,v in spec_sample]) + "."
                st.session_state.description_score = get_description_score(description_string)

                # --- Generate Overall Review Summary (Inferred) --- <<< NEW CALL
                with st.spinner("Generating overall review summary..."): # Nested spinner
                    st.session_state.overall_summary = generate_overall_review_summary(
                        st.session_state.product_name,
                        st.session_state.ratings_info,
                        st.session_state.other_info.get('review_snippet')
                    )

                st.session_state.product_data_loaded = True
                st.success("✅ Analysis complete!")
            else:
                st.error("Failed to retrieve or parse webpage. Please check the URL or try again later.")
                st.session_state.product_data_loaded = False
                st.session_state.overall_summary = None # Reset on failure

elif not url and 'product_data_loaded' in st.session_state and st.session_state.product_data_loaded:
     st.session_state.product_data_loaded = False
     keys_to_clear = ['product_name', 'ratings_info', 'other_info', 'product_specs', 'description_score', 'overall_summary'] # Add overall_summary
     for key in keys_to_clear:
          if key in st.session_state: del st.session_state[key]


# --- Display Area ---
if st.session_state.get('product_data_loaded', False):
    col1, col2 = st.columns([2, 1])
    with col1:
        st.header(f"📊 Analysis Results for: {st.session_state.get('product_name', 'Product')}")
        st.markdown("---")

        # --- Display Rating Summary ---
        st.subheader("⭐ Customer Ratings")
        if st.session_state.get('ratings_info') and isinstance(st.session_state.ratings_info, dict):
            overall_rating = st.session_state['ratings_info'].get('overall_rating', 'N/A')
            total_ratings = st.session_state['ratings_info'].get('total_ratings_count', 'N/A')
            total_ratings_display = "N/A"
            if isinstance(total_ratings, int): total_ratings_display = f"{total_ratings:,}"
            elif isinstance(total_ratings, str): total_ratings_display = total_ratings
            rating_value_display = "N/A"
            if isinstance(overall_rating, (float, int)): rating_value_display = f"{overall_rating:.1f} / 5 Stars"
            elif isinstance(overall_rating, str): rating_value_display = overall_rating
            st.metric(label="Average Rating", value=rating_value_display,
                      delta=f"{total_ratings_display} Global Ratings" if total_ratings_display != 'N/A' else None,
                      delta_color="off")
            display_rating_bar_chart(st.session_state['ratings_info'].get('star_percentages'))
        else:
            st.info("Detailed rating information could not be extracted or is unavailable.")

        # --- Display Inferred Overall Review Summary --- <<< NEW SECTION
        st.subheader("📝Overall Review Summary")
       # st.caption("(Generated by AI based on available rating data & snippet - max 3 lines)")
        overall_summary = st.session_state.get('overall_summary', "Summary could not be generated.")
        # Use markdown blockquote or info box for the summary
        st.info(overall_summary) # Using info box


        # --- Display Review Snippet Text ---
        review_snippet = st.session_state.get('other_info', {}).get('review_snippet', 'N/A')
        if review_snippet and review_snippet not in ["Review snippet not found", "N/A", "Error extracting snippet"]:
             #st.subheader("💬 Sample Review Snippet")
            # st.caption("(Extracted from one review body or title)")
            # st.markdown(f"> _{review_snippet}_")

        # --- Text-to-Speech Button ---
         st.subheader("🔊 Audio Summary")
        # Add overall summary to TTS? Optional, could make it long. Let's add it for now.
        if st.button("Read Rating, Summary & Snippet"):
             tts_text_parts = []
             # Rating
             if st.session_state.get('ratings_info') and isinstance(st.session_state.ratings_info, dict):
                 overall_rating = st.session_state['ratings_info'].get('overall_rating')
                 total_ratings = st.session_state['ratings_info'].get('total_ratings_count')
                 rating_part = ""
                 if isinstance(overall_rating, (float, int)):
                     rating_part = f"The average rating is {overall_rating:.1f} out of 5 stars"
                     if isinstance(total_ratings, int): rating_part += f", based on {total_ratings:,} global ratings. "
                     else: rating_part += ". "
                 elif total_ratings: rating_part = f"Based on {total_ratings:,} global ratings. "
                 else: rating_part = "Rating information unavailable. "
                 tts_text_parts.append(rating_part)
             else: tts_text_parts.append("Rating information unavailable. ")
             # Overall Summary
             if overall_summary and "Could not generate" not in overall_summary and "Error generating" not in overall_summary:
                 tts_text_parts.append(f"The inferred overall summary is: {overall_summary}")
             # Snippet
             if review_snippet and review_snippet not in ["Review snippet not found", "N/A", "Error extracting snippet"]:
                 snippet_for_speech = review_snippet.removeprefix("Title: ").strip()
                # tts_text_parts.append(f"A sample review snippet says: {snippet_for_speech}")

             final_tts_text = " ".join(tts_text_parts)
             text_to_speech(final_tts_text)


        # --- User Query Section ---
        st.subheader("❓ Ask Gemini about this Product")
      #  st.caption("Based on extracted data (Name, Price, Colour, Specs)")
        user_query = st.text_input("Your question:", placeholder="e.g., What material is it made of? Is it waterproof?")
        if st.button("💬 Get Answer") and user_query:
            context_parts = [f"Product Name: {st.session_state.get('product_name', 'N/A')}"]
            other_info = st.session_state.get('other_info', {})
            price = other_info.get('price', 'N/A')
            colour = other_info.get('colour', 'N/A')
            if price not in ["N/A", "Price not found", "Error extracting price"]: context_parts.append(f"Price: {price}")
            if colour not in ["N/A", "Colour not found", "Error extracting colour"]: context_parts.append(f"Colour: {colour}")
            specs = st.session_state.get('product_specs', {})
            if isinstance(specs, dict) and specs:
                 specs_string = "\n".join([f"- {key}: {value}" for key, value in specs.items()])
                 context_parts.append(f"Specifications:\n{specs_string}")
            elif isinstance(specs, str): context_parts.append(f"Specifications: {specs}")
            else: context_parts.append("Specifications: Not available")
            product_info_context = "\n".join(context_parts)
            with st.spinner("Asking Gemini..."):
                query_response = get_query_response(user_query, product_info_context)
                st.markdown("**Gemini's Response:**")
                st.info(query_response)

    with col2:
        st.header("📦 Product Info Summary")
        st.markdown("---")
        st.write(f"**🏷️ Name:** {st.session_state.get('product_name', 'N/A')}")
        st.write(f"**💲 Price:** {st.session_state.get('other_info', {}).get('price', 'N/A')}")
       # st.write(f"**🎨 Colour:** {st.session_state.get('other_info', {}).get('colour', 'N/A')}")
        st.subheader("🤖 Description Score")
        st.info(f"{st.session_state.get('description_score', 'N/A')}")
        st.subheader("⚙️ Specifications")
        specs = st.session_state.get('product_specs', {})
        if isinstance(specs, dict) and specs:
            with st.expander("View Extracted Specifications", expanded=False):
                 for key, value in specs.items(): st.markdown(f"**{key}:** {value}")
        elif isinstance(specs, str): st.write(specs)
        else: st.write("No specifications found or extracted.")

else:
    if not url: st.info("☝️ Enter an Amazon product URL above and click 'Analyze Product'.")

st.markdown("---")
st.caption("Amazon Product Analyzer | Uses Web Scraping & Google Gemini | Accuracy depends on Amazon's page structure. Overall summary is AI-inferred from limited data.")