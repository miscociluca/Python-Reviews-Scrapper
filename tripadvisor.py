# -*- coding: utf-8 -*-
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
from datetime import datetime
import time
import re
import logging
import traceback
from selenium.webdriver.remote.webelement import WebElement

GM_WEBPAGE = 'https://www.tripadvisor.com/'
MAX_WAIT = 10
MAX_RETRY = 5
MAX_SCROLLS = 40


class TripAdvisorScraper:

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
        text = ""
        try:
            actualPosts = item.find("p",{"class": "partial_entry"})
            if actualPosts:
                text += actualPosts.text
        except Exception as e:
            text = ''
        return text

    def _extract_userName(self,item):
        username = ""
        try:
            username = item.find('div', class_='info_text pointer_cursor').find('div').text
        except Exception as e:
            username = ""
        return username

    def _extract_postDate(self,item):
        try:
            date = item.find('span',class_="ratingDate").text
        except Exception as e:
            date = ''

        return date

    def _extract_post_id(self,item):
        try:
            postIds =item.find("div", {"class": "quote"}).find('a')
            post_id = "https://www.tripadvisor.com" + postIds.get('href')
        except Exception as e:
            postIds = ""     
        return post_id


    def _extract_comments(self,item):
        try:
            comment = item.find("div", {"class": "mgrRspnInline"})
        except Exception as e:
            comment = ""
        comments = dict()
        if comment != "" and comment != None:
            commenter = comment.find("div", {"class":"header"}).text
            responded = comment.find("span", {"class":"responseDate"}).text
            actualPosts = comment.find("div",{"class": "entry"})
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

    def check_exists_by_xpath(self,xpath):
        try:
            self.driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        return True

    def _extract_html(self,bs_data,page):
        k = bs_data.find_all(class_="reviewSelector cx_brand_refresh_phase2")
        postBigDict = list()
        for item in k:
            postDict = dict()
            postDict['Username'] = self._extract_userName(item)
            data = self._extract_postDate(item)
            data = data.replace('Reviewed ', '')
            postDict['Date'] = data
            postDict['Post'] = self._extract_post_text(item)
            isResponded = self._extract_comments(item)
            if isResponded is None:
                postDict['IsResponded'] = 'False'
            else:
                postDict['IsResponded'] = 'True'

            postDict['Comments'] = self._extract_comments(item)
            postDict['PostUrl'] = self._extract_post_id(item)
            postBigDict.append(postDict)
            
        return postBigDict


    def extract(self,page, numOfPost):
        result = list()
        self.driver.get(page)
        elementList= self.driver.find_element_by_class_name("pageNumbers")       
        pagesBtns = elementList.find_elements_by_class_name("pageNum")
        lastPageNumber = int(pagesBtns[len(pagesBtns)-1].text)
        reviewsUrls = []
        for pages in range (1,lastPageNumber):
            try:
                if (self.check_exists_by_xpath("//span[@class='taLnk ulBlueLinks']")):
                    try: 
                        moreBtns = self.driver.find_elements_by_xpath("//span[@class='taLnk ulBlueLinks']")         
                        for target in moreBtns:
                            if target.text == 'More':
                                target.click()
                                time.sleep(3)
                                break           
                    except Exception as e: 
                        moreBtns = self.driver.find_elements_by_xpath("//span[@class='taLnk ulBlueLinks']")
                        for target in moreBtns:
                            if target.text == 'More':
                                target.click()
                                time.sleep(3)
                                break
                   
                source_data = self.driver.page_source
                # Throw your source into BeautifulSoup and start parsing!
                bs_data = bs(source_data, 'html.parser')
                postBigDict = self._extract_html(bs_data,page)
                result.append(postBigDict)


                if (self.check_exists_by_xpath('//a[@class="ui_button nav next primary "]')):
                    self.driver.find_element_by_xpath('//a[@class="ui_button nav next primary "]').click()
                    time.sleep(5)


            except Exception as e:
                print(e)

        return result


    def get_reviews(self,url,offset):
        postBigDict = self.extract(page=url, numOfPost=offset)
        return postBigDict

    def __get_logger(self):
        # create logger
        logger = logging.getLogger('tripadvisor-scraper')
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
        options.add_argument('log-level=3')
        options.add_argument("--disable-notifications")
        options.add_argument("--lang=en-GB")
        input_driver = webdriver.Chrome(
            executable_path='C:/Users/LucaMiscoci/Desktop/scrapping/chromedriver.exe', chrome_options=options)

        return input_driver

    # util function to clean special characters

    def __filter_string(self, str):
        strOut = str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        return strOut