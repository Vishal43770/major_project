from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re

def get_ratings_data(url):
    # Set up Chrome options to run headless (no visible browser window)
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    # Automatically download and use the correct ChromeDriver version
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    
    driver.get(url)
    
    # Wait until the overall rating element is loaded
    try:
        overall_rating_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.a-icon-alt"))
        )
        overall_rating = overall_rating_element.text.strip()
    except Exception as e:
        overall_rating = "Overall rating not found"
    
    # Wait for the histogram table to load (it typically has the id 'histogramTable')
    try:
        histogram_table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "histogramTable"))
        )
        # Find each histogram row using the common class of its <a> element
        rows = histogram_table.find_elements(By.CSS_SELECTOR, "a.cr-ratings-histogram_style_histogram-row-container__V7o7i")
        ratings_breakdown = {}
        for row in rows:
            # The 'aria-label' contains percentage info (e.g., "52 percent of reviews have 5 stars")
            aria_label = row.get_attribute("aria-label")
            if aria_label:
                match = re.search(r"(\d+)\s*percent.*?(\d+)\s*star", aria_label, re.IGNORECASE)
                if match:
                    percent = match.group(1)
                    star = match.group(2)
                    ratings_breakdown[f"{star} star"] = f"{percent}%"
    except Exception as e:
        ratings_breakdown = "Ratings histogram not found"
    
    driver.quit()
    return overall_rating, ratings_breakdown

if __name__ == "__main__":
    url = input("Please enter the Amazon product URL: ").strip()
    overall_rating, ratings_breakdown = get_ratings_data(url)
    
    print("\nOverall Rating:")
    print(overall_rating)
    
    print("\nRatings Breakdown:")
    if isinstance(ratings_breakdown, dict):
        for star, percentage in ratings_breakdown.items():
            print(f"{star}: {percentage}")
    else:
        print(ratings_breakdown)