# Amazon Product Review Summary and Q&A Tool

## Overview

This project is a Python-based tool that scrapes Amazon product pages to extract and summarize product information, including:

*   **Overall Review Summary:** Retrieves the overall star rating and a summary of customer reviews.
*   **Product Details:** Extracts the product name, price, and color.
*   **Product Specifications:** Gathers technical specifications from the product page.
*   **Description Scoring:** Uses the Gemini API to rate the quality of the product description.
*   **Rating Distribution:** Displays a bar chart showing the distribution of star ratings.
*   **Text-to-Speech:** Provides an option to read the overall review summary aloud.
* **Q&A:** Allow the user to ask question about the product.

The project utilizes web scraping, natural language processing (NLP), and the Gemini API to provide a comprehensive overview of Amazon products.

## Features

*   **Web Scraping:** Uses `requests` and `BeautifulSoup` to scrape Amazon product pages.
*   **Data Extraction:** Extracts key product information, including ratings, reviews, specifications, and descriptions.
*   **Gemini API Integration:** Leverages the Gemini API for:
    *   Scoring the quality of product descriptions.
    *   Answering user queries about the product.
*   **Streamlit Interface:** Provides an interactive web application using the Streamlit framework.
*   **Text-to-Speech:** Uses `pyttsx3` to convert text to speech.
*   **Data Visualization:** Uses `matplotlib` to display a bar chart of the rating distribution.
* **Q&A:** Uses the gemini API to answer the user question.

## Files

*   **`amazon.py`:** Contains the core logic for scraping Amazon product pages and extracting basic review information.
*   **`artical_gemini.py`:** Extends `amazon.py` by adding Gemini API integration for description scoring and more detailed product information extraction.
*   **`reviewqna.py`:** Extends `artical_gemini.py` by adding Gemini API integration for answering user queries about the product.
*   **`.env`:** Stores the Gemini API key (should not be committed to version control).
*   **`.gitignore`:** Specifies files and directories that should be ignored by Git.
*   **`requirements.txt`:** Lists the project's Python dependencies.
*   `.vscode/`: Contains the setting for the vs code.

## Dependencies

*   `requests`
*   `beautifulsoup4`
*   `streamlit`
*   `pyttsx3`
*   `matplotlib`
*   `python-dotenv`
*   `google-generativeai`
* `textblob`
* `pandas`

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set up the Gemini API key:**
    *   Create a `.env` file in the project's root directory.
    *   Add your Gemini API key to the `.env` file:
        ```
        GEMINI_API_KEY=your_api_key_here
        ```
4.  **Run the Streamlit app:**
    ```bash
    streamlit run reviewqna.py
    ```

## Usage

1.  Open the Streamlit app in your web browser.
2.  Enter an Amazon product URL in the text input field.
3.  Click the "Submit" button.
4.  View the overall review summary, product details, specifications, and description score.
5.  Click the "Read Overall Review" button to hear the summary aloud.
6. Ask question about the product.


