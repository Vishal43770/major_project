import requests
from bs4 import BeautifulSoup
import streamlit as st
import pyttsx3

# Define headers to mimic a real browser request
HEADERS = ({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Accept-Language': 'en-US, en;q=0.5'
})

# Function to get the HTML data
def getdata(url):
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.text
    else:
        return None

# Function to parse the HTML code
def html_code(url):
    htmldata = getdata(url)
    if htmldata:
        soup = BeautifulSoup(htmldata, 'html.parser')
        return soup
    return None

# Function to extract overall review rating and summary
def extract_overall_review(soup):
    try:
        # Extract overall star rating
        rating_element = soup.select_one("span[data-hook='rating-out-of-text']")
        overall_rating = rating_element.get_text(strip=True) if rating_element else "Rating not found"

        # Extract the review summary text
        summary_element = soup.select_one("div[data-hook='cr-insights-widget-summary']")
        review_summary = summary_element.get_text(strip=True) if summary_element else "Summary not found"

        return overall_rating, review_summary
    except AttributeError:
        return "Overall review not found", "Summary not found"

# Function to convert text to speech
def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# Streamlit application
st.title("Amazon Product Review Summary")
url = st.text_input("Enter the Amazon product URL:")

if url and 'overall_rating' not in st.session_state:
    soup = html_code(url)
    if soup:
        overall_rating, review_summary = extract_overall_review(soup)
        st.session_state['overall_rating'] = overall_rating
        st.session_state['review_summary'] = review_summary
    else:
        st.session_state['overall_rating'] = "Failed to retrieve webpage"
        st.session_state['review_summary'] = "Please check the URL or try again later."

if 'overall_rating' in st.session_state:
    st.subheader("Overall Review Summary")
    st.write(f"**Overall Rating:** {st.session_state['overall_rating']}")
    st.write(f"**Review Summary:** {st.session_state['review_summary']}")

    # Convert summary to speech
    if st.button("Read Summary Aloud"):
        text_to_speech(f"Overall Rating: {st.session_state['overall_rating']}. Review Summary: {st.session_state['review_summary']}")