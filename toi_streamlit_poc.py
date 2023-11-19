import re
import pytz
import bs4

import markdownify as md
import streamlit as st

from urllib.request import Request, urlopen
from datetime import datetime, timezone

now_ts = datetime.now(timezone.utc)

st.set_page_config(layout = 'wide')

st.header('Times of Israel Live Blog: ' + now_ts.strftime("%B %d %Y"))

#to_parse_url = 'https://www.timesofisrael.com/liveblog-' + now_ts.strftime('%B-%d-%Y').lower()
to_parse_url = 'https://www.timesofisrael.com/liveblog-november-16-2023'

soup = bs4.BeautifulSoup(urlopen(Request(to_parse_url, headers = {'User-Agent': 'Mozilla/5.0'})).read(), 'html.parser')

liveblog_entries = soup.find('div', id = re.compile('^liveblog-\d')).find_all(id = re.compile('^liveblog-entry-\d'))

for lb_entry in liveblog_entries:
  lb_entry_datetime = datetime.utcfromtimestamp(int(lb_entry.find('div', class_ = 'liveblog-date').a.span['data-timestamp']))
  lb_entry_datetime_est = pytz.timezone('UTC').localize(lb_entry_datetime).astimezone(pytz.timezone('US/Eastern'))
  lb_entry_datetime_est_str = lb_entry_datetime_est.strftime('%I:%M:%S %p')

  lb_entry_paragraph = lb_entry.find('div', class_ = 'liveblog-paragraph')

  lb_entry_title_helper = lb_entry_paragraph.h4.a

  lb_entry_title = lb_entry_title_helper.text
  lb_entry_href = lb_entry_title_helper['href']

  expander = st.expander(':red[' + lb_entry_datetime_est_str + '] **' + lb_entry_title + '**')

  lb_entry_paragraph.h4.decompose()
  lb_entry_paragraph.find('ul', class_ = 'social liveblog-social').decompose()

  lb_entry_byline = lb_entry_paragraph.find('div', class_ = 'byline')
  if lb_entry_byline:
    lb_entry_byline_text = str(lb_entry_byline)
    lb_entry_byline.decompose()
    expander.caption(md.markdownify(lb_entry_byline_text))

  lb_entry_media = lb_entry.find('div', class_ = 'media')
  if lb_entry_media:
    tmp_media = lb_entry_media.a.img
    expander.image(tmp_media['src'])
    expander.caption(tmp_media['title'])
    lb_entry_media.decompose()

  #This code removes the outer div, but is not necessary as it does not translate into the Markdown
  #lb_entry_html = ''.join([str(x) for x in lb_entry_paragraph.contents])
  
  expander.write(md.markdownify(str(lb_entry_paragraph)))
  expander.caption(f'[Link to Original Post]({lb_entry_href})')