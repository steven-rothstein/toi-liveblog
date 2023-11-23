# Times of Israel Live Blog: Streamlit Application

This repository holds a simple Python script that scrapes [The Times of Israel's](https://timesofisrael.com) current live blog for its content, and writes it to a [Streamlit](https://streamlit.io) application that uses `expander` components for each blog post. The goal of this application is entirely UI-based. The news source's page requires users to scroll through all content, and the desire was to scroll through headlines and expand the headline if the article content was desired.

## Usage

The original goal was to deploy this Streamlit application to the Streamlit Community Cloud, but their servers block the web scrape (it is allowed locally). As such, the requirements.txt file needed for Streamlit application deployment is included in case this limitation changes.

To run this application, install Python and all packages listed in the requirements.txt file. Additionally, install the `streamlit` package (it is available via pip). Either clone this repo or download it locally. Finally, open a terminal and navigate to the directory where the repo is cloned or downloaded. Run the following command:

`streamlit run toi_liveblog_scrape_streamlit.py`

