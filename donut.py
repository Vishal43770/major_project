# --- Imports ---
import requests
from bs4 import BeautifulSoup
import streamlit as st
import pyttsx3
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
import os
import google.generativeai as genai
from gtts import gTTS

# --- Load environment variables ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Validate API Key
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found. Please check your .env file!")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name='models/gemini-1.5-flash',
    generation_config={
        "temperature": 0.7,
        "max_output_tokens": 500,
        "top_p": 0.9,
        "top_k": 40
    },
    safety_settings=[
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_LOW_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_LOW_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_LOW_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_LOW_AND_ABOVE"},
    ],
    system_instruction="You are a helpful assistant that answers questions in simple and short sentences, structured in a way that each piece of information is presented on a separate line."
)

# --- Headers for Amazon ---
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'),
    'Accept-Language': 'en-US,en;q=0.5'
}

# --- Functions ---

def getdata(url):
    try:
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            return r.text
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching URL: {e}")
        return None

def html_code(url):
    html = getdata(url)
    if html:
        return BeautifulSoup(html, 'html.parser')
    return None

def extract_overall_review(soup):
    try:
        rating_element = soup.select_one("span[data-hook='rating-out-of-text']")
        summary_element = soup.select_one("div[data-hook='cr-insights-widget-summary']")
        overall_rating = rating_element.get_text(strip=True) if rating_element else "Rating not found"
        review_summary = summary_element.get_text(strip=True) if summary_element else "Summary not found"
        return overall_rating, review_summary
    except Exception:
        return "Overall review not found", "Summary not found"

def extract_product_details(soup):
    try:
        title_element = soup.find('span', id='productTitle')
        return title_element.get_text(strip=True) if title_element else "Product name not found"
    except Exception:
        return "Product name not found"

def extract_product_specifications(soup):
    try:
        specs = {}
        spec_table = soup.find("table", id="productDetails_techSpec_section_1") \
                    or soup.find("table", id="productDetails_detailBullets_sections1")
        if spec_table:
            rows = spec_table.find_all("tr")
            for row in rows:
                header = row.find("th")
                value = row.find("td")
                if header and value:
                    specs[header.get_text(strip=True)] = value.get_text(strip=True)
        return specs
    except Exception:
        return {}

def extract_product_description(soup):
    try:
        product_name = extract_product_details(soup)
        price_element = soup.find("span", id="priceblock_ourprice") or soup.find("span", id="priceblock_dealprice")
        product_price = price_element.get_text(strip=True) if price_element else "Price not found"
        colour = "Colour not found"
        for li in soup.find_all("li"):
            text = li.get_text(strip=True)
            if "Color" in text or "Colour" in text:
                parts = text.split(":")
                if len(parts) > 1:
                    colour = parts[1].strip()
                    break
        return {"product_name": product_name, "price": product_price, "colour": colour}
    except Exception:
        return {}

def display_overall_rating_donut(overall_rating_text):
    try:
        rating = float(overall_rating_text.split()[0])
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(
            [rating, 5-rating],
            labels=['Rating', ''],
            startangle=90,
            colors=['#00cc66', '#e0e0e0'],
            wedgeprops={'width': 0.3, 'edgecolor': 'white'}
        )
        ax.text(0, 0, f"{rating}/5", ha='center', va='center', fontsize=14, weight='bold')
        ax.set_title('Overall Rating', fontsize=12)
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error displaying chart: {e}")

def get_description_score(description):
    try:
        response = model.generate_content(
            f"Rate this product description out of 100 and explain briefly: {description}")
        return response.text or "Error: Empty response"
    except Exception as e:
        return f"Error generating description score: {str(e)}"

def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    filename = "output.mp3"
    tts.save(filename)
    audio_file = open(filename, "rb")
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3')
    os.remove(filename)


def get_query_response(query, product_info):
    try:
        context = (
            f"Product Name: {product_info['product_name']}, "
            f"Price: {product_info['price']}, "
            f"Colour: {product_info['colour']}, "
            f"Specifications: {product_info['specs']}."
        )
        response = model.generate_content(
            f"Answer the following query based on the product data: {context}. Query: {query}")
        return response.text or "Error: Empty chatbot response"
    except Exception as e:
        return f"Error generating chatbot response: {str(e)}"

# --- Streamlit UI ---

st.title("📢 Amazon Product Review Analyzer")

url = st.text_input("Enter Amazon product URL:", placeholder="https://www.amazon.com/Example-Product/dp/B08XXXX")
if st.button("✅ Submit") and url:
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

        st.session_state.update({
            'overall_rating': overall_rating,
            'review_summary': review_summary,
            'product_name': product_name,
            'product_specs': product_specs,
            'product_description': product_description,
            'description_score': description_score
        })
    else:
        st.error("Failed to fetch product page. Please verify the URL.")

if 'overall_rating' in st.session_state:
    st.sidebar.header("📦 Product Info")
    st.sidebar.write(f"**Name:** {st.session_state['product_name']}")
    st.sidebar.write(f"**Description Score:** {st.session_state['description_score']}")

    st.sidebar.header("⚙ Specifications")
    specs = st.session_state.get('product_specs', {})
    if specs:
        for k, v in specs.items():
            st.sidebar.write(f"{k}: {v}")
    else:
        st.sidebar.write("No specifications found.")

    st.subheader("📊 Overall Review")
    st.write(f"**Rating:** {st.session_state['overall_rating']}")
    st.write(f"**Summary:** {st.session_state['review_summary']}")

    st.subheader("📈 Visual Rating")
    display_overall_rating_donut(st.session_state['overall_rating'])

    if st.button("🔊 Listen to Review"):
        review_text = (
            f"Overall Rating: {st.session_state['overall_rating']}. "
            f"Review Summary: {st.session_state['review_summary']}."
        )
        text_to_speech(review_text)

    st.subheader("🤖 Product Query Chatbot")
    user_query = st.text_input("Ask about the product:", placeholder="What is the battery life?")
    if st.button("🔍 Get Answer") and user_query:
        product_info = {
            'product_name': st.session_state['product_name'],
            'price': st.session_state['product_description']['price'],
            'colour': st.session_state['product_description']['colour'],
            'specs': st.session_state['product_specs']
        }
        response = get_query_response(user_query, product_info)
        st.success(response)




#https://www.amazon.in/BSB-Cotton-Football-Printed-Bedsheets/dp/B08T7LQR4F/?_encoding=UTF8&ref_=pd_hp_d_btf_gcx_gw_per_1

# coloue shape sixe design and name of the product   battery life 