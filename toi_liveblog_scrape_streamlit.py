import re  # For regular expressions
import pytz  # For time zone conversions
import bs4  # For the scrape
import platform  # For platform-dependent date format

import markdownify as md  # Simple html to markdown conversion
import streamlit as st  # Frontend

from urllib.request import Request, urlopen  # For obtaining the html for the scrape
from datetime import datetime, timezone, timedelta  # Time zone management


# Given a `datetime` named `ts_arg`, generate the url to scrape, which is based on the current UTC time.
def generate_scrape_url(ts_arg):
    leading_0_char = "-"

    if platform.system() == "Windows":
        leading_0_char = "#"

    if ts_arg.month >= 11:
        leading_0_char = ""

    return (
        "https://www.timesofisrael.com/liveblog-"
        + ts_arg.strftime(f"%B-%{leading_0_char}d-%Y").lower()
    )


# Helper function to request a webpage to scrape, given a string `url`.
def generate_url_request(url):
    return urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}))


# Scrape the live blog, given a `datetime` named` `ts_arg` for which to check live blog posts.
def scrape_liveblog(ts_arg):
    lb_url = generate_scrape_url(ts_arg)

    # If the live blog is not up yet, try yesterday's rather than throw an error.
    try:
        url_request = generate_url_request(lb_url)
    except:
        url_request = generate_url_request(
            generate_scrape_url(ts_arg - timedelta(days=1))
        )

    # Parse the scraped html!
    soup = bs4.BeautifulSoup(
        url_request.read(),
        "html.parser",
    )

    # Grab the page headline and underline
    liveblog_header = soup.find("h1", class_="headline").text
    liveblog_underline = soup.find("h2", class_="underline").text

    # Write to frontend
    st.markdown(f"#### {liveblog_header}")
    st.write(f":grey[{liveblog_underline}]")

    # Find all live blog entries
    liveblog_entries = soup.find("div", id=re.compile("^liveblog-\d")).find_all(
        id=re.compile("^liveblog-entry-\d")
    )

    # Loop through each entry, parse its components, and write them to the front end.
    for lb_entry in liveblog_entries:
        # Get the datetime of the entry and convert it to US/Eastern.
        lb_entry_datetime = datetime.utcfromtimestamp(
            int(lb_entry.find("div", class_="liveblog-date").a.span["data-timestamp"])
        )
        lb_entry_datetime_est = (
            pytz.timezone("UTC")
            .localize(lb_entry_datetime)
            .astimezone(pytz.timezone("US/Eastern"))
        )
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
        lb_entry_paragraph.find("ul", class_="social liveblog-social").decompose()

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
            caption_images = [
                lb_entry_caption.a["href"] for lb_entry_caption in lb_entry_captions
            ]
            caption_captions = [
                lb_entry_caption.find("div", class_="wp-caption-text").text
                for lb_entry_caption in lb_entry_captions
            ]

            # Write to frontend
            expander.image(caption_images, caption=caption_captions)

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
