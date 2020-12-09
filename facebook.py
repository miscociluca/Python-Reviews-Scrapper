import argparse
import time
import json
import csv
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
from datetime import datetime
import time
import re
import logging
import traceback

# with open('facebook_credentials.txt') as file:
    # EMAIL = file.readline().split('"')[1]
    # PASSWORD = file.readline().split('"')[1]

GM_WEBPAGE = 'https://www.facebook.com/'
MAX_WAIT = 10
MAX_RETRY = 5
MAX_SCROLLS = 40

class FacebookScraper:
    def __init__(self, debug=False):
        self.debug = debug
        self.driver = self.__get_driver()
        self.logger = self.__get_logger()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)

        self.driver.close()
        self.driver.quit()
        return True
            
        
    def _extract_post_text(self,item):
        actualPosts = item.find_all(attrs={"data-testid": "post_message"})
        text = ""
        if actualPosts:
            for posts in actualPosts:
                paragraphs = posts.find_all('p')
                text = ""
                for index in range(0, len(paragraphs)):
                    text += paragraphs[index].text
        return text

    def _extract_userName(self,item):
        username = "";
        try:
            username = item.find(class_="profileLink").text
        except Exception as e:
            username = "";
        return username

    def _extract_postDate(self,item):
        date = item.find(class_="timestampContent").text;
        return date
        
    def _extract_link(self,item):
        postLinks = item.find_all(class_="_6ks")
        link = ""
        for postLink in postLinks:
            link = postLink.find('a').get('href')
        return link


    def _extract_post_id(self,item):
        postIds =item.find("a", {"class": "_5pcq"})
        post_id = ""
        post_id = f"https://www.facebook.com{postIds.get('href')}"
        return post_id


    def _extract_image(self,item):
        postPictures = item.find_all(class_="scaledImageFitWidth img")
        image = ""
        for postPicture in postPictures:
            image = postPicture.get('src')
        return image


    def _extract_shares(self,item):
        postShares = item.find_all(class_="_4vn1")
        shares = ""
        for postShare in postShares:

            x = postShare.string
            if x is not None:
                x = x.split(">", 1)
                shares = x
            else:
                shares = "0"
        return shares


    def _extract_comments(self,item,merchant):
        postComments = item.findAll("div", {"class": "_4eek"})
        comments = dict()
        # print(postDict)
        for comment in postComments:
            if comment.find(class_="_6qw4") is None:
                continue

            commenter = comment.find(class_="_6qw4").text
            comments[commenter] = dict()

            comment_text = comment.find("span", class_="_3l3x")

            if comment_text is not None:
                comments[commenter]["text"] = comment_text.text

            comment_link = comment.find(class_="_ns_")
            if comment_link is not None:
                comments[commenter]["link"] = comment_link.get("href")

            comment_pic = comment.find(class_="_2txe")
            if comment_pic is not None:
                comments[commenter]["image"] = comment_pic.find(class_="img").get("src")

            commentList = item.find('ul', {'class': '_7791'})
            if commentList:
                comments = dict()
                comment = commentList.find_all('li')
                if comment:
                    for litag in comment:
                        aria = litag.find("div", {"class": "_4eek"})
                        if aria:
                            commenter = aria.find(class_="_6qw4").text
                            comments[commenter] = dict()
                            comment_text = litag.find("span", class_="_3l3x")
                            if comment_text:
                                comments[commenter]["text"] = comment_text.text
                                # print(str(litag)+"\n")

                            comment_link = litag.find(class_="_ns_")
                            if comment_link is not None:
                                comments[commenter]["link"] = comment_link.get("href")

                            comment_pic = litag.find(class_="_2txe")
                            if comment_pic is not None:
                                comments[commenter]["image"] = comment_pic.find(class_="img").get("src")

                            repliesList = litag.find(class_="_2h2j")
                            if repliesList:
                                reply = repliesList.find_all('li')
                                if reply:
                                    comments[commenter]['reply'] = dict()
                                    for litag2 in reply:
                                        aria2 = litag2.find("div", {"class": "_4efk"})
                                        if aria2:
                                            replier = aria2.find(class_="_6qw4").text
                                            if replier:
                                                comments[commenter]['reply'][replier] = dict()

                                                reply_text = litag2.find("span", class_="_3l3x")
                                                if reply_text:
                                                    comments[commenter]['reply'][replier][
                                                        "reply_text"] = reply_text.text

                                                r_link = litag2.find(class_="_ns_")
                                                if r_link is not None:
                                                    comments[commenter]['reply']["link"] = r_link.get("href")

                                                r_pic = litag2.find(class_="_2txe")
                                                if r_pic is not None:
                                                    comments[commenter]['reply']["image"] = r_pic.find(
                                                        class_="img").get("src")
        if len(comments) > 0:                                           
            return comments;
        else:
            return None;

    def _extract_reaction(self,item):
        toolBar = item.find_all(attrs={"role": "toolbar"})

        if not toolBar:  # pretty fun
            return
        reaction = dict()
        for toolBar_child in toolBar[0].children:
            str = toolBar_child['data-testid']
            reaction = str.split("UFI2TopReactions/tooltip_")[1]

            reaction[reaction] = 0

            for toolBar_child_child in toolBar_child.children:

                num = toolBar_child_child['aria-label'].split()[0]

                # fix weird ',' happening in some reaction values
                num = num.replace(',', '.')

                if 'K' in num:
                    realNum = float(num[:-1]) * 1000
                else:
                    realNum = float(num)

                reaction[reaction] = realNum
        return reaction


    def _extract_html(self,bs_data,merchant):
        k = bs_data.find_all(class_="_5pcr userContentWrapper")
        postBigDict = list();
        for item in k:
            postDict = dict()
            postDict['Username'] = self._extract_userName(item);
            postDict['Date'] = self._extract_postDate(item);
            postDict['Post'] = self._extract_post_text(item)
            isResponded = self._extract_comments(item,merchant);
            if isResponded is None:
                postDict['IsResponded'] = 'False';
            else:
                postDict['IsResponded'] = 'True';
            
            postDict['Comments'] = self._extract_comments(item,merchant)
            postDict['PostUrl'] = self._extract_post_id(item);
            
            postBigDict.append(postDict);
               
        return postBigDict


    # def _login(browser, email, password):
        # browser.get("http://facebook.com")
        # browser.maximize_window()
        # browser.find_element_by_name("email").send_keys(email)
        # browser.find_element_by_name("pass").send_keys(password)
        # browser.find_element_by_name('login').click()
        # time.sleep(5)


    def _count_needed_scrolls(self,browser, infinite_scroll, numOfPost):
        if infinite_scroll:
            lenOfPage = browser.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;"
            )
        else:
            # roughly 8 post per scroll kindaOf
            lenOfPage = int(numOfPost / 8)
        return lenOfPage


    def _scroll(self,browser, infinite_scroll, lenOfPage):
        lastCount = -1
        match = False

        while not match:
            if infinite_scroll:
                lastCount = lenOfPage
            else:
                lastCount += 1

            # wait for the browser to load, this time can be changed slightly ~3 seconds with no difference, but 5 seems
            # to be stable enough
            time.sleep(5)

            if infinite_scroll:
                lenOfPage = browser.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return "
                    "lenOfPage;")
            else:
                browser.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return "
                    "lenOfPage;")

            if lastCount == lenOfPage:
                match = True


    def extract(self,page, numOfPost, infinite_scroll=True, scrape_comment=False):
        #_login(self.driver, EMAIL, PASSWORD)
        print(page)
        self.driver.get(page)
        acceptAllBtn=self.driver.find_elements_by_xpath('//button[@class=\'_42ft _4jy0 _9fws _4jy3 _4jy1 selected _51sy\']')
        acceptAllBtn[0].click();
        # notNowBtn=self.driver.find_elements_by_xpath('//a[@class=\'_3j0u\']')
        # notNowBtn[0].click();
        
        lenOfPage = self._count_needed_scrolls(self.driver, infinite_scroll, numOfPost)
        self._scroll(self.driver, infinite_scroll, lenOfPage)

        # Now that the page is fully scrolled, grab the source code.
        source_data = self.driver.page_source
        # Throw your source into BeautifulSoup and start parsing!
        bs_data = bs(source_data, 'html.parser')
        merchant = page[25:-9];
        postBigDict = self._extract_html(bs_data,merchant)

        return postBigDict


    def get_reviews(self,url,offset):
        infinite = True
        scrape_comment = False
        postBigDict = self.extract(page=url, numOfPost=offset, infinite_scroll=infinite, scrape_comment=scrape_comment)
        return postBigDict


       

    def __get_logger(self):
        # create logger
        logger = logging.getLogger('facebook-scraper')
        logger.setLevel(logging.DEBUG)

        # create console handler and set level to debug
        fh = logging.FileHandler('scraper.log')
        fh.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # add formatter to ch
        fh.setFormatter(formatter)

        # add ch to logger
        logger.addHandler(fh)

        return logger


    def __get_driver(self, debug=False):
        options = Options()

        if not self.debug:
            options.add_argument("--headless")
        else:
            options.add_argument("--window-size=1366,768")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--lang=en-GB")
        input_driver = webdriver.Chrome(executable_path='C:/Users/LucaMiscoci/Desktop/scrapping/chromedriver.exe',chrome_options=options)

        return input_driver


    # util function to clean special characters
    def __filter_string(self, str):
        strOut = str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        return strOut
