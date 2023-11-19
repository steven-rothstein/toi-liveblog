import streamlit as st
import streamlit.components.v1 as st_components

import re
import pytz
import bs4
import markdownify as md

from urllib.request import Request, urlopen
from datetime import datetime, timezone

now_ts = datetime.now(timezone.utc)

st.title('Times of Israel Live Blog: ' + now_ts.strftime("%B %d %Y"))

to_parse_url = 'https://www.timesofisrael.com/liveblog-' + now_ts.strftime('%B-%d-%Y').lower()

req = Request(to_parse_url, headers= {'User-Agent': 'Mozilla/5.0'})
html_page = urlopen(req).read()

soup = bs4.BeautifulSoup(html_page, 'html.parser')

liveblog_base = soup.find('div', id = re.compile('^liveblog-\d'))

liveblog_entries = liveblog_base.find_all(id = re.compile('^liveblog-entry-\d'))

liveblog_entries_button_html_list = []

for lb_entry in liveblog_entries:
  lb_entry_date_div = lb_entry.find('div', class_ = 'liveblog-date')

  lb_entry_unix_timestamp = int(lb_entry_date_div.a.span['data-timestamp'])

  lb_entry_datetime = datetime.utcfromtimestamp(lb_entry_unix_timestamp)

  lb_entry_datetime_est = pytz.timezone('UTC').localize(lb_entry_datetime).astimezone(pytz.timezone('US/Eastern'))

  lb_entry_datetime_est_str = lb_entry_datetime_est.strftime('%H:%M:%S')

  lb_entry_paragraph = lb_entry.find('div', class_ = 'liveblog-paragraph')

  lb_entry_title_helper = lb_entry_paragraph.h4.a

  lb_entry_title = lb_entry_title_helper.text
  lb_entry_href = lb_entry_title_helper['href']

  lb_entry_paragraph.h4.decompose()
  lb_entry_paragraph.find('ul', class_ = 'social liveblog-social').decompose()

  lb_entry_html = ''.join([str(x) for x in lb_entry_paragraph.contents])

  liveblog_entries_button_html_list.append('<button class="collapsible">' + lb_entry_datetime_est_str + ' | ' + lb_entry_title + \
                                            '</button>\n' + \
                                            '<div class="content">' + lb_entry_html + '\n</div>')
  
  expander = st.expander(lb_entry_datetime_est_str + ' | ' + lb_entry_title)
  expander.write(md.markdownify(lb_entry_html))
  
st_button_tags = ''.join(liveblog_entries_button_html_list)

st_style_tag = '''<style>
.collapsible {
  background-color: white;
  color: black;
  cursor: pointer;
  padding: 18px;
  width: 100%;
  border-color: red;
  border-bottom: none;
  border-left: none;
  border-right: none;
  text-align: left;
  outline: none;
  font-size: 16px;
  font-family: inherit;
}

.collapsible:hover {
  background-color: lightgrey;
}

.collapsible:after {
  content: "\\002B";
  color: black;
  font-weight: bold;
  float: right;
  margin-left: 5px;
}

.active:after {
  content: "\\2212";
}

.content {
  padding: 0 18px;
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.2s ease-out;
  background-color: white;
}
</style>
'''

st_script_tag = '''<script>
var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.maxHeight){
      content.style.maxHeight = null;
    } else {
      content.style.maxHeight = content.scrollHeight + "px";
    } 
  });
}
</script>
'''

all_st_html = st_style_tag + '\n' + st_button_tags + '\n' + st_script_tag

# st_components.html(all_st_html, height = 1000, scrolling = True)