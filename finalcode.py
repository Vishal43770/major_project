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

# # --- Load environment variables ---
# load_dotenv()
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# # --- Configure Gemini ---
# # Check if API key is loaded
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


# # --- Define headers to mimic a real browser request ---
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

# # --- Web Scraping Helper Functions ---
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

# # --- Combined Extraction Functions ---

# def extract_product_details(soup):
#     """Extracts Product Title."""
#     if not soup: return "Product name not found"
#     try:
#         title_element = soup.find('span', id='productTitle')
#         product_name = title_element.get_text(strip=True) if title_element else "Product name not found"
#         return product_name
#     except Exception:
#         return "Product name not found"

# def extract_product_specifications(soup):
#     """Extracts Product Specifications from tables."""
#     if not soup: return {}
#     specs = {}
#     try:
#         # Look for different possible table IDs
#         spec_table = soup.find("table", id="productDetails_techSpec_section_1")
#         if not spec_table:
#             spec_table = soup.find("table", id="productDetails_detailBullets_sections1")
#         # Add more potential table IDs or classes if needed
#         if not spec_table:
#              # Fallback: Look for a table with class 'prodDetTable'
#              spec_table = soup.find('table', class_='prodDetTable')

#         if spec_table:
#             rows = spec_table.find_all("tr")
#             for row in rows:
#                 header_cell = row.find("th")
#                 value_cell = row.find("td")
#                 if header_cell and value_cell:
#                     key = header_cell.get_text(strip=True)
#                     value = value_cell.get_text(strip=True).replace('\n', ' ').replace('\u200e', '').replace('\u200f', '') # Clean value
#                     specs[key] = value
#             return specs

#         # Fallback: Look for detail bullet points if table fails
#         detail_bullets = soup.find('div', id='detailBullets_feature_div')
#         if detail_bullets:
#             list_items = detail_bullets.find_all('li')
#             for item in list_items:
#                  key_span = item.find('span', class_='a-text-bold')
#                  if key_span:
#                      key = key_span.get_text(strip=True).replace(':','').strip()
#                      # Find the value part (the rest of the span content after the bold part)
#                      value_part = key_span.next_sibling
#                      if value_part and isinstance(value_part, str):
#                          value = value_part.strip()
#                          if key and value:
#                              specs[key] = value
#                      elif item.find('span', class_='a-list-item'): # If value is in another span
#                           value_span = item.find('span', class_='a-list-item')
#                           # Remove the key span's text from the full list item text
#                           full_text = value_span.get_text(strip=True)
#                           key_text_in_val = key_span.get_text(strip=True)
#                           value = full_text.replace(key_text_in_val, '').strip()
#                           if key and value:
#                              specs[key] = value

#         return specs # Return potentially populated specs or empty dict

#     except Exception as e:
#         st.warning(f"Error extracting specifications: {e}")
#         return {}


# def extract_other_product_info(soup):
#     """Extracts Price, Color, and potentially a single review summary."""
#     if not soup: return {"price": "N/A", "colour": "N/A", "review_summary": "N/A"}
#     info = {}
#     try:
#         # --- Price ---
#         price_element = soup.select_one('span.a-price span[aria-hidden="true"]') # More robust price selector
#         if not price_element:
#              price_element = soup.select_one('span.a-offscreen') # Alternative selector often used
#         if not price_element:
#             price_element = soup.find("span", id="priceblock_ourprice")
#         if not price_element:
#             price_element = soup.find("span", id="priceblock_dealprice")

#         info["price"] = price_element.get_text(strip=True) if price_element else "Price not found"

#         # --- Colour ---
#         colour = "Colour not found"
#         # Try finding the selected variation
#         colour_swatch = soup.select_one('div#variation_color_name span.selection')
#         if colour_swatch:
#             colour = colour_swatch.get_text(strip=True)
#         else:
#             # Fallback to searching list items or tables
#             details_container = soup.find('div', id='detailBullets_feature_div') or soup.find('div', id='productDetails_feature_div')
#             if details_container:
#                 list_items = details_container.find_all('li')
#                 for item in list_items:
#                      text = item.get_text(strip=True)
#                      if text.lower().startswith("color:") or text.lower().startswith("colour:"):
#                           parts = text.split(":", 1)
#                           if len(parts) > 1:
#                               colour = parts[1].strip()
#                               break
#             # Fallback: check specification table too
#             if colour == "Colour not found":
#                  specs = extract_product_specifications(soup) # Reuse function
#                  for key, value in specs.items():
#                       if key.lower() == 'color' or key.lower() == 'colour':
#                            colour = value
#                            break
#         info["colour"] = colour

#         # --- Single Review Summary (from original script's logic) ---
#         review_summary = "Summary not found"
#         summary_element = soup.find('span', {'data-hook': 'review-body'})
#         if not summary_element:
#             # Backup: Look for a top review title
#              review_title_link = soup.find('a', {'data-hook': 'review-title'})
#              if review_title_link:
#                   review_title_span = review_title_link.find('span', recursive=False) # Find immediate span child
#                   if review_title_span:
#                       review_summary = review_title_span.get_text(strip=True)
#         else:
#             review_summary = summary_element.get_text(strip=True, limit=300) # Limit length

#         info["review_summary"] = review_summary

#         return info

#     except Exception as e:
#         st.warning(f"Error extracting price/colour/summary: {e}")
#         return {"price": "Error", "colour": "Error", "review_summary": "Error"}


# def get_amazon_ratings_from_soup(soup):
#     """
#     Extracts detailed rating info (overall, count, percentages) from a BeautifulSoup object.
#     """
#     if not soup:
#         return None

#     ratings_data = {
#         'overall_rating': None,
#         'total_ratings_count': None,
#         'star_percentages': {} # To store { '5': 52, '4': 25, ... } (Using numbers as keys)
#     }

#     try:
#         # --- 1. Extract Overall Rating ---
#         rating_text = None
#         # Primary: data-hook approach
#         rating_icon_span = soup.find('i', {'data-hook': 'average-star-rating'})
#         if rating_icon_span:
#             rating_text_span = rating_icon_span.find('span', class_='a-icon-alt')
#             if rating_text_span:
#                 rating_text = rating_text_span.text.strip()
#         # Fallback: Text directly in span
#         if not rating_text:
#             rating_span_alt = soup.find('span', {'data-hook': 'rating-out-of-text'})
#             if rating_span_alt:
#                 rating_text = rating_span_alt.text.strip()
#         # Fallback: Older structure maybe
#         if not rating_text:
#              rating_element = soup.select_one('span[data-asin-review-star-rating] span.a-icon-alt')
#              if rating_element:
#                   rating_text = rating_element.get_text(strip=True)


#         if rating_text:
#             match = re.search(r'([\d.]+)\s+out\s+of\s+5', rating_text)
#             if match:
#                 ratings_data['overall_rating'] = float(match.group(1))
#                 print(f"DEBUG: Found overall rating: {ratings_data['overall_rating']}") # Keep print for debugging
#         else:
#             print("DEBUG: Could not find overall rating element.")

#         # --- 2. Extract Total Ratings Count ---
#         count_element = soup.find('span', {'data-hook': 'total-review-count'})
#         if count_element:
#             count_text_match = re.search(r'([\d,]+)', count_element.text.strip()) # Simpler regex, just get number
#             if count_text_match:
#                 count_text = count_text_match.group(1).replace(',', '')
#                 if count_text.isdigit():
#                     ratings_data['total_ratings_count'] = int(count_text)
#                     print(f"DEBUG: Found total ratings count: {ratings_data['total_ratings_count']}")
#         else:
#              print("DEBUG: Could not find total ratings count element.")

#         # --- 3. Extract Star Rating Percentages ---
#         print("DEBUG: Attempting to extract star percentages...")

#         # Primary method: Find links with aria-labels
#         percentage_links = soup.find_all('a', {'aria-label': re.compile(r'\d+\s*percent of reviews have \d+ stars?', re.IGNORECASE)})
#         if percentage_links:
#             print(f"DEBUG: Found {len(percentage_links)} links with aria-label for percentages.")
#             for link in percentage_links:
#                 aria_label_text = link.get('aria-label', '').strip()
#                 star_match = re.search(r'have\s+(\d+)\s+stars?', aria_label_text, re.IGNORECASE)
#                 percent_match = re.search(r'^(\d+)\s*percent', aria_label_text, re.IGNORECASE)
#                 if star_match and percent_match:
#                     star_level = int(star_match.group(1))
#                     percentage = int(percent_match.group(1))
#                     ratings_data['star_percentages'][star_level] = percentage
#                     print(f"DEBUG: Found percentage via aria-label: {star_level} star = {percentage}%")

#         # Fallback method: Look for table rows or specific list items/links
#         if not ratings_data['star_percentages']:
#             print("DEBUG: Did not find percentage links via aria-label. Trying fallback selectors...")
#             # Try common table row selector
#             histogram_rows = soup.select('table#histogramTable tr.a-histogram-row')
#             if not histogram_rows:
#                  # Try selector from user's original HTML (more specific)
#                  histogram_rows = soup.select('ul[class*="_histogram"] > li span.a-list-item > a[class*="_histogram-row-container"]')

#             if histogram_rows:
#                  print(f"DEBUG: Found {len(histogram_rows)} potential percentage rows using fallback selectors.")
#                  for row in histogram_rows:
#                      # Find star level text (e.g., "5 star")
#                      star_text_element = row.find(['span', 'a'], class_='a-size-base', string=re.compile(r'\d+\s+star'))
#                      # Find percentage text (e.g., "52%") - often in a right-aligned element
#                      percentage_text_element = row.find('span', class_='a-text-right')
#                      if not percentage_text_element: # Another common pattern
#                           percentage_link = row.find('a', class_='a-link-normal', title=re.compile(r'\d+%'))
#                           if percentage_link:
#                                percentage_text_element = percentage_link # Use the link itself if it has the % title


#                      if star_text_element and percentage_text_element:
#                          star_text = star_text_element.text.strip()
#                          percentage_text = percentage_text_element.text.strip()

#                          star_match = re.search(r'(\d+)\s+star', star_text, re.IGNORECASE)
#                          # Percentage might be in text OR in title attribute
#                          percent_match = re.search(r'(\d+)%', percentage_text)
#                          if not percent_match and hasattr(percentage_text_element, 'title'):
#                               percent_match = re.search(r'(\d+)%', percentage_text_element.get('title',''))


#                          if star_match and percent_match:
#                              star_level = int(star_match.group(1))
#                              percentage = int(percent_match.group(1))
#                              ratings_data['star_percentages'][star_level] = percentage
#                              print(f"DEBUG: Found percentage via fallback: {star_level} star = {percentage}%")
#                      else:
#                           print(f"DEBUG: Could not parse fallback row content.")
#             else:
#                  print("DEBUG: Could not find percentage rows using fallback selectors either.")

#         # Final check and return
#         if ratings_data['overall_rating'] is None and ratings_data['total_ratings_count'] is None and not ratings_data['star_percentages']:
#             print("DEBUG: Failed to extract any rating data.")
#             st.warning("Could not extract detailed rating information.")
#             return None
#         elif not ratings_data['star_percentages']:
#              print("DEBUG: Failed to get star percentages.")
#              st.warning("Extracted overall rating/count, but couldn't find star percentages breakdown.")

#         # Sort percentages by star (descending)
#         ratings_data['star_percentages'] = dict(sorted(ratings_data['star_percentages'].items(), reverse=True))
#         return ratings_data

#     except Exception as e:
#         print(f"Error during rating extraction: {e}") # Keep print for debugging
#         st.warning(f"An error occurred while extracting ratings: {e}")
#         return None


# # --- Gemini API Integration ---
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
#     """Uses Gemini to answer user queries based on extracted product info."""
#     if not query:
#         return "Please enter a question."
#     try:
#         prompt = (
#             f"Based *only* on the following product information, answer the user's query.\n"
#             f"Product Information:\n{product_info_context}\n\n"
#             f"User Query: {query}\n\n"
#             f"Answer:"
#         )
#         response = model.generate_content(prompt)
#         return response.text.strip() if response.text else "Sorry, I couldn't generate a response based on the available data."
#     except Exception as e:
#         st.error(f"Gemini Error (Query): {e}")
#         return f"Error getting answer: {str(e)}"

# # --- Text-to-Speech Function ---
# def text_to_speech(text, filename="output.mp3"):
#     """Generates and plays audio from text using gTTS."""
#     if not text:
#         st.warning("No text provided for speech synthesis.")
#         return
#     try:
#         tts = gTTS(text=text, lang='en', slow=False) # slow=False for normal speed
#         # Use a temporary file to avoid permission issues
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
#             temp_filename = fp.name
#             tts.save(temp_filename)

#         # Play the audio
#         audio_file = open(temp_filename, "rb")
#         audio_bytes = audio_file.read()
#         st.audio(audio_bytes, format='audio/mp3')
#         audio_file.close() # Close the file handle

#         # Clean up the temporary file
#         os.remove(temp_filename)

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
#     labels = [f"{i} Star{'s' if i > 1 else ''}" for i in range(5, 0, -1)] # 5 Stars, 4 Stars...
#     sizes = [star_percentages.get(i, 0) for i in range(5, 0, -1)] # Get percentage or default to 0

#     # Check if we actually have any data to plot
#     if sum(sizes) == 0:
#         st.info("Rating distribution data contains only zero percentages.")
#         return

#     # Define colors (can customize)
#     colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336'] # Green to Red gradient

#     try:
#         fig, ax = plt.subplots(figsize=(7, 4)) # Adjust figure size if needed
#         bars = ax.bar(labels, sizes, color=colors)

#         # Add percentage labels on top of bars
#         ax.bar_label(bars, fmt='%d%%', padding=3)

#         ax.set_ylabel('Percentage of Total Ratings')
#         ax.set_title('Customer Rating Distribution')
#         ax.set_ylim(0, 105) # Set y-limit slightly above 100 for padding
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
#     if not (url.startswith("http://") or url.startswith("https://")) or "amazon." not in url or "/dp/" not in url:
#          st.error("Invalid Amazon product URL format. Please use a URL like 'https://www.amazon.com/dp/ASIN'.")
#     else:
#         with st.spinner("Fetching and analyzing product data... Please wait."):
#             soup = html_code(url)
#             if soup:
#                 # --- Perform all extractions ---
#                 st.session_state.product_name = extract_product_details(soup)
#                 st.session_state.ratings_info = get_amazon_ratings_from_soup(soup) # Detailed ratings
#                 st.session_state.other_info = extract_other_product_info(soup) # Price, color, summary
#                 st.session_state.product_specs = extract_product_specifications(soup)

#                 # --- Generate Description Score ---
#                 description_string = (
#                     f"Product Name: {st.session_state.product_name}. "
#                     f"Price: {st.session_state.other_info.get('price', 'N/A')}. "
#                     f"Colour: {st.session_state.other_info.get('colour', 'N/A')}."
#                     # Add key specs if available? Could make prompt long.
#                 )
#                 st.session_state.description_score = get_description_score(description_string)

#                 # --- Mark data as loaded ---
#                 st.session_state.product_data_loaded = True
#                 st.success("✅ Analysis complete!")

#             else:
#                 st.error("Failed to retrieve or parse webpage. Please check the URL or try again later.")
#                 st.session_state.product_data_loaded = False # Reset flag on failure
# # Clear data if URL is cleared
# elif not url and 'product_data_loaded' in st.session_state:
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
#         if st.session_state.get('ratings_info'):
#             overall_rating = st.session_state['ratings_info'].get('overall_rating', 'N/A')
#             total_ratings = st.session_state['ratings_info'].get('total_ratings_count', 'N/A')
#             if isinstance(total_ratings, int):
#                 total_ratings = f"{total_ratings:,}" # Format with comma

#             st.metric(label="Average Rating", value=f"{overall_rating} / 5 Stars" if isinstance(overall_rating, (float, int)) else overall_rating,
#                       delta=f"{total_ratings} Global Ratings" if total_ratings != 'N/A' else None)

#             # --- Display Rating Bar Chart ---
#             display_rating_bar_chart(st.session_state['ratings_info'].get('star_percentages'))
#         else:
#             st.info("Detailed rating information could not be extracted.")

#         # --- Display Review Summary Text ---
#         review_summary = st.session_state.get('other_info', {}).get('review_summary', 'N/A')
#         if review_summary and review_summary not in ["Summary not found", "N/A", "Error"]:
#              st.subheader("📝 Sample Review Snippet")
#              st.caption("(This is often from a top or recent review)")
#              st.info(f"_{review_summary}_")


#         # --- Text-to-Speech Button ---
#         st.subheader("🔊 Audio Summary")
#         if st.button("Read Rating & Snippet"):
#              tts_text = ""
#              if st.session_state.get('ratings_info') and st.session_state['ratings_info'].get('overall_rating'):
#                  tts_text += f"The average rating is {st.session_state['ratings_info']['overall_rating']} out of 5 stars, based on {st.session_state['ratings_info'].get('total_ratings_count', 'multiple')} global ratings. "
#              else:
#                   tts_text += "Rating information unavailable. "

#              if review_summary and review_summary not in ["Summary not found", "N/A", "Error"]:
#                  tts_text += f"A review snippet says: {review_summary}"
#              else:
#                  tts_text += "No review snippet available."

#              text_to_speech(tts_text)


#         # --- User Query Section ---
#         st.subheader("❓ Ask Gemini about this Product")
#         st.caption("Based on extracted data (Name, Price, Color, Specs)")
#         user_query = st.text_input("Your question:", placeholder="e.g., What material is it made of? Is it waterproof?")

#         if st.button("💬 Get Answer") and user_query:
#             # Prepare context for Gemini
#             product_info_context = (
#                 f"Product Name: {st.session_state.get('product_name', 'N/A')}\n"
#                 f"Price: {st.session_state.get('other_info', {}).get('price', 'N/A')}\n"
#                 f"Colour: {st.session_state.get('other_info', {}).get('colour', 'N/A')}\n"
#                 f"Specifications: {json.dumps(st.session_state.get('product_specs', {}), indent=2)}\n" # Format specs nicely
#                  # Removed overall rating from context as query is about specs/features usually
#             )
#             with st.spinner("Asking Gemini..."):
#                 query_response = get_query_response(user_query, product_info_context)
#                 st.markdown("**Gemini's Response:**")
#                 st.info(query_response) # Use info box for response

#     with col2:
#         st.header("📦 Product Info")
#         st.markdown("---")
#         st.write(f"**Name:** {st.session_state.get('product_name', 'N/A')}")
#         st.write(f"**Price:** {st.session_state.get('other_info', {}).get('price', 'N/A')}")
#         st.write(f"**Colour:** {st.session_state.get('other_info', {}).get('colour', 'N/A')}")

#         st.subheader("📝 Description Score")
#         st.write(f"**Gemini Score & Reason:**")
#         st.info(f"{st.session_state.get('description_score', 'N/A')}") # Use info box

#         st.subheader("⚙️ Specifications")
#         specs = st.session_state.get('product_specs', {})
#         if isinstance(specs, dict) and specs:
#             # Use an expander for potentially long spec lists
#             with st.expander("View Specifications", expanded=False):
#                  for key, value in specs.items():
#                      st.write(f"**{key}:** {value}")
#         elif isinstance(specs, str): # Handle case where specs extraction returned string error
#              st.write(specs)
#         else:
#             st.write("No specifications found or extracted.")

# else:
#     # Show instructions if no analysis has run yet
#     if not url:
#         st.info("☝️ Enter an Amazon product URL above and click 'Analyze Product'.")

# # Add a footer (optional)
# st.markdown("---")
# st.caption("Amazon Product Analyzer | Uses Web Scraping & Google Gemini | Scraped data accuracy depends on Amazon page structure.")










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
import time # To potentially add delays if needed

# --- Load environment variables ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Configure Gemini ---
# Check if API key is loaded
if not GEMINI_API_KEY:
    st.error("🔴 GEMINI_API_KEY not found. Please set it in your .env file.")
    st.stop() # Stop execution if key is missing

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
         model_name='models/gemini-1.5-flash', # Or use 'gemini-pro'
        generation_config={
            "temperature": 0.4,
            "max_output_tokens": 800,
            "top_p": 0.9,
            "top_k": 40
        },
        safety_settings=[
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ],
        system_instruction="You are a helpful assistant that analyzes Amazon product data and answers user questions based on the provided information."
    )
except Exception as e:
    st.error(f"🔴 Error configuring Gemini: {e}")
    st.stop()


# --- Define headers to mimic a real browser request ---
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'), # More recent User Agent
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    # Sometimes needed:
    # 'Referer': 'https://www.google.com/',
    # 'Sec-Fetch-Dest': 'document',
    # 'Sec-Fetch-Mode': 'navigate',
    # 'Sec-Fetch-Site': 'cross-site', # or 'same-origin' depending on context
    # 'Sec-Fetch-User': '?1',
    # 'TE': 'trailers',
}

# --- Web Scraping Helper Functions ---
def getdata(url):
    """Fetches HTML content from a URL."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=25) # Slightly longer timeout
        r.raise_for_status() # Check for HTTP errors
        # Simple check for CAPTCHA or block pages
        if "api-services-support@amazon.com" in r.text or "captcha" in r.text.lower():
             st.error("Amazon is blocking the request (CAPTCHA or block page detected). Try again later or use a different IP/proxy.")
             return None
        return r.text
    except requests.exceptions.Timeout:
        st.warning(f"Request timed out for {url}")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Error fetching {url}: {e.response.status_code} {e.response.reason}")
        return None
    except requests.exceptions.RequestException as e:
        st.warning(f"Network Error fetching {url}: {e}")
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

# --- Combined Extraction Functions ---

def extract_product_details(soup):
    """Extracts Product Title."""
    if not soup: return "Product name not found"
    try:
        title_element = soup.find('span', id='productTitle')
        product_name = title_element.get_text(strip=True) if title_element else "Product name not found"
        return product_name
    except Exception:
        return "Product name not found"

def extract_product_specifications(soup):
    """Extracts Product Specifications from tables."""
    if not soup: return {}
    specs = {}
    try:
        # Prioritize the technical details table
        spec_table = soup.find("table", id="productDetails_techSpec_section_1")

        # Fallback to detail bullets table
        if not spec_table:
            spec_table = soup.find("table", id="productDetails_detailBullets_sections1")

        # Fallback: Generic product details table class
        if not spec_table:
            spec_table = soup.find('table', id='productDetails_productDetails_table')

        # Fallback: Class-based search (less reliable)
        if not spec_table:
             spec_table = soup.find('table', class_='a-keyvalue') # Common class for specs

        if spec_table:
            rows = spec_table.find_all("tr")
            for row in rows:
                header_cell = row.find(["th", "td"], class_=re.compile(r'prodDetSectionEntry|a-span3|a-text-bold')) # Find header robustly
                value_cell = row.find("td", class_=re.compile(r'prodDetAttrValue|a-span9')) # Find value robustly

                if header_cell and value_cell : # Basic case
                    key = header_cell.get_text(strip=True).replace(':','').strip()
                    value = value_cell.get_text(strip=True).replace('\n', ' ').replace('\u200e', '').replace('\u200f', '').strip() # Clean value
                    if key and value and key.lower() != 'customer reviews': # Exclude rating row if caught
                         specs[key] = value
                elif header_cell and not value_cell: # Case where value might be next sibling td
                     next_td = header_cell.find_next_sibling('td')
                     if next_td:
                          key = header_cell.get_text(strip=True).replace(':','').strip()
                          value = next_td.get_text(strip=True).replace('\n', ' ').replace('\u200e', '').replace('\u200f', '').strip()
                          if key and value and key.lower() != 'customer reviews':
                               specs[key] = value

            if specs: return specs # Return if found via tables


        # Fallback: Look for detail bullet points list *if table fails*
        print("DEBUG: Table methods failed for specs, trying detail bullets list...")
        detail_bullets_div = soup.find('div', id='detailBullets_feature_div')
        if detail_bullets_div:
            list_items = detail_bullets_div.find_all('li')
            for item in list_items:
                text_content = item.get_text(strip=True)
                if ':' in text_content:
                    parts = text_content.split(':', 1)
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if key and value and key.lower() != 'customer reviews': # Exclude rating row if caught
                         specs[key] = value
        return specs

    except Exception as e:
        st.warning(f"Error extracting specifications: {e}")
        return {}


def extract_other_product_info(soup):
    """Extracts Price, Color, and potentially a single review summary."""
    if not soup: return {"price": "N/A", "colour": "N/A", "review_summary": "N/A"}
    info = {"price": "Price not found", "colour": "Colour not found", "review_summary": "Summary not found"}
    try:
        # --- Price ---
        # Most reliable: Look for 'a-offscreen' which often hides the price for screen readers
        price_element = soup.select_one('span.a-price span.a-offscreen')
        if price_element:
            info["price"] = price_element.get_text(strip=True)
            print(f"DEBUG: Price found via .a-offscreen: {info['price']}")
        else:
            # Fallback: Look for price elements within common price blocks
            price_block = soup.select_one('#corePrice_feature_div, #price, #priceblock_ourprice, #priceblock_dealprice, #tp_price_block_total_price_ww')
            if price_block:
                # Try finding '.a-offscreen' within the block first
                price_element = price_block.select_one('span.a-offscreen')
                if price_element:
                     info["price"] = price_element.get_text(strip=True)
                     print(f"DEBUG: Price found via .a-offscreen within block: {info['price']}")
                else:
                     # Look for any span with a price format (less reliable)
                     price_span = price_block.find('span', string=re.compile(r'[$£€]\d+'))
                     if price_span:
                          info["price"] = price_span.get_text(strip=True)
                          print(f"DEBUG: Price found via regex string search: {info['price']}")
                     else: # Last resort: get text of the whole block
                           info["price"] = price_block.get_text(strip=True).splitlines()[0] # Take first line
                           print(f"DEBUG: Price found via block text: {info['price']}")

        # --- Colour ---
        colour = None
        # Try finding the selected variation label
        variation_label = soup.select_one('#variation_color_name .selection') # Check selected color swatch text
        if variation_label:
            colour = variation_label.get_text(strip=True)
            print(f"DEBUG: Color found via variation label: {colour}")
        else:
             # Fallback: Search specific spans within list items in detail bullets
             detail_bullets_div = soup.find('div', id='detailBullets_feature_div')
             if detail_bullets_div:
                 list_items = detail_bullets_div.find_all('li')
                 for item in list_items:
                      # Look for "Color: <value>" pattern
                      bold_span = item.find('span', class_='a-text-bold', string=re.compile(r'Colour?:\s*$')) # Matches 'Color:' or 'Colour:'
                      if bold_span:
                          value_span = bold_span.find_next_sibling('span')
                          if value_span:
                               colour = value_span.get_text(strip=True)
                               print(f"DEBUG: Color found via detail bullet list item: {colour}")
                               break # Found it
        # Fallback: Check extracted specifications
        if not colour or colour == "Colour not found":
            specs = extract_product_specifications(soup) # Reuse function
            for key, value in specs.items():
                if key.lower() == 'color' or key.lower() == 'colour':
                    colour = value
                    print(f"DEBUG: Color found via specifications table: {colour}")
                    break
        info["colour"] = colour if colour else "Colour not found"


        # --- Single Review Summary ---
        review_summary = "Summary not found"
        # Try data-hook first
        summary_element = soup.find('span', {'data-hook': 'review-body'})
        if summary_element:
             review_summary = summary_element.get_text(strip=True)
             print(f"DEBUG: Review summary found via data-hook='review-body'")
        else:
            # Fallback: Look for a top review title
             review_title_link = soup.find('a', {'data-hook': 'review-title'})
             if review_title_link:
                  review_title_span = review_title_link.find('span', recursive=False) # Find immediate span child
                  if review_title_span:
                      review_summary = review_title_span.get_text(strip=True)
                      print(f"DEBUG: Review summary found via data-hook='review-title'")

        # Truncate if found and necessary (removed 'limit' from get_text)
        # if review_summary != "Summary not found":
        #     review_summary = review_summary[:300] + "..." if len(review_summary) > 300 else review_summary

        info["review_summary"] = review_summary

        return info

    except Exception as e:
        st.warning(f"Error extracting price/colour/summary: {e}")
        # Return dictionary with error indicators
        return {"price": "Error extracting", "colour": "Error extracting", "review_summary": "Error extracting"}


def get_amazon_ratings_from_soup(soup):
    """
    Extracts detailed rating info (overall, count, percentages) from a BeautifulSoup object.
    """
    if not soup:
        return None

    ratings_data = {
        'overall_rating': None,
        'total_ratings_count': None,
        'star_percentages': {} # To store { 5: 52, 4: 25, ... } (Using integers as keys)
    }

    try:
        # --- 1. Extract Overall Rating ---
        rating_text = None
        # Strategy 1: Find dedicated rating summary block (often has data-hook)
        rating_summary_block = soup.find('div', {'data-hook': 'rating-summary'})
        if rating_summary_block:
            rating_span = rating_summary_block.find('span', {'data-hook': 'rating-out-of-text'})
            if rating_span:
                rating_text = rating_span.text.strip()
                print("DEBUG: Found rating text via data-hook='rating-out-of-text'")

        # Strategy 2: Find the star icon element and get its alt text
        if not rating_text:
            rating_icon_span = soup.find('i', {'data-hook': 'average-star-rating'})
            if rating_icon_span:
                rating_text_span = rating_icon_span.find('span', class_='a-icon-alt')
                if rating_text_span:
                    rating_text = rating_text_span.text.strip()
                    print("DEBUG: Found rating text via i[data-hook='average-star-rating'] > span")

        # Strategy 3: Find rating near the title (less common now)
        if not rating_text:
             title_group = soup.find('div', id='title_feature_div') # Or other container near title
             if title_group:
                  rating_span = title_group.select_one('#acrPopover span.a-icon-alt') # Common pattern near title
                  if rating_span:
                       rating_text = rating_span.text.strip()
                       print("DEBUG: Found rating text via #acrPopover near title")

        # Parse the found text
        if rating_text:
            match = re.search(r'([\d.]+)\s+out\s+of\s+5', rating_text)
            if match:
                ratings_data['overall_rating'] = float(match.group(1))
                print(f"DEBUG: Parsed overall rating: {ratings_data['overall_rating']}")
        else:
            print("DEBUG: Could not find overall rating text using multiple strategies.")

        # --- 2. Extract Total Ratings Count ---
        count_text = None
        # Strategy 1: data-hook='total-review-count'
        count_element = soup.find('span', {'data-hook': 'total-review-count'})
        if count_element:
            count_text = count_element.text.strip()
            print("DEBUG: Found total rating text via data-hook='total-review-count'")
        # Strategy 2: Look for text like "X,XXX ratings" near the stars
        if not count_text:
            if rating_summary_block: # Reuse block from rating search
                 count_span = rating_summary_block.find(string=re.compile(r'[\d,]+\s+(global\s+)?ratings?'))
                 if count_span:
                      count_text = count_span.strip()
                      print("DEBUG: Found total rating text via regex string search near rating")
            elif 'title_group' in locals() and title_group: # Or near title
                 count_span = title_group.find(string=re.compile(r'[\d,]+\s+(global\s+)?ratings?'))
                 if count_span:
                      count_text = count_span.strip()
                      print("DEBUG: Found total rating text via regex string search near title")


        # Parse the found text
        if count_text:
            count_text_match = re.search(r'([\d,]+)', count_text) # Just get number
            if count_text_match:
                cleaned_count = count_text_match.group(1).replace(',', '')
                if cleaned_count.isdigit():
                    ratings_data['total_ratings_count'] = int(cleaned_count)
                    print(f"DEBUG: Parsed total ratings count: {ratings_data['total_ratings_count']}")
        else:
             print("DEBUG: Could not find total ratings count text.")


        # --- 3. Extract Star Rating Percentages ---
        print("DEBUG: Attempting to extract star percentages...")

        # Find the container for the histogram (ID is best, class fallback)
        histogram_container = soup.find('div', id='histogramTable-react-wrapper') # React version
        if not histogram_container:
             histogram_container = soup.find('div', id='reviews-medley-histogram') # Another ID
        if not histogram_container:
             histogram_container = soup.find('table', id='histogramTable') # Old table ID
        if not histogram_container:
             histogram_container = soup.find('div', class_='cr-widget-desktop-review-histogram') # Class name

        if histogram_container:
             print(f"DEBUG: Found histogram container: {histogram_container.name}#{histogram_container.get('id')} or class {histogram_container.get('class')}")
             # Strategy 1: Find percentage rows using data-hook (Newer React Structure)
             percentage_rows = histogram_container.find_all('div', {'data-hook': 'histogram-row'})
             if percentage_rows:
                  print(f"DEBUG: Found {len(percentage_rows)} rows via data-hook='histogram-row'")
                  for row in percentage_rows:
                      star_label = row.find('span', {'data-hook': 'histogram-star-rating-text'})
                      percentage_label = row.find('span', {'data-hook': 'histogram-star-rating-percentage'})
                      if star_label and percentage_label:
                           star_match = re.search(r'(\d+)\s+star', star_label.text, re.IGNORECASE)
                           percent_match = re.search(r'(\d+)%', percentage_label.text)
                           if star_match and percent_match:
                                star_level = int(star_match.group(1))
                                percentage = int(percent_match.group(1))
                                ratings_data['star_percentages'][star_level] = percentage
                                print(f"DEBUG: Found percentage via data-hook row: {star_level} star = {percentage}%")

             # Strategy 2: Find links with aria-labels (Common structure)
             elif not ratings_data['star_percentages']: # Only try if previous failed
                 percentage_links = histogram_container.find_all('a', {'aria-label': re.compile(r'\d+\s*percent of reviews have \d+ stars?', re.IGNORECASE)})
                 if percentage_links:
                     print(f"DEBUG: Found {len(percentage_links)} links with aria-label for percentages.")
                     for link in percentage_links:
                         aria_label_text = link.get('aria-label', '').strip()
                         star_match = re.search(r'have\s+(\d+)\s+stars?', aria_label_text, re.IGNORECASE)
                         percent_match = re.search(r'^(\d+)\s*percent', aria_label_text, re.IGNORECASE)
                         if star_match and percent_match:
                             star_level = int(star_match.group(1))
                             percentage = int(percent_match.group(1))
                             ratings_data['star_percentages'][star_level] = percentage
                             print(f"DEBUG: Found percentage via aria-label: {star_level} star = {percentage}%")

             # Strategy 3: Fallback to table rows (Older structure)
             elif not ratings_data['star_percentages']:
                  histogram_rows = histogram_container.select('tr.a-histogram-row')
                  if histogram_rows:
                       print(f"DEBUG: Found {len(histogram_rows)} table rows via tr.a-histogram-row.")
                       for row in histogram_rows:
                           # Find star level text (e.g., "5 star")
                           star_text_element = row.find(['td','a'], class_='a-text-left') # Link or cell
                           percentage_text_element = row.find('td', class_='a-text-right') # Percentage cell

                           if star_text_element and percentage_text_element:
                               star_text = star_text_element.get_text(strip=True)
                               percentage_text = percentage_text_element.get_text(strip=True)

                               star_match = re.search(r'(\d+)\s+star', star_text, re.IGNORECASE)
                               percent_match = re.search(r'(\d+)%', percentage_text)

                               if star_match and percent_match:
                                   star_level = int(star_match.group(1))
                                   percentage = int(percent_match.group(1))
                                   ratings_data['star_percentages'][star_level] = percentage
                                   print(f"DEBUG: Found percentage via fallback table row: {star_level} star = {percentage}%")
                           else:
                                print("DEBUG: Could not parse fallback table row structure.")
        else:
             print("DEBUG: Could not find histogram container using common IDs/classes.")


        # Final check and return
        if ratings_data['overall_rating'] is None and ratings_data['total_ratings_count'] is None and not ratings_data['star_percentages']:
            print("DEBUG: Failed to extract any rating data.")
            st.warning("Could not extract detailed rating information.")
            return None
        elif not ratings_data['star_percentages']:
             print("DEBUG: Failed to get star percentages.")
             # Don't show warning if overall/count were found, just means no breakdown available
             if ratings_data['overall_rating'] is not None:
                  print("DEBUG: Overall rating/count found, but no percentage breakdown.")
             else:
                  st.warning("Extracted some rating info, but couldn't find star percentages breakdown.")


        # Sort percentages by star (descending) if found
        if ratings_data['star_percentages']:
             ratings_data['star_percentages'] = dict(sorted(ratings_data['star_percentages'].items(), reverse=True))
        return ratings_data

    except Exception as e:
        print(f"Error during rating extraction: {e}") # Keep print for debugging
        st.warning(f"An error occurred while extracting ratings: {e}")
        # Return partial data if possible
        if any(ratings_data.values()):
            return ratings_data
        return None


# --- Gemini API Integration ---
def get_description_score(product_name, price, colour):
    """Uses Gemini to score the product description based on available info."""
    context = f"Product Name: {product_name if product_name else 'N/A'}. "
    context += f"Price: {price if price and price not in ['Price not found', 'Error extracting'] else 'N/A'}. "
    context += f"Colour: {colour if colour and colour not in ['Colour not found', 'Error extracting'] else 'N/A'}."

    if context.count("N/A") >= 2: # Don't bother scoring if too much info is missing
        return "Insufficient product details (name/price/color) extracted to generate a meaningful description score."

    try:
        prompt = (f"Based *only* on the provided basic product details below, rate how complete these details are for a potential customer out of 100. "
                  f"Give a very short (1 sentence) reason focusing on what *basic* info (like price or color) is present or missing.\n\n"
                  f"Details:\n{context}\n\n"
                  f"Score and Reason:")
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "Error: Unable to score description (No response)"
    except Exception as e:
        st.error(f"Gemini Error (Scoring): {e}")
        return f"Error scoring description: {str(e)}"

def get_query_response(query, product_info_context):
    """Uses Gemini to answer user queries based on extracted product info."""
    if not query:
        return "Please enter a question."
    try:
        prompt = (
            f"Based *strictly* on the following product information extracted from an Amazon page, answer the user's query. "
            f"If the information is not present in the provided details, state that the information is not available in the extracted data.\n\n"
            f"--- Product Information Start ---\n{product_info_context}\n--- Product Information End ---\n\n"
            f"User Query: {query}\n\n"
            f"Answer:"
        )
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "Sorry, I couldn't generate a response based on the available data."
    except Exception as e:
        st.error(f"Gemini Error (Query): {e}")
        return f"Error getting answer: {str(e)}"

# --- Text-to-Speech Function ---
def text_to_speech(text, filename="output.mp3"):
    """Generates and plays audio from text using gTTS."""
    if not text or text.strip() == "":
        st.warning("No text provided for speech synthesis.")
        return
    try:
        tts = gTTS(text=text, lang='en', slow=False) # slow=False for normal speed
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_filename = fp.name
            tts.save(temp_filename)

        audio_file = open(temp_filename, "rb")
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format='audio/mp3')
        audio_file.close()

        os.remove(temp_filename) # Clean up immediately after reading

    except Exception as e:
        st.error(f"Error during text-to-speech: {e}")
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
             try: os.remove(temp_filename)
             except OSError: pass


# --- Display Bar Chart for Ratings (Dynamic) ---
def display_rating_bar_chart(star_percentages):
    """Displays a bar chart based on the dynamically scraped star percentages."""
    if not star_percentages or not isinstance(star_percentages, dict):
        st.info("Rating distribution data is not available to display the chart.")
        return

    # Prepare data for the chart, ensuring all 5 levels are present
    labels = [f"{i} Star{'s' if i > 1 else ''}" for i in range(5, 0, -1)] # 5 Stars, 4 Stars...
    sizes = [star_percentages.get(i, 0) for i in range(5, 0, -1)] # Get percentage or default to 0

    # Check if we actually have any non-zero data to plot
    if sum(sizes) == 0:
        st.info("Rating distribution data contains only zero percentages or could not be found.")
        return

    # Define colors
    colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336'] # Green to Red gradient

    try:
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.bar(labels, sizes, color=colors)
        ax.bar_label(bars, fmt='%d%%', padding=3)
        ax.set_ylabel('Percentage of Total Ratings')
        ax.set_title('Customer Rating Distribution')
        ax.set_ylim(0, max(105, max(sizes) + 10)) # Adjust ylim based on max value
        plt.xticks(rotation=0, ha='center')
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error generating rating chart: {e}")


# --- Streamlit Application Layout ---
st.set_page_config(layout="wide")
st.title("📢 Amazon Product Analyzer")

# --- Initialize Session State ---
if 'product_data_loaded' not in st.session_state:
    st.session_state.product_data_loaded = False

# User inputs the Amazon product URL
url = st.text_input("Enter the Amazon product URL:", placeholder="e.g., https://www.amazon.com/dp/ASIN_HERE", key="amazon_url_input")

# Add a submit button
submit_button = st.button("📊 Analyze Product")

# --- Main Analysis Logic ---
if submit_button and url:
    if not (url.startswith("http://") or url.startswith("https://")) or "amazon." not in url or ("/dp/" not in url and "/product/" not in url) :
         st.error("Invalid Amazon product URL format. Please use a URL containing '/dp/' or '/product/'.")
         st.session_state.product_data_loaded = False # Ensure flag is false
    else:
        with st.spinner("Fetching and analyzing product data... This may take a moment."):
            soup = html_code(url)
            if soup:
                # Perform all extractions
                st.session_state.product_name = extract_product_details(soup)
                st.session_state.ratings_info = get_amazon_ratings_from_soup(soup)
                st.session_state.other_info = extract_other_product_info(soup)
                st.session_state.product_specs = extract_product_specifications(soup)

                # Generate Description Score based on extracted basic info
                st.session_state.description_score = get_description_score(
                    st.session_state.product_name,
                    st.session_state.other_info.get('price'),
                    st.session_state.other_info.get('colour')
                )

                st.session_state.product_data_loaded = True
                st.success("✅ Analysis complete!")

            else:
                # Error message handled within getdata/html_code
                st.session_state.product_data_loaded = False # Reset flag on failure
# Clear data if URL is cleared manually AND analysis was done
elif not url and st.session_state.get('product_data_loaded', False):
     print("DEBUG: Clearing session state because URL is empty.")
     st.session_state.product_data_loaded = False
     keys_to_clear = ['product_name', 'ratings_info', 'other_info', 'product_specs', 'description_score']
     for key in keys_to_clear:
          if key in st.session_state:
               del st.session_state[key]


# --- Display Area (only shows if data is loaded) ---
if st.session_state.get('product_data_loaded', False):

    col1, col2 = st.columns([2, 1]) # Main content left, details right

    with col1:
        st.header(f"📊 Analysis Results for: {st.session_state.get('product_name', 'Product')}")
        st.markdown("---")

        # --- Display Rating Summary ---
        st.subheader("⭐ Customer Ratings")
        ratings_info = st.session_state.get('ratings_info')
        if ratings_info:
            overall_rating = ratings_info.get('overall_rating') # Might be None
            total_ratings = ratings_info.get('total_ratings_count') # Might be None

            rating_value_str = "N/A"
            if isinstance(overall_rating, (float, int)):
                 rating_value_str = f"{overall_rating:.1f} / 5 Stars" # Format to 1 decimal place

            total_ratings_str = None
            if isinstance(total_ratings, int):
                 total_ratings_str = f"{total_ratings:,} Global Ratings" # Format with comma

            st.metric(label="Average Rating", value=rating_value_str, delta=total_ratings_str)

            # Display Rating Bar Chart
            display_rating_bar_chart(ratings_info.get('star_percentages'))
        else:
            st.info("Detailed rating information (average, count, breakdown) could not be fully extracted.")

        # --- Display Review Summary Text ---
        review_summary = st.session_state.get('other_info', {}).get('review_summary', 'N/A')
        if review_summary and review_summary not in ["Summary not found", "N/A", "Error extracting"]:
             st.subheader("📝 Sample Review Snippet")
             st.caption("(This is often from a top or recent review title/body)")
             st.info(f"_{review_summary}_") # Use info box for visual separation

        # --- Text-to-Speech Button ---
        st.subheader("🔊 Audio Summary")
        if st.button("Read Rating & Snippet"):
             tts_text_parts = []
             if ratings_info and isinstance(overall_rating, (float, int)):
                  tts_text_parts.append(f"The average rating is {overall_rating:.1f} out of 5 stars")
                  if isinstance(total_ratings, int):
                       tts_text_parts[-1] += f", based on {total_ratings:,} global ratings."
                  else:
                       tts_text_parts[-1] += "."
             else:
                  tts_text_parts.append("Rating information unavailable.")

             if review_summary and review_summary not in ["Summary not found", "N/A", "Error extracting"]:
                  tts_text_parts.append(f"A review snippet says: {review_summary}")

             text_to_speech(" ".join(tts_text_parts))


        # --- User Query Section ---
        st.subheader("❓ Ask Gemini about this Product")
        st.caption("Based on extracted data (Name, Price, Color, Specs)")
        user_query = st.text_input("Your question:", placeholder="e.g., What material is it made of? What are the dimensions?", key="user_query_input")

        if st.button("💬 Get Answer") and user_query:
            # Prepare context for Gemini
            product_info_context = (
                f"Product Name: {st.session_state.get('product_name', 'N/A')}\n"
                f"Price: {st.session_state.get('other_info', {}).get('price', 'N/A')}\n"
                f"Colour: {st.session_state.get('other_info', {}).get('colour', 'N/A')}\n"
                # Only include specs if it's a non-empty dictionary
                f"Specifications: {json.dumps(st.session_state.get('product_specs'), indent=2) if isinstance(st.session_state.get('product_specs'), dict) and st.session_state.get('product_specs') else 'Not Available'}\n"
            )
            with st.spinner("Asking Gemini..."):
                query_response = get_query_response(user_query, product_info_context)
                st.markdown("**Gemini's Response:**")
                st.info(query_response) # Use info box

    with col2:
        st.header("📦 Product Info")
        st.markdown("---")
        st.write(f"**Name:** {st.session_state.get('product_name', 'N/A')}")
        st.write(f"**Price:** {st.session_state.get('other_info', {}).get('price', 'N/A')}")
        st.write(f"**Colour:** {st.session_state.get('other_info', {}).get('colour', 'N/A')}")

        st.subheader("📝 Description Score")
        st.caption("(Based on extracted Name/Price/Color)")
        st.info(f"{st.session_state.get('description_score', 'N/A')}") # Use info box

        st.subheader("⚙️ Specifications")
        specs = st.session_state.get('product_specs', {})
        if isinstance(specs, dict) and specs:
            with st.expander("View Specifications", expanded=False):
                 for key, value in specs.items():
                     st.write(f"**{key}:** {value}")
        elif isinstance(specs, str): # Handle case where specs extraction returned string error/message
             st.write(specs)
        else:
            st.write("No specifications found or extracted.")

else:
    # Show instructions if no analysis has run yet and URL is not entered
    if not url:
        st.info("☝️ Enter an Amazon product URL above and click 'Analyze Product'.")


# --- Footer ---
st.markdown("---")
st.caption("Amazon Product Analyzer | Uses Web Scraping & Google Gemini | Data accuracy depends on Amazon's current page structure and may vary.")