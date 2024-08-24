from .authentication import BeaconAuthentication
from .content import BeaconContent
from . import helpers

import subprocess
import requests
import logging
import json
import time
import m3u8
import os

import progressbar
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException

series_url = "https://beacon.tv/series"

class BeaconSeries:
    def __init__(self, auth : BeaconAuthentication):
        self.auth = auth
        self.id = None                  
        self.title = None               
        self.description = None
        self.series_url = None
        self.content = []

    def get_all_series(auth : BeaconAuthentication):
        logging.info("Finding all series IDs")

        driver = auth.get_driver()        
        driver.get(series_url)

        # click "load more" until everything is loaded
        click_count = 0
        while True:
            try:
                # find the button
                load_more_span = driver.find_element(By.XPATH, "//span[text()='Load More']")
                load_more_button = load_more_span.find_element(By.XPATH, "./ancestor::button")
                driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
                
                logging.log(helpers.LOG_VERBOSE, f"\"Load More\" click #{click_count}")
                click_count = click_count + 1
                load_more_button.click()
                time.sleep(1)
            except ElementClickInterceptedException: # clicking too fast or while its loading will throw this, so we will just try again
                continue
            except NoSuchElementException: # I hate python
                break
            except StaleElementReferenceException: # if we get the element when the page removes it
                break

        # get all the links
        unique_ids = set()
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="series"]')
        for link in links:
            href = link.get_attribute('href')
            if series_url in href:
                value = href.split("/series/")[-1]
                if value != series_url: # bit of a hack to ignore the main series link at the top of the page
                    unique_ids.add(value)

        # Convert the set to a list
        series_ids = list(unique_ids)
        logging.info(f"found {len(series_ids)} series after {click_count} clicks to load")

        # create content info for each found id
        for series_id in series_ids:
            logging.log(helpers.LOG_VERBOSE, f"Found series \"{series_id}\"")
        
        return series_ids


    @classmethod
    def create(cls, auth : BeaconAuthentication, series_id : str, auto_fetch : bool = False):

        # Initialize the browser
        driver = auth.get_driver()
        
        new_series = None
        try:
            url = f"{series_url}/{series_id}"
            driver.get(url)
            
            title = driver.find_element(By.CSS_SELECTOR, 'h2.is_Type.font_heading').text
            description = driver.find_element(By.CSS_SELECTOR, 'p.is_Type.font_body').text

            new_series = cls(auth)
            new_series.id           = series_id
            new_series.title        = title
            new_series.description  = description
            new_series.series_url   = url
            
            new_series.fetch(auth)

        except:
            logging.warn(f"Unable to create series \"{series_id}\".")
        return new_series

    # fetches all the content for this series
    def fetch(self, auth : BeaconAuthentication):

        driver = auth.get_driver()        
        driver.get(self.series_url)

        # click "load more" until everything is loaded
        click_count = 0
        while True:
            try:
                # find the button
                load_more_span = driver.find_element(By.XPATH, "//span[text()='Load More']")
                load_more_button = load_more_span.find_element(By.XPATH, "./ancestor::button")
                driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
                
                logging.log(helpers.LOG_VERBOSE, f"\"Load More\" click #{click_count}")
                click_count = click_count + 1
                load_more_button.click()
                time.sleep(1)
            except ElementClickInterceptedException: # clicking too fast or while its loading will throw this, so we will just try again
                continue
            except NoSuchElementException: # I hate python
                break
            except StaleElementReferenceException: # if we get the element when the page removes it
                break

        # get all the links
        logging.info("Finding all Content IDs")
        unique_ids = set()
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="content"]')
        for link in links:
            href = link.get_attribute('href')
            if '/content/' in href:
                value = href.split('/content/')[-1]
                unique_ids.add(value)

        # Convert the set to a list
        content_ids = list(unique_ids)
        logging.info(f"found {len(content_ids)} content after {click_count} clicks to load")

        # create content info for each found id
        for content_id in progressbar.ProgressBar(redirect_stdout=True, redirect_stderr=True)(content_ids):
            logging.log(helpers.LOG_VERBOSE, f"Reading Content for \"{content_id}\"")
            new_content = BeaconContent.create(auth, content_id)
            if new_content is not None:
                self.content.append(new_content)
