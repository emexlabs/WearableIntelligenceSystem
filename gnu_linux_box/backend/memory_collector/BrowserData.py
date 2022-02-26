#warning that timestamps from browsers are in WebKit time, so microseconds since Jan 1, 1601. Thanks Derek Lam.

import numpy as np
import requests
import sys
import os
import sqlite3
import time
from bs4 import BeautifulSoup
from bs4.element import Comment
import urllib.request
from selenium import webdriver
from shutil import copyfile
import json
import pandas as pd
import random
import config
import lxml
import cchardet
import datetime

class BrowserData:
    def __init__(self, browser_name="brave"):
        #single file keys
        self.sf_keys = ["url", "name"]

        #browser keys
        self.keys = ["url", "name", "date_added"]

        #browser name
        self.browser_name = browser_name #"chrome", "firefox" are options

    def openDB(self, name):
            # Creates or opens a file called mydb with a SQLite3 DB
            copyfile(name, "./{}".format(os.path.basename(name)))
            db = sqlite3.connect("./{}".format(os.path.basename(name)))
            return db

    def closeDB(self, db):
            db.close()
            return 1

    def firefoxHistory(self, db, cursor):
            """cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            print(cursor.fetchall())
            cursor.execute("PRAGMA table_info(moz_places);")
            print("Table structure: {}".format(cursor.fetchall()))"""
            cursor.execute("SELECT * FROM moz_places;")
            resp = cursor.fetchall()
            urls = list()
            for tup in resp:
                    urls.append([tup[1], tup[2], int(tup[5])])
            return urls

    def chromeHistory(self, db, cursor): #also used for Brave browser
            """cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            print(cursor.fetchall())
            cursor.execute("PRAGMA table_info(urls);")
            print("Table structure: {}".format(cursor.fetchall()))"""
            cursor.execute("SELECT * FROM URLS;")
            resp = cursor.fetchall()
            urls = list()
            for tup in resp:
                urls.append([tup[1], tup[2], int(tup[5])])
            return urls

    def scrape(self, urls):
            done = os.listdir("./history/")
            for i, f in enumerate(done):
                done[i] = f[:-4]
                
            driver = webdriver.Firefox(timeout=20)
            driver.set_page_load_timeout(5)
            for url in urls:
                if ("duckduckgo" in url[0]) or ("google.com" in url[0]) or ("google.ca" in url[0]) or ("localhost" in url[0]) or ("192.168" in url[0]): #ignore search engines
                    print("Skipping...")
                    continue
                if url[2] in done: #skip if we already have a file for this entry
                    print("Skipping...")
                    continue
                try:
                    driver.get(url[0])
                    time.sleep(3) #wait for JS to load
                    pageText = driver.find_element_by_tag_name("body").text
                    if pageText is not None and pageText != "" and not pageText.isspace():
                        with open("./history/{}.txt".format(url[2]), 'w') as f:
                            f.write(url[0] + "\n")
                            f.write(url[1] + "\n")
                            f.write(url[2] + "\n")
                            f.writelines(pageText)
                except Exception as e:
                    print(e)

    def pullHistory(self, name):
        db = self.openDB(name)
        cursor = db.cursor()
        if self.browser_name == "brave" or self.browser_name == "chrome":
                urls = self.chromeHistory(db, cursor)
        elif sys.argv[1] == "firefox":
                urls = self.firefox(db, cursor)
        cursor.close()
        self.closeDB(db)
        history_df = pd.DataFrame(urls, columns=self.keys)
        history_df = self.convert_df_webkit_datetime(history_df)
        return history_df

    def loadBookmarks(self, name):
        with open(name, 'r') as f:
            a = json.load(f)

        booksList = list()

        def surfBooks(books): #folders can be in folders can be in folders, so we use this function recursively to jump down the bookmarks hierarchy
            for book in books['children']:
                if book['type'] == 'url':
                    booksList.append([book['url'], book['name'], int(book['date_added'])])
                elif book['type'] == 'folder':
                    surfBooks(book)
            
        for i in a['roots'].keys():
            surfBooks(a['roots'][i])

        bookmarks_df = pd.DataFrame(booksList, columns=self.keys)
        bookmarks_df = self.convert_df_webkit_datetime(bookmarks_df)

        return bookmarks_df

    def convert_df_webkit_datetime(self, df, col_name="date_added"):
        timestamp = 13107300761977770
        def convert_webkit_to_unix(delta):
            if delta == 0:
                return pd.Timestamp(0)
            unix_time = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=delta)
            return pd.Timestamp(unix_time)
        df[col_name] = df.apply(lambda row : convert_webkit_to_unix(row['date_added']), axis = 1)
        return df

    def convert_to_wearable_referencer_format(self, df):
        local_keys = ["id", "name", "authours", "link", "keyword_list"]
        df = df.rename(columns={"url" : "link", "date_added" : "year"})
        df["keyword_list"] = "" #empty strings
        df["authours"] = "" #empty strings

        #reorder columns
        df = df[["name","year","authours","link","keyword_list"]]
        return df

    def get_history_and_bookmarks_from_browser(self):
        history_df = self.pullHistory(config.historyFile)
        bookmarks_df = self.loadBookmarks(config.bookmarksFile)
        return history_df, bookmarks_df

    def get_history_from_single_file(self, sf_history):
        """
        sf_history is an array of file names that have already been scraped. We use this because it takes a long time to scrape 10,000s of pages, so we should only do that once.
        Right now, this just pulls text, but soon we can add images, etc because we can create embeddings of images, audio, etc in the same vector space as text (with txtai or similiar tools)
        """
        start_string = "internet_history_backup"
        result = [["file://" + os.path.join(dp, f), os.path.splitext(f)[0]] for dp, dn, filenames in os.walk(config.single_file_root) for f in filenames if ((start_string in os.path.splitext(f)[0]) and (".html" in os.path.splitext(f)[1]) and (f not in sf_history))]
        result = result[:15]
        sf_history_df = pd.DataFrame(result, columns=self.sf_keys)

        sf_history_df['text'] = sf_history_df.apply(lambda row : self.get_text_from_html_file(row['url'][len("file://"):]), axis = 1)
        sf_history_df[['name', 'date_added']] = sf_history_df.apply(lambda row : self.parse_sf_file_name(row['name']), axis = 1, result_type="expand")
        return sf_history_df

    #get text from html file
    def get_text_from_html_file(self, file_name):
        html = urllib.request.urlopen("file://" + file_name).read()
        text = self.text_from_html(html)
        return text

    # reference - https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text
    def tag_visible(self, element):
        if element == "\n":
            return False
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True

    def visible_text_recreator(self, element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return ""
        if isinstance(element, Comment):
            return ""
        return element

    def filter_texts(self, texts):
        res = ""
        old_app = ""
        for t in texts:
            app = self.visible_text_recreator(t)
            if old_app == "\n" and app == "\n":
                continue
            res += app
            old_app = app
        return res

    def text_from_html(self, body):
        soup = BeautifulSoup(body, 'lxml')
        texts = soup.findAll(text=True)
        visible_texts = self.filter_texts(texts)  
        return visible_texts
    
    def parse_sf_file_name(self, file_name):
        """
        internet_history_backup_{page-title}_({date-locale}_{time-locale}).html

        file_name is the name of a file, NOT the path, and with the extension ALREADY REMOVED
        """
        starter = "internet_history_backup_"
        info = file_name[len(starter):]
        date_start_idx = info.rindex("(")
        date_string = info[date_start_idx+1:-1]
        name = info[:date_start_idx-1]
        sf_date = datetime.datetime.strptime(date_string, "%d_%m_%Y_%H_%M_%S")
        return name, sf_date

def main():
    browser_data = BrowserData()
    sf_history_df = browser_data.get_history_from_single_file([])

#def main():
#    """
#    How to use
#    python3 browsemem.py {nameofbrowser} 
#    make sure to fill in the config with your browser file locations
#    TODO make the script auto pull the file locations
#    """
#    if len(sys.argv) < 3:
#        print("Please supply a browser and a destination folder. Example usage: `python3 bak_browser_data.py firefox ~/MyDataStuffFolder` \nExiting.")
#        sys.exit()
#
#    history_df = pullHistory(config.historyFile)
#    history_df.to_csv(os.path.join(sys.argv[2], "browser_history_{}.csv".format(time.time())))
#
#    bookmarks_df = loadBookmarks(config.bookmarksFile)
#    bookmarks_df.to_csv(os.path.join(sys.argv[2], "browser_bookmarks_{}.csv".format(time.time())))
#    converted_bookmarks_df = convert_to_wearable_referencer_format(bookmarks_df)
#    converted_history_df = convert_to_wearable_referencer_format(history_df)
#    converted_history_df.to_csv(os.path.join(sys.argv[2], "wearable_referencer_browser_history_{}.csv".format(time.time())))
#    converted_bookmarks_df.to_csv(os.path.join(sys.argv[2], "wearable_referencer_browser_bookmarks_{}.csv".format(time.time())))
#
if __name__ == "__main__":
    main()
