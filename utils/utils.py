from bs4 import BeautifulSoup
from datetime import datetime
import logging
import os
import pandas as pd
from typing import List, Tuple, Union, Optional
import re
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
import time
from urllib.parse import urljoin


################################################################################################
# Helper functions for bulk downloading links from a page
################################################################################################

def create_logger(file_path, resource_name):
    '''
    Create a logger object for logging information and errors to a file and the console.

    Parameters:
    file_path: The file path where the log folder and accompanying files should be saved; should be same as the script's location.
    resource_name: The name of the logger - by convention, can choose the name of the script

    
    Returns:
    logger: A logger object for logging information and errors.
    
    '''
    # Get the current date and time for the log filename
    log_filename = f"{file_path}/logs/{resource_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    
    # Create a logger
    logger = logging.getLogger(resource_name)
    logger.setLevel(logging.INFO)
    
    # Create file handler which logs even debug messages
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.INFO)
    
    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    # Add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger


def set_up_soup(url, logger, dynamic=False, headless=True, file_types_to_wait=('all',), timeout=30, alt_header_required=False):
    '''
    Fetches the URL and parses it using BeautifulSoup, with optional dynamic content rendering.

    Parameters:
    url (str): The URL to fetch and parse.
    logger (Logger): Logger instance for logging information and errors.
    dynamic (bool): If True, uses Selenium to render the page before parsing (default is False).
    headless (bool): If True and dynamic is True, runs a headless browser, i.e. without launching a window (default is True).
    file_types_to_wait (tuple): Optional tuple of file types to check for the presence of before parsing HTML (default is ('all',); requires dynamic=True).
    timeout (int): How long to wait for the page to load (default is 30 seconds);
    alt_header_required (bool): If True, uses a different user-agent header to fetch the page (default is False). 
        NOTE: This should only be done if the site doesn't accept the default header and contains publicly available information.
        Be sure to double check the robots.txt and site TOS first!

    
    Returns:
    BeautifulSoup: Parsed HTML content of the page.
    '''
    if not dynamic:
        if alt_header_required:
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 MDI/ResearchCollector'}
        else:
            headers = {'user-agent': f'MDI Research Data Collector'}
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            logger.info(f"Successfully fetched and parsed URL: {url}")
            return soup
        except requests.RequestException as e:
            logger.error(f"Error fetching URL {url}: {e}")
            raise
    else:
        try:
        # Setup headless driver (won't open a new Chrome window)
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(options = chrome_options)
            driver.get(url)
            # If want to wait for a file of certain kind to load before parsing:
            if file_types_to_wait:
                element, file_type = find_element(driver, file_types_to_wait)
                if element: 
                    logger.info(f'Found {file_type} file - proceed to parse HTML')
                else:
                    logger.error(f'No element found containing the specified file types: {file_types_to_wait}')
            # If not waiting for a file to load, just parse the HTML:
            else:
                logger.info('No file types specified - proceed to parse HTML')
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            driver.quit()
            return soup
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            raise


def find_element(driver, file_types=('all',)):
    '''
    Find an element on the page that contains a link to a file with one of the specified file types.
    This function is useful when you want to download a file from a page but the link is not immediately visible.
    It will search for the link in the page and return the element containing it.

    Parameters:
    driver (WebDriver): The Selenium WebDriver object.
    file_types (tuple): A tuple of file extensions to filter the files to be downloaded. E.g. ['.zip', '.pdf']
        If ('all',) (default), will search for any hrefs (i.e. could be redirects to subpages)

    Returns:
    tuple: The element containing the file link and the file type found. (Otherwise None, None)
    '''
    if file_types == ('all',):
        selectors = ['a[href]']
        print(f'Selector is {selectors}')
    else:
        selectors = [f'a[href$="{file_type}"]' for file_type in file_types]
    for file_type, selector in zip(file_types, selectors):
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            if element:
                return element, file_type
        except Exception:
            continue  # Continue to the next selector if an exception occurs
    return None, None

def download_files(logger, soup, file_path, base_url, file_types=('.zip', '.pdf', '.docx'), get_subpages=False, is_subpage=False, timeout=30, alt_header_required=False):
    """
    Downloads files from the given BeautifulSoup object and saves them to the specified file path.
    This works best in situations where you want to grab all the files linked to on a webpage. 
    The function will find them, create their URLs for download, and save them to the specified file path.
    It will also optionally return any subpages linked to that can then themselves be searched for downloads.

    Args:
        logger (logging.Logger): Logger object for logging information and errors. Created with create_logger above
        soup (BeautifulSoup): BeautifulSoup object containing the parsed HTML. Create with set_up_soup above
        file_path (str): The directory path where the files will be saved.
        base_url (str): The base URL of the site being scraped to construct the full URL for each file.
        file_types (tuple, optional): A tuple of file extensions to filter the files to be downloaded. Defaults to ('.zip', '.pdf', '.docx').
                                      If you don't want to specify a suffix, input file_types=None
        get_subpages (bool, optional): If True, will also return a list of subpages linked to on the site. Defaults to False.
        is_subpage (bool, optional): If True, will alter how the file path is created to store download in a subdirectory within /data. Defaults to False. (For organizational purposes only.)
                                     Note that if is_subpage is True, the file_path should be the full file path including the subdirectory name.
        timeout (int, optional): How long to wait for GET requests to download files. Defaults to 30.
        alt_header_required (bool): If True, uses a different user-agent header to fetch the page (default is False). See set_up_soup function above for guidance on use of this!

    Returns:
        None if get_subpages is False, a list of subpages if True
    """
    if file_types:
        hrefs = [a.get('href') for a in soup.find_all('a') if a.get('href') and 
             (a.get('href').endswith(file_types) or a.get('type') == 'zip')]
    else:
        hrefs = [a.get('href') for a in soup.find_all('a') if a.get('href')]
    # Create a directory to save the downloaded files
    if not is_subpage:
        # If is_subpage is True, assumes the file path being fed in is the full file path which includes "data" in it. 
        file_path = f'{file_path}/data'
    os.makedirs(file_path, exist_ok=True)
    
    # Download each file
    for href in hrefs:
        try:
            # Construct the full URL
            file_url = urljoin(base_url, href)
            # Get the file name
            file_name = os.path.join(file_path, os.path.basename(href))
            
            # Check if the file already exists
            if os.path.exists(file_name):
                logger.info(f"File already exists: {file_name}")
                continue
            
            time.sleep(5)
            if alt_header_required:
                headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 UrbanInstitute/ResearchCollector'}
            else:
                headers = {'user-agent': f'Urban Institute Research Data Collector'}
            # Send a GET request to download the file
            file_response = requests.get(file_url, timeout=timeout, headers=headers)
            file_response.raise_for_status()  # Check if the request was successful
            
            # Save the file
            with open(file_name, 'wb') as file:
                file.write(file_response.content)
            logger.info(f"Successfully downloaded file: {file_name}")
        except requests.RequestException as e:
            logger.error(f"Error downloading file {href}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    if get_subpages:
        file_extension_pattern = re.compile(r'\.\w{3,5}$') # Matches any strings ending in a period followed by 3-5 letters
        hrefs = [a.get('href') for a in soup.find_all('a') if a.get('href') and not re.search(file_extension_pattern, a.get('href'))]
        # Create full URLs for subpages
        hrefs = [urljoin(base_url, href) for href in hrefs]
        logger.info(f"Found {len(hrefs)} subpages")
        # Write out subpages to .txt file
        with open(f'{file_path}/subpages.txt', 'w') as f:
            for href in hrefs:
                f.write(href + '\n')
        return hrefs
    return None



################################################################################################
# Helper functions for basic Selenium operations
################################################################################################

def set_up_driver(logger, headless=True, download_location=None):
    """
    Initializes a Selenium WebDriver object for use in scraping dynamic web pages.

    Inputs:
        logger (Logger): Logger object for logging information and errors. Created with create_logger above/
        headless (bool): If True, runs a headless browser, i.e. without launching a window (default is True).
        download_location (str): The directory path where files will be downloaded. If None, files will be downloaded to the Downloads folder.
    """


    try:
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        if download_location is not None:
            prefs = {
                "download.default_directory": os.path.join(os.getcwd(), download_location),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "profile.default_content_settings.popups": 0
            }
            chrome_options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options = chrome_options)
        logger.info("Successfully initialized driver")
    except Exception as e:
        logger.error(f"Failed to initialize driver: {e}")
        raise
    return driver


def click_button(identifier, driver, by=By.XPATH, timeout=15):   
    '''
    This function waits until a button is clickable and then clicks on it.
    You can either feed in the actual WebElement object (e.g. the result from `find_element`) as the identifier for the button, 
    or you can use a By object to identify its location (e.g. by its XPath, ID, etc.).


    Inputs:
        identifier (string): The Id, XPath, or actual WebElement of the element to be clicked on.
        driver (WebDriver): The Selenium WebDriver object.
        by (By object): How to identify the identifier (Options include By.XPATH, By.ID, By.Name and others).
            Make sure 'by' and 'identifier' correspond to one other as they are used as a tuple pair below.
        timeout (int): How long to wait for the object to be clickable

    Returns:
        None (just clicks on button)
    '''
    try:
        if isinstance(identifier, WebElement):
            element = identifier
        else:
            element_clickable = EC.element_to_be_clickable((by, identifier))
            element = WebDriverWait(driver, timeout=timeout).until(element_clickable)
        driver.execute_script("arguments[0].click();", element)
    except TimeoutException:
        print(f"Timeout: The button with identifier {identifier} was not clickable within {timeout} seconds.")
    except NoSuchElementException:
        print(f"Error: The button with identifier {identifier} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def select_dropdown(identifier, driver, by=By.XPATH, value=None, option=None, index=None, wait_for_visibility=False):
    '''
    This function clicks on the correct dropdown option in a dropdown object.
    It first waits until the element becomes selectable before locating the proper drop down menu. Then it selects the proper option.
    If the page doesn't load within 15 seconds, it will return a timeout message.

    Inputs:
        identifier (string): This is the HTML 'value' of the dropdown menu to be selected, 
            found through inspecting the web page.
        driver (WebDriver): The Selenium WebDriver object.
        by (By object): How to identify the identifier (Options include By.XPATH, By.ID, By.Name and others).
        value (string): The value to select from the dropdown menu.
        option (string): The visible text of the option to select from the dropdown menu.
        index (int): If index is not None, function assumes we want to select an option by its index instead of by specific value. 
            In this case, should specify that value = None.
        wait_for_visibility (bool): If True, waits for the element to be visible before checking for clickability.
    
    Returns:
        boolean (whether or not the selection was successful)
    '''
    try:
        if wait_for_visibility:
            element_visible = EC.visibility_of_element_located((by, identifier))
            WebDriverWait(driver, timeout=15).until(element_visible)
        
        element_clickable = EC.element_to_be_clickable((by, identifier))
        element = WebDriverWait(driver, timeout=15).until(element_clickable)
        select = Select(element)
        if value is not None:
            select.select_by_value(value)
        elif option is not None:
            select.select_by_visible_text(option)
        else:
            select.select_by_index(index)
        return True
    except TimeoutException:
        print(f"Timeout: The menu with identifier {identifier} was not clickable within 15 seconds.")
    except NoSuchElementException:
        print(f"Error: The menu with identifier {identifier} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return False

def enter_text(identifier, text, driver, by=By.XPATH):
    """
    This function enters text into a text box object on a web page.
    It first waits until the element becomes selectable before locating the text box. Then it enters the text.
    If the page doesn't load within 15 seconds, it will return a timeout message.

    Inputs:
        identifier (string): This is the HTML 'value' of the text box to be selected,
            found through inspecting the web page.
        text (string): The text to enter into the text box.
        driver (WebDriver): The Selenium WebDriver object.
        by (By object): How to identify the identifier (Options include By.XPATH, By.ID, By.Name and others).
    
    Returns:
        boolean (whether or not the selection was successful)
    """
    try:
        element_clickable = EC.element_to_be_clickable((by, identifier))
        element = WebDriverWait(driver, timeout=15).until(element_clickable)
        # Clear the text from the text box (zip code wasn't overwriting)
        element.clear()
        element.send_keys(text)
    except TimeoutException:
        print(f"Timeout: The text box with identifier {identifier} was not clickable within 15 seconds.")
    except NoSuchElementException:
        print(f"Error: The text box with identifier {identifier} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_href(identifier, driver, by=By.XPATH):
    '''
    Get a hyperlink from an element that appears on a dynamic webpage.
    '''
    element_clickable = EC.element_to_be_clickable((by, identifier))
    element = WebDriverWait(driver, timeout=15).until(element_clickable)
    return element.get_attribute('href')



def check_valid_urls(
    urls: Union[List[str], pd.DataFrame, str],
    url_column: Optional[str] = None,
    export: bool = False,
    export_path: Optional[str] = None
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Check the validity of a list of URLs.

    Parameters:
        urls (list, DataFrame, or str): List of URLs, a DataFrame containing URLs, or a file path (CSV/Excel).
        url_column (str, optional): Column name containing URLs if a DataFrame or file is provided.
        export (bool, optional): If True, writes the valid and invalid links to a file.
        export_path (str, optional): Path to export the results. Required if export is True.

    Returns:
        tuple: (valid_links, invalid_links)
            valid_links: List of valid URLs.
            invalid_links: List of tuples (URL, error/status).

    Example usage:
        check_valid_urls(['https://www.google.com', 'https://invalid.url'], export=True, export_path='results.txt')
        check_valid_urls('my_urls.xlsx', url_column='url')
    """
    # Load URLs from different input types
    if isinstance(urls, str):
        if urls.endswith('.csv'):
            df = pd.read_csv(urls)
        elif urls.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(urls)
        else:
            raise ValueError("Unsupported file type. Use CSV or Excel.")
        if not url_column:
            raise ValueError("Please specify the url_column when providing a file path or DataFrame.")
        links = df[url_column].dropna().tolist()
    elif isinstance(urls, pd.DataFrame):
        if not url_column:
            raise ValueError("Please specify the url_column when providing a DataFrame.")
        links = urls[url_column].dropna().tolist()
    elif isinstance(urls, list):
        links = [u for u in urls if pd.notna(u)]
    else:
        raise ValueError("Input must be a list of URLs, a DataFrame, or a file path.")

    valid_links = []
    invalid_links = []

    for link in links:
        try:
            print(f"Checking link: {link}")
            response = requests.head(link, allow_redirects=True, timeout=10)
            if response.status_code == 200:
                valid_links.append(link)
            else:
                invalid_links.append((link, str(response.status_code)))
        except requests.RequestException as e:
            invalid_links.append((link, str(e)))

    print("Valid Links:")
    for valid_link in valid_links:
        print(valid_link)

    print("\nInvalid Links:")
    for invalid_link, error in invalid_links:
        print(f"{invalid_link} - {error}")

    if export:
        if not export_path:
            raise ValueError("Please specify export_path if export is True.")
        with open(export_path, "w") as file:
            file.write("Valid Links:\n")
            for link in valid_links:
                file.write(link + "\n")
            file.write("\nInvalid Links:\n")
            for link, error in invalid_links:
                file.write(f"{link} - {error}\n")

    return valid_links, invalid_links
