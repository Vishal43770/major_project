import requests
from bs4 import BeautifulSoup
import streamlit as st
import pyttsx3
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os
import google.generativeai as genai
from gtts import gTTS
import tempfile

# --- Load environment variables ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
     model_name='models/gemini-1.5-flash', 
    generation_config={
        "temperature": 0.4,  # Controls randomness, 0 is deterministic
        "max_output_tokens": 800,  # Limits the length of the response
        "top_p": 0.9,  # Nucleus sampling
        "top_k": 40  # Limits to top-k tokens
    },
    safety_settings=[
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_LOW_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_LOW_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_LOW_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_LOW_AND_ABOVE"},
    ],
    system_instruction="You are a helpful assistant that answers questions based on product data extracted from Amazon pages."
)

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
        # Primary Attempt: Look for the "Average Customer Review" star rating
        rating_element = soup.select_one('span[data-asin-review-star-rating] span.a-icon-alt')
        if not rating_element:
            # Backup: Look for near product title
            rating_element = soup.select_one('span.a-icon-alt')
        
        overall_rating = rating_element.get_text(strip=True) if rating_element else "Rating not found"
        
        # Attempt to find a short summary text under reviews
        summary_element = soup.find('span', {'data-hook': 'review-body'})
        if not summary_element:
            # Backup: Any review title or top review highlight
            summary_element = soup.find('a', {'data-hook': 'review-title'})
        
        review_summary = summary_element.get_text(strip=True) if summary_element else "Summary not found"
        
        return overall_rating, review_summary
    except Exception as e:
        return f"Error extracting rating: {str(e)}", "Summary not found"


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
    tts = gTTS(text=text, lang='en')
    filename = "output.mp3"
    tts.save(filename)
    audio_file = open(filename, "rb")
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3')
    os.remove(filename)


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

# --- Gemini API for User Queries ---
def get_query_response(query, product_info):
    try:
        query_context = (
            f"Product Name: {product_info['product_name']}, "
            f"Price: {product_info['price']}, "
            f"Colour: {product_info['colour']}, "
            f"Specifications: {product_info['specs']}."
        )
        response = model.generate_content(f"Answer the following query based on the product data: {query_context}. Query: {query}")
        if response.text:
            return response.text
        else:
            return "No response generated."
    except Exception as e:
        return f"Error: {str(e)}"

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

    # --- User Query Section ---
    st.subheader("🤖 Ask Queries about the Product")
    user_query = st.text_input("Ask a question about the product:", placeholder="What is the price of the product?")

    if st.button("🔍 Get Answer") and user_query:
        product_info = {
            'product_name': st.session_state['product_name'],
            'price': st.session_state['product_description'].get('price', 'Price not found'),
            'colour': st.session_state['product_description'].get('colour', 'Colour not found'),
            'specs': st.session_state['product_specs']
        }
        query_response = get_query_response(user_query, product_info)
        st.write(f"💬 Response: {query_response}")
