from . import helpers

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import InvalidCookieDomainException
import logging
import json
import time 
import os

base_url = "https://beacon.tv"
profile_url = "https://beacon.tv/profile"

class BeaconAuthentication:

    def __init__(self, email = None, password = None, cookies_file = None):
        self.email = email
        self.password = password
        self.cookies_file = cookies_file

        self.driver = None
        self.authenticated_cookies = None
        self.username = None
        self.IsAuthenticated = False
        self.CheckedAuthentication = False

        # Set up Chrome options to simulate a real user
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")  # comment this out to debug view what is going on
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36")

        if self.cookies_file is None:
            self.cookies_file = os.path.expanduser(helpers.DEFAULT_COOKIES)
        
        if self.cookies_file is not None:
            self.cookies_file = os.path.expanduser(self.cookies_file)
            self.load_cookies()
            if self.authenticated_cookies is not None:
                self.check_authentication()
        else:
            assert self.email is not None and self.password is not None, "Cookies are somehow invalid. Need to specify an email and password"
    
    def __del__(self):
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

    
    def get_driver(self):
        if self.driver is None:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.implicitly_wait(10)

            self.driver.get(base_url)

            # set cookies if they are loaded
            if self.authenticated_cookies:
                for cookie in self.authenticated_cookies:
                    cookie['domain'] = cookie['domain'].lstrip('.')
                    try:
                        self.driver.add_cookie(cookie)
                    except InvalidCookieDomainException:
                        logging.log(helpers.LOG_VERBOSE, f"Wrong domain for cookie: {cookie}")
                        continue


        return self.driver

    def authenticate(self, force : bool = False):
        
        if self.IsAuthenticated == True and self.CheckedAuthentication == True and not force:
            return 

        # Open the login page
        driver = self.get_driver()

        try:
            driver.get(base_url)

            # find and click the login button(Note we need to either do this now, or we need to do it after we enter our credentials)
            login_button = driver.find_element(By.LINK_TEXT, 'Login') 
            login_button.click()

            # Find the email input field and enter the email address
            email_input = driver.find_element(By.ID, 'session_email') 
            email_input.send_keys(self.email)

            # Click the "Continue" button
            continue_button = driver.find_element(By.NAME, 'commit')  
            continue_button.click()

            # Find the password input field and enter the password
            password_input = driver.find_element(By.ID, 'session_password')  
            password_input.send_keys(self.password)

            # Click the "Sign In" button
            sign_in_button = driver.find_element(By.NAME, 'commit')
            sign_in_button.click()

            # wait for our cookies to arrive
            time.sleep(5) 

            # Capture all cookies after logging in
            self.authenticated_cookies = driver.get_cookies()
            self.save_cookies()

            self.check_authentication()
        except:
            logging.warn("Unable to login.  Please check your credentials or clear your cookies and try again.")

    def check_authentication(self):

        driver = self.get_driver()

        try:
            # Open the login page
            driver.get(profile_url)

            # if we arent properly logged in, we will redirect back to the homepage
            if driver.current_url != profile_url:
                self.username = None
                self.IsAuthenticated = False
                self.CheckedAuthentication = False
                logging.warn("Not properly authenticated.  Please check your credentials or clear your cookies and try again.")
                return

            profile_name = driver.find_element(By.XPATH, "//h1[contains(@class, 'is_Type') and contains(@class, 'font_heading')]")
            self.username = profile_name.text
            self.IsAuthenticated = True
            self.CheckedAuthentication = True

            logging.info(f"Authenticated as: {self.username}")

        except:
            self.username = None
            self.IsAuthenticated = False
            self.CheckedAuthentication = False
            logging.warn("Unable to verify authentication.  Please check your credentials or clear your cookies and try again.")


    def save_cookies(self):
        cookies_dict = {
            "cookies": self.authenticated_cookies
        }
        
        os.makedirs(os.path.dirname(self.cookies_file), exist_ok=True)
        with open(self.cookies_file, 'w') as file:
            json.dump(cookies_dict, file, indent=4)

    def load_cookies(self):
        if self.cookies_file is not None and os.path.exists(self.cookies_file):
            with open(self.cookies_file, 'r') as file:
                self.authenticated_cookies = json.load(file).get('cookies', [])

    def clear_cookies(self):
        self.email = None
        self.password = None
        self.authenticated_cookies = None
        self.username = None
        self.IsAuthenticated = False
        self.CheckedAuthentication = False

        if os.path.exists(self.cookies_file):
            os.remove(self.cookies_file)
        
        if self.driver:
            self.driver.delete_all_cookies()
            self.driver.get(base_url)

        logging.info("Cookies cleared.")