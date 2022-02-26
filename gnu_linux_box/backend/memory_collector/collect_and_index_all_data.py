#collect all of this data, embed it, and index it. After this call, data will be ready to be searched by our Remembrance Agent system
#data: browser history, browser bookmarks, voice transcriptions, PKMS, etc.

from BrowserData import BrowserData
from VimWikiData import VimWikiData

#web browser data
browser_data = BrowserData()
history_df, bookmarks_df = browser_data.get_history_and_bookmarks_from_browser()
sf_history_df = browser_data.get_history_from_single_file([])

#PKMS data
vimwiki_data = VimWikiData()
vimwiki_df = vimwiki_data.get_new_vimwiki_files()

#just references
print("history:")
print(history_df)
print("bookmarks:")
print(bookmarks_df)

#references with content
print("single file full history:")
print(sf_history_df)
print("vimwiki:")
print(vimwiki_df)
