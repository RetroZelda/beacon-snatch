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

collections_url = "https://beacon.tv/collections"

class BeaconCollectionID:
    def __init__(self, my_id : str, parent_id : str = None):
        self.id = my_id
        self.parent_id = parent_id

class BeaconCollection:
    def __init__(self, auth : BeaconAuthentication):
        self.auth = auth
        self.id : BeaconCollectionID = None                  
        self.title = None               
        self.description = None
        self.collection_url = None
        self.content = []
        self.collections = []

    def get_all_collections(auth : BeaconAuthentication, max_depth : int = 5):
        logging.info("Finding all collection IDs")

        # Convert the set to a list
        unique_ids = BeaconCollection.recursive_gather_collections(auth, collections_url, None, max_depth)

        collection_ids = list(unique_ids)

        # create content info for each found id
        for collection_id in collection_ids:
            logging.log(helpers.LOG_VERBOSE, f"Found collection \"{collection_id}\"")
        
        return collection_ids

    def recursive_gather_collections(auth : BeaconAuthentication, collection_url : str, base_collection_id : str, remaining_depth : int) -> set[BeaconCollectionID]:
        driver = auth.get_driver()        
        driver.get(collection_url)

        # click "load more" until everything is loaded
        click_count = 0
        while True:
            try:
                # find the button
                load_more_span = driver.find_element(By.XPATH, "//span[text()='Load More']")
                load_more_button = load_more_span.find_element(By.XPATH, "./ancestor::button")
                driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
                
                logging.log(helpers.LOG_VERBOSE, f"Depth {remaining_depth}|{base_collection_id}: \"Load More\" click #{click_count}")
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
        unique_ids = set[BeaconCollectionID]()
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="collections"]')
        for link in links:
            href = link.get_attribute('href')
            if collections_url in href:
                value = href.split("/collections/")[-1]
                
                not_root = value != collections_url  # bit of a hack to ignore the main collections link at the top of the page
                not_self = base_collection_id != value
                if not_root and not_self:
                    unique_ids.add(BeaconCollectionID(value, base_collection_id))

        logging.info(f"Depth {remaining_depth}|{base_collection_id}: found {len(unique_ids)} collections after {click_count} clicks to load")
        if remaining_depth > 0:
            if len(unique_ids) > 0:
                new_ids = set[BeaconCollectionID]()
                for collection_id in unique_ids:
                    new_ids.update(BeaconCollection.recursive_gather_collections(auth, f"{collections_url}/{collection_id.id}", collection_id.id, remaining_depth - 1))

                logging.info(f"Depth {remaining_depth}|{base_collection_id}: found {len(new_ids)} more collections after recursing down")
                unique_ids.update(new_ids)
        else:
            logging.info(f"Depth {remaining_depth}|{base_collection_id}: Reached the max depth")
        return unique_ids

    @classmethod
    def create(cls, auth : BeaconAuthentication, collection_id : str, auto_fetch : bool = False):

        # Initialize the browser
        driver = auth.get_driver()
        
        new_collection = None
        try:
            url = f"{collections_url}/{collection_id}"
            driver.get(url)
            
            title = driver.find_element(By.CSS_SELECTOR, 'h2.is_Type.font_heading').text

            try:
                description = driver.find_element(By.CSS_SELECTOR, 'p.is_Type.font_body').text
            except:
                description = ""

            new_collection = cls(auth)
            new_collection.id               = BeaconCollectionID(collection_id, None)
            new_collection.title            = title
            new_collection.description      = description
            new_collection.collection_url  = url
            
            if auto_fetch:
                new_collection.fetch(auth, -1, True)

        except:
            logging.warning(f"Unable to create collection \"{collection_id}\".")
        return new_collection

    # fetches all the content for this collection
    def fetch(self, auth : BeaconAuthentication, max_pages = -1, auto_fetch_collections : bool = False):

        driver = auth.get_driver()        
        driver.get(self.collection_url)

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

                if max_pages < 0 or click_count < max_pages:
                    load_more_button.click()
                    time.sleep(1)
                else:
                    break
            except ElementClickInterceptedException: # clicking too fast or while its loading will throw this, so we will just try again
                continue
            except NoSuchElementException: # I hate python
                break
            except StaleElementReferenceException: # if we get the element when the page removes it
                break

        # get all the content links
        logging.info("Finding all Content IDs")
        unique_ids = set()
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="content"]')
        for link in links:
            href = link.get_attribute('href')
            if '/content/' in href:
                value = href.split('/content/')[-1]
                unique_ids.add(value)

        # get all the collection links
        unique_collections = set[BeaconCollectionID]()
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="collections"]')
        for link in links:
            href = link.get_attribute('href')
            if collections_url in href:
                value = href.split("/collections/")[-1]
                
                not_root = value != collections_url  # bit of a hack to ignore the main collections link at the top of the page
                not_self = self.id.id != value
                if not_root and not_self:
                    unique_collections.add(BeaconCollectionID(value, self.id.id))

        # Convert the set to a list
        content_ids = list(unique_ids)
        collection_ids = list(unique_collections)        
        logging.info(f"found {len(content_ids)} content and {len(collection_ids)} sub-collections after {click_count} clicks to load")

        # create content info for each found id
        for content_id in progressbar.ProgressBar(redirect_stdout=True, redirect_stderr=True)(content_ids):
            logging.log(helpers.LOG_VERBOSE, f"Reading Content for \"{content_id}\"")
            new_content = BeaconContent.create(auth, content_id)
            if new_content is not None:
                self.content.append(new_content)

        # create collection info for each found id
        for collection_id in progressbar.ProgressBar(redirect_stdout=True, redirect_stderr=True)(collection_ids):
            logging.log(helpers.LOG_VERBOSE, f"Reading Collection for \"{collection_id}\"")
            new_collection = BeaconCollection.create(auth, collection_id.id, auto_fetch_collections)
            if new_collection is not None:
                new_collection.id.parent_id = self.id.id
                self.collections.append(new_collection)
