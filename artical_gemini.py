import requests
from bs4 import BeautifulSoup
import streamlit as st
import pyttsx3
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os
import google.generativeai as genai

# --- Load environment variables ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# --- Define headers to mimic a real browser request ---
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'),
    'Accept-Language': 'en-US, en;q=0.5'
}

# --- Data Fetching & Parsing Functions ---
def getdata(url):
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.text
    else:
        return None

def html_code(url):
    htmldata = getdata(url)
    if htmldata:
        soup = BeautifulSoup(htmldata, 'html.parser')
        return soup
    return None

# --- Extraction Functions ---
def extract_overall_review(soup):
    try:
        rating_element = soup.select_one("span[data-hook='rating-out-of-text']")
        overall_rating = rating_element.get_text(strip=True) if rating_element else "Rating not found"

        summary_element = soup.select_one("div[data-hook='cr-insights-widget-summary']")
        review_summary = summary_element.get_text(strip=True) if summary_element else "Summary not found"
        
        return overall_rating, review_summary
    except AttributeError:
        return "Overall review not found", "Summary not found"

def extract_product_details(soup):
    try:
        title_element = soup.find('span', id='productTitle')
        product_name = title_element.get_text(strip=True) if title_element else "Product name not found"
        return product_name
    except Exception:
        return "Product name not found"

def extract_product_specifications(soup):
    try:
        spec_table = soup.find("table", id="productDetails_techSpec_section_1")
        if not spec_table:
            spec_table = soup.find("table", id="productDetails_detailBullets_sections1")
        specs = {}
        if spec_table:
            rows = spec_table.find_all("tr")
            for row in rows:
                header_cell = row.find("th")
                value_cell = row.find("td")
                if header_cell and value_cell:
                    specs[header_cell.get_text(strip=True)] = value_cell.get_text(strip=True)
            return specs
        else:
            return {}
    except Exception:
        return {}

def extract_product_description(soup):
    try:
        product_name = extract_product_details(soup)
        
        price_element = soup.find("span", id="priceblock_ourprice")
        if not price_element:
            price_element = soup.find("span", id="priceblock_dealprice")
        product_price = price_element.get_text(strip=True) if price_element else "Price not found"
        
        colour = None
        details = soup.find_all("li")
        for detail in details:
            text = detail.get_text(strip=True)
            if "Color" in text or "Colour" in text:
                parts = text.split(":")
                if len(parts) > 1:
                    colour = parts[1].strip()
                    break
        if not colour:
            colour = "Colour not found"
        
        return {
            "product_name": product_name,
            "price": product_price,
            "colour": colour
        }
    except Exception:
        return {}

# --- Gemini API Integration for Description Scoring ---
def get_description_score(description):
    try:
        response = model.generate_content(f"Rate this product description out of 100 and give a short reason for the score: {description}")
        if response.text:
            return response.text
        else:
            return "Error: Unable to score description"
    except Exception as e:
        return f"Error: {str(e)}"

# --- Text-to-Speech Function ---
def text_to_speech(text):
    """
    Converts text to speech using pyttsx3
    """
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        st.error(f"Text-to-Speech Error: {e}")

# --- Display Bar Chart for Ratings ---
def display_rating_bar_chart():
    labels = ['5 Stars', '4 Stars', '3 Stars', '2 Stars', '1 Star']
    sizes = [60, 25, 10, 3, 2]
    colors = ['green', 'blue', 'orange', 'red', 'gray']
    
    fig, ax = plt.subplots()
    ax.bar(labels, sizes, color=colors)
    ax.set_ylabel('Percentage')
    ax.set_title('Rating Distribution')
    st.pyplot(fig)

# --- Streamlit Application Layout ---
st.title("📢 Amazon Product Review Summary")

# User inputs the Amazon product URL
url = st.text_input("Enter the Amazon product URL:", placeholder="https://www.amazon.com/Example-Product/dp/B08XXXX")

# Add a submit button with proper alignment
submit_button = st.button("✅ Submit")

if submit_button and url:
    soup = html_code(url)
    if soup:
        overall_rating, review_summary = extract_overall_review(soup)
        product_name = extract_product_details(soup)
        product_specs = extract_product_specifications(soup)
        product_description = extract_product_description(soup)

        description_string = (
            f"Product Name: {product_description['product_name']}. "
            f"Price: {product_description['price']}. "
            f"Colour: {product_description['colour']}."
        )
        description_score = get_description_score(description_string)

        # Store results in session state
        st.session_state['overall_rating'] = overall_rating
        st.session_state['review_summary'] = review_summary
        st.session_state['product_name'] = product_name
        st.session_state['product_specs'] = product_specs if product_specs else "Product specifications not found"
        st.session_state['product_description'] = product_description
        st.session_state['description_score'] = description_score
    else:
        st.error("Failed to retrieve webpage. Please check the URL.")

# --- Sidebar for Product Details and Specifications ---
if 'overall_rating' in st.session_state:
    st.sidebar.header("📦 Product Details")
    st.sidebar.write(f"**Name:** {st.session_state['product_name']}")
    st.sidebar.write(f"**Description Score:** {st.session_state.get('description_score', 'N/A')}")

    st.sidebar.header("⚙️ Product Specifications")
    if isinstance(st.session_state['product_specs'], dict) and st.session_state['product_specs']:
        for key, value in st.session_state['product_specs'].items():
            st.sidebar.write(f"**{key}:** {value}")
    else:
        st.sidebar.write("No specifications found.")

    # --- Main Content ---
    st.subheader("📊 Overall Review Summary")
    st.write(f"**Overall Rating:** {st.session_state['overall_rating']}")
    st.write(f"**Review Summary:** {st.session_state['review_summary']}")

    # --- Display Rating Bar Chart ---
    st.subheader("📊 Rating Distribution")
    display_rating_bar_chart()

    # --- Text-to-Speech Button ---
    if st.button("🔊 Read Overall Review"):
        text_to_speech(
            f"Overall Rating: {st.session_state['overall_rating']}. "
            f"Review Summary: {st.session_state['review_summary']}"
        )
