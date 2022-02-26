import os
import config
import pandas as pd
import sys

class VimWikiData:
    def __init__(self):
        self.keys = ["url", "name"]

    #get text from file
    def get_text_from_filename(self, file_name):
        try:
            with open(file_name,"r") as file: x = file.read().splitlines()
            return x
        except UnicodeDecodeError as e:
            return [""]

    #get vimwiki files + text
    def get_new_vimwiki_files(self):
        #get file location, name and filetype
        result = [["file://" + os.path.join(dp, f), os.path.splitext(f)[0]] for dp, dn, filenames in os.walk(config.vimwiki_root) for f in filenames if ".swp" not in os.path.splitext(f)[1]]
        vimwiki_df = pd.DataFrame(result, columns=self.keys)

        vimwiki_df['text'] = vimwiki_df.apply(lambda row : self.get_text_from_filename(row['url'][len("file://"):]), axis = 1)
        return vimwiki_df
