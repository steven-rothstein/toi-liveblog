import re
import pytz
import bs4

import markdownify as md
import streamlit as st

from urllib.request import Request, urlopen
from datetime import datetime, timezone, timedelta


def generate_scrape_url(ts_arg):
    # %-d removes a leading 0
    d_format = "%B-%-d-%Y"
    if ts_arg.month == 11:
        d_format = "%B-%d-%Y"
    return "https://www.timesofisrael.com/liveblog-" + ts_arg.strftime(d_format).lower()


def generate_url_request(url):
    return urlopen(Request(url, headers={"User-Agent": "XYZ/3.0"}), timeout=10)


def scrape_liveblog(ts_arg):
    lb_url = generate_scrape_url(ts_arg)

    try:
        url_request = generate_url_request(lb_url)
    except:
        url_request = generate_url_request(
            generate_scrape_url(ts_arg - timedelta(days=1))
        )

    soup = bs4.BeautifulSoup(
        url_request.read(),
        "html.parser",
    )

    liveblog_entries = soup.find("div", id=re.compile("^liveblog-\d")).find_all(
        id=re.compile("^liveblog-entry-\d")
    )

    for lb_entry in liveblog_entries:
        lb_entry_datetime = datetime.utcfromtimestamp(
            int(lb_entry.find("div", class_="liveblog-date").a.span["data-timestamp"])
        )
        lb_entry_datetime_est = (
            pytz.timezone("UTC")
            .localize(lb_entry_datetime)
            .astimezone(pytz.timezone("US/Eastern"))
        )
        lb_entry_datetime_est_str = lb_entry_datetime_est.strftime("%I:%M:%S %p")

        lb_entry_paragraph = lb_entry.find("div", class_="liveblog-paragraph")

        lb_entry_title_helper = lb_entry_paragraph.h4.a

        lb_entry_title = lb_entry_title_helper.text
        lb_entry_href = lb_entry_title_helper["href"]

        expander = st.expander(
            ":red[" + lb_entry_datetime_est_str + "] **" + lb_entry_title + "**"
        )

        lb_entry_paragraph.h4.decompose()
        lb_entry_paragraph.find("ul", class_="social liveblog-social").decompose()

        lb_entry_byline = lb_entry_paragraph.find("div", class_="byline")
        if lb_entry_byline:
            lb_entry_byline_text = str(lb_entry_byline)
            lb_entry_byline.decompose()
            expander.caption(md.markdownify(lb_entry_byline_text))

        lb_entry_media = lb_entry_paragraph.find("div", class_="media")
        if lb_entry_media:
            tmp_media = lb_entry_media.a.img
            expander.image(tmp_media["src"])
            expander.caption(tmp_media["title"])
            lb_entry_media.decompose()

        lb_entry_captions = lb_entry_paragraph.find_all(
            "div", class_=re.compile("^wp-caption"), id=re.compile("^attachment")
        )
        if lb_entry_captions:
            for lb_entry_caption in lb_entry_captions:
                expander.image(lb_entry_caption.a["href"])
                expander.caption(
                    lb_entry_caption.find("div", class_="wp-caption-text").text
                )
                lb_entry_caption.decompose()

        expander.write(md.markdownify(str(lb_entry_paragraph)))
        expander.caption(f"[Link to Original Post]({lb_entry_href})")


now_ts = datetime.now(timezone.utc)

st.set_page_config(layout="wide")

st.header("Times of Israel Live Blog")

scrape_ts = st.date_input(
    "Blog Date (click to select)",
    value=now_ts,
    min_value=datetime(2023, 10, 7),
    max_value=now_ts,
    format="YYYY-MM-DD",
)

scrape_liveblog(scrape_ts)
