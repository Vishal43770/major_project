import streamlit as st
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

# --- Helper Functions ---

def html_code(url):
    """Fetch and parse the HTML content of the given URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.RequestException as e:
        st.error(f"Error fetching the page: {e}")
        return None

def extract_product_details(soup):
    """Extract product name."""
    try:
        title = soup.find('span', {'id': 'productTitle'}).text.strip()
        return title
    except AttributeError:
        return "Product Title Not Found"

def extract_rating_counts(soup):
    """Extract dynamic rating distribution from Amazon page."""
    rating_counts = {'5': 0, '4': 0, '3': 0, '2': 0, '1': 0}
    try:
        table = soup.find('table', {'id': 'histogramTable'})
        if table:
            rows = table.find_all('tr')
            for row in rows:
                star = row.find('td', {'class': 'aok-nowrap'}).text.strip()[0]  # First character is rating
                count = row.find('td', {'class': 'a-text-right'}).text.strip()
                count = int(count.replace(',', ''))
                rating_counts[star] = count
        return rating_counts
    except Exception as e:
        st.warning(f"Warning extracting ratings: {e}")
        return rating_counts  # return default zero dict if error

def display_rating_bar_chart_dynamic(rating_counts):
    """Display a dynamic bar chart for rating distribution."""
    stars = list(rating_counts.keys())
    counts = list(rating_counts.values())

    fig, ax = plt.subplots()
    bars = ax.bar(stars, counts, color='skyblue', edgecolor='black')
    ax.set_xlabel('Star Rating')
    ax.set_ylabel('Number of Ratings')
    ax.set_title('Rating Distribution')

    for bar, count in zip(bars, counts):
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 2, str(count), ha='center', va='bottom')

    st.pyplot(fig)

# --- Streamlit App ---

st.title("🛒 Amazon Product Review Dashboard")

url = st.text_input("Enter the Amazon Product URL:")

if st.button("Submit") and url:
    soup = html_code(url)
    if soup:
        product_name = extract_product_details(soup)
        rating_counts = extract_rating_counts(soup)

        st.header(f"📦 {product_name}")

        st.subheader("⭐ Rating Distribution")
        display_rating_bar_chart_dynamic(rating_counts)

        st.success("✅ Fetched and Plotted Ratings Dynamically!")
    else:
        st.error("❌ Could not fetch the webpage. Please check the URL.")

