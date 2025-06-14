import re  # For regular expressions
import bs4  # For the scrape
import platform  # For platform-dependent date format
import time # Selenium

import markdownify as md  # Simple html to markdown conversion
import streamlit as st  # Frontend

from urllib.request import Request, urlopen  # For obtaining the html for the scrape
from datetime import datetime, timezone, timedelta  # Time zone management
from zoneinfo import ZoneInfo  # For time zone conversions
from selenium import webdriver # Selenium
from selenium.webdriver.chrome.options import Options # Selenium
from selenium.webdriver.chrome.service import Service # Selenium
from selenium.webdriver.common.by import By # Selenium
from selenium.webdriver.support.ui import WebDriverWait # Selenium
from selenium.webdriver.support import expected_conditions as EC # Selenium
from webdriver_manager.chrome import ChromeDriverManager # Selenium


# Helper function to format `datetime` named `ts_arg` according to `format_str`.
# Returns the formatted URL to try to scrape.
def generate_scrape_url(ts_arg, format_str):
    return (
        f"https://www.timesofisrael.com/liveblog-{ts_arg.strftime(format_str).lower()}"
    )


# Given a `datetime` named `ts_arg`, generate the urls to scrape (one with leading 0 in the day, one without),
# which is based on the current UTC time.
def generate_scrape_urls_to_process(ts_arg):
    leading_0_char = "-"

    if platform.system() == "Windows":
        leading_0_char = "#"

    perc_str = "%"

    format_with_leading_0_char = f"%B-%{leading_0_char}d-%Y"
    format_without_leading_0_char = format_with_leading_0_char.replace(
        f"{perc_str}{leading_0_char}", perc_str
    )

    return tuple(
        [
            generate_scrape_url(ts_arg, x)
            for x in [format_with_leading_0_char, format_without_leading_0_char]
        ]
    )


# Helper function to request a webpage to scrape, given a string `url`.
def generate_url_request(url):
    return urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}))


# Scrape the live blog, given a `datetime` named` `ts_arg` for which to check live blog posts.
def scrape_liveblog(ts_arg):
    for _ in range(2):
        # If the live blog is not up yet, try yesterday's rather than throw an error.
        # First, try both versions of leading 0 in the day field for the URL if needed.
        final_lb_url = None
        lb_url_0, lb_url_1 = generate_scrape_urls_to_process(ts_arg)
        try:
            url_request = generate_url_request(lb_url_0)
            final_lb_url = lb_url_0
            break
        except:
            try:
                url_request = generate_url_request(lb_url_1)
                final_lb_url = lb_url_1
                break
            except:
                ts_arg -= timedelta(days=1)

    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    # options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(final_lb_url)

    html = None

    try:
        show_more_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "show-more-btn")))
        show_more_button.click()
        time.sleep(2)  # Wait for updates to load

        # Get the updated page source
        html = driver.page_source
        driver.quit()
    except Exception as e:
        html = url_request.read()

    # Parse the scraped html!
    soup = bs4.BeautifulSoup(
        html,
        "html.parser",
    )

    # Grab the page headline and underline
    liveblog_header = soup.find("h1", class_="headline").text
    liveblog_underline = soup.find("h2", class_="underline").text

    # Write to frontend
    st.markdown(f"#### {liveblog_header}")
    st.write(f":grey[{liveblog_underline}]")

    # Find all live blog entries
    liveblog_entries = soup.find("div", id=re.compile(r"^liveblog-\d")).find_all(
        id=re.compile(r"^liveblog-entry-\d")
    )

    # Loop through each entry, parse its components, and write them to the front end.
    for lb_entry in liveblog_entries:
        # Get the datetime of the entry and convert it to US/Eastern.
        lb_entry_datetime_est = datetime.fromtimestamp(
            int(lb_entry.find("div", class_="liveblog-date").a.span["data-timestamp"]),
            timezone.utc,
        ).astimezone(ZoneInfo("America/New_York"))

        lb_entry_datetime_est_str = lb_entry_datetime_est.strftime("%I:%M:%S %p")

        # The main entry content
        lb_entry_paragraph = lb_entry.find("div", class_="liveblog-paragraph")

        # The entry title
        lb_entry_title_helper = lb_entry_paragraph.h4.a
        lb_entry_title = lb_entry_title_helper.text
        lb_entry_href = lb_entry_title_helper["href"]

        # Write the entry title and timestamp to the frontend, with formatting.
        expander = st.expander(
            f":red[{lb_entry_datetime_est_str}] **{lb_entry_title}**"
        )

        # Remove the already written content from the content to write, as well as the social media links.
        lb_entry_paragraph.h4.decompose()
        lb_entry_paragraph.find("div", class_="single-share").decompose()

        # If a byline is found, get its text, convert to String, remove it from content to be written,
        # and finally convert it to markdown and write as a caption.
        lb_entry_byline = lb_entry_paragraph.find("div", class_="byline")
        if lb_entry_byline:
            lb_entry_byline_text = str(lb_entry_byline)
            lb_entry_byline.decompose()
            expander.caption(md.markdownify(lb_entry_byline_text))

        # If media is found, get its image and caption text, convert the latter to String, remove it all from content to be written later,
        # and finally write the content.
        lb_entry_media = lb_entry_paragraph.find("div", class_="media")
        if lb_entry_media:
            tmp_media = lb_entry_media.a.img
            expander.image(tmp_media["src"], caption=tmp_media["title"])
            lb_entry_media.decompose()

        # Find all captions.
        # Similar to above, grab and format all content and add it now while removing it from the content to be written later.
        lb_entry_captions = lb_entry_paragraph.find_all(
            "div", class_=re.compile("^wp-caption"), id=re.compile("^attachment")
        )
        if lb_entry_captions:
            for lb_entry_caption in lb_entry_captions:
                tmp_caption_a = lb_entry_caption.a
                tmp_caption_img = lb_entry_caption.img
                tmp_caption_text = lb_entry_caption.find(
                    "div", class_="wp-caption-text"
                ).text

                tmp_caption_img_to_use = None
                if tmp_caption_a:
                    tmp_caption_img_to_use = tmp_caption_a["href"]
                elif tmp_caption_img:
                    tmp_caption_img_to_use = tmp_caption_img["src"]

                expander.image(tmp_caption_img_to_use, caption=tmp_caption_text)

            for lb_entry_caption in lb_entry_captions:
                lb_entry_caption.decompose()

        # Convert main content from html to markdown, and write it and a link to the original article to the frontend.
        expander.write(md.markdownify(str(lb_entry_paragraph)))
        expander.caption(f"[Link to Original Post]({lb_entry_href})")


# Get the current UTC time
now_ts = datetime.now(timezone.utc)

# Set the default layout for the frontend
st.set_page_config(layout="wide")

# Write a header to the frontend home page
st.header("Times of Israel Live Blog")

# Write a datetime calendar input widget to the frontend.
# Restrict the dates to only ones that have a web page.
scrape_ts = st.date_input(
    "Blog Date (click to select)",
    value=now_ts,
    min_value=datetime(2023, 10, 7),
    max_value=now_ts,
    format="YYYY-MM-DD",
)

# Perform the scrape!
scrape_liveblog(scrape_ts)
