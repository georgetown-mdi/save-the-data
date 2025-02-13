import os, time
import pandas as pd
from io import StringIO
from utils import utils
from selenium.webdriver.common.by import By

# Specify folder path and file name for saving out data and informative logging
file_path = "scraping-pihlstrom"
resource_name =  "bjs-fed-prison-mortality"
# URL to scrape
url = 'https://bjs.ojp.gov/taxonomy/term/deaths-custody'
# File types to download from URL
file_types = ('.zip')

if __name__ == '__main__':
    # Create logger
    logger = utils.create_logger(file_path=file_path, resource_name=resource_name)
    driver = utils.set_up_driver(logger)

    # Set up soup object to parse text; can toggle dynamic=True, headless=False options to see Selenium functionality
    soup = utils.set_up_soup(url=url, logger=logger)

    for page_num in range(6):

        driver.get(url + f"?page={page_num}")
        articles = driver.find_elements(By.XPATH, '//*[@id="block-ojp-content"]/article')

        for index, article in enumerate(articles, start=1):
            try:
                link_element = article.find_element(By.XPATH, './/a')
                href = link_element.get_attribute("href")

                utils.download_files(logger, utils.set_up_soup(url=href, logger=logger), os.path.join(file_path, resource_name), href, file_types = (".zip"))

            except:
                print(f"Article {index}: No link found")
        

    # Close WebDriver
    driver.quit()





