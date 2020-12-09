# -*- coding: utf-8 -*-
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
from selenium.webdriver.remote.webelement import WebElement

GM_WEBPAGE = 'https://www.opentable.com/'
MAX_WAIT = 10
MAX_RETRY = 5
MAX_SCROLLS = 40


class OpenTableScraper:

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
        actualPosts = item.find("div",{"class": "reviewBodyContainer oc-reviews-8107696f"})
        text = ""
        if actualPosts:
            paragraphs = actualPosts.find_all('p')
            for index in range(0, len(paragraphs)):
                 text += paragraphs[index].text

        return text

    def _extract_userName(self,item):
        username = ""
        try:
            username = item.find('div', class_='oc-reviews-954a6007').find('span').text
        except Exception as e:
            username = ""
        return username

    def _extract_postDate(self,item):
        date = item.find('span',class_="oc-reviews-47b8de40").text
        return date

    def _extract_post_id(self,item):
        postIds =item.find("a", {"class": "_5pcq"})
        post_id = ""
        post_id = f"https://www.facebook.com{postIds.get('href')}"
        return post_id


    def _extract_comments(self,item):
        try:
            comment = item.find("div", {"class": "oc-reviews-94bab1cf"})
        except Exception as e:
            comment = ""
        comments = dict()
        if comment != "" and comment != None:
            commenter = comment.find("div", {"class":"oc-reviews-9cc090e8"}).text
            responded = comment.find("div", {"class":"oc-reviews-e3a0f859"}).text
            actualPosts = comment.find("div",{"class": "publicResponseBodyContainer"})
            text = ""
            if actualPosts:
                paragraphs = actualPosts.find_all('p')
                for index in range(0, len(paragraphs)):
                    text += paragraphs[index].text

            commtext = text
            comments[commenter] = '  '+ responded +'  '+ commtext

        if len(comments) > 0:
            return comments
        else:
            return None

    def _extract_html(self,bs_data,page):
        k = bs_data.find_all(class_="oc-reviews-5a88ccc3")
        postBigDict = list()
        for item in k:
            postDict = dict()
            postDict['Username'] = self._extract_userName(item)
            data = self._extract_postDate(item)
            data = data.replace('Dined on ', '')
            postDict['Date'] = data
            
            postDict['Post'] = self._extract_post_text(item)
            isResponded = self._extract_comments(item)
            if isResponded is None:
                postDict['IsResponded'] = 'False'
            else:
                postDict['IsResponded'] = 'True'

            postDict['Comments'] = self._extract_comments(item)
            postDict['PostUrl'] = page#self._extract_post_id(item)
            postBigDict.append(postDict)

        return postBigDict


    def extract(self,page, numOfPost):
        result = list()
        self.driver.get(page)
        pagesBtns = self.driver.find_elements_by_xpath('//button[@data-parameter=\'page\']')
        lastPageNumber = 0
        if len(pagesBtns) > 3:
            if pagesBtns[3].text.isdigit() is False:
                lastPageNumber = len(pagesBtns) -1
            else:
                lastPageNumber= int(pagesBtns[3].text)
        else:
            lastPageNumber = len(pagesBtns)
        reviewsUrls = []
        for index in range(1, lastPageNumber):
                 url= page + '?page='+ str(index)
                 reviewsUrls.append(url)
        reviewsUrls.append(page + '?page='+ str(lastPageNumber))
        for url in reviewsUrls:
            self.driver.get(url)
            source_data = self.driver.page_source
            # Throw your source into BeautifulSoup and start parsing!
            bs_data = bs(source_data, 'html.parser')
            postBigDict = self._extract_html(bs_data,page)
            result.append(postBigDict)

        return result


    def get_reviews(self,url,offset):
        postBigDict = self.extract(page=url, numOfPost=offset)
        return postBigDict

    def __get_logger(self):
        # create logger
        logger = logging.getLogger('opentable-scraper')
        logger.setLevel(logging.DEBUG)

        # create console handler and set level to debug
        fh = logging.FileHandler('scraper.log')
        fh.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')

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

        options.add_argument("--disable-notifications")
        options.add_argument("--lang=en-GB")
        input_driver = webdriver.Chrome(
            executable_path='C:/Users/LucaMiscoci/Desktop/scrapping/chromedriver.exe', chrome_options=options)

        return input_driver

    # util function to clean special characters

    def __filter_string(self, str):
        strOut = str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        return strOut