import os, time
import pandas as pd
from io import StringIO
from utils import utils
from selenium.webdriver.common.by import By

# Specify folder path and file name for saving out data and informative logging
file_path = "pihlstrom"
resource_name =  "arts-data-profile-series"
# URL to scrape
url = 'https://www.arts.gov/impact/research/arts-data-profile-series'
# File types to download from URL
file_types = ('.zip')

if __name__ == '__main__':
    # Create logger
    logger = utils.create_logger(file_path=file_path, resource_name=resource_name)
    driver = utils.set_up_driver(logger)

    # Set up soup object to parse text; can toggle dynamic=True, headless=False options to see Selenium functionality
    soup = utils.set_up_soup(url=url, logger=logger)

    for i in range(2):
        driver.get(url + f"?page={i+1}")
        articles = driver.find_elements(By.TAG_NAME, "article")
        print(len(articles))

        for index, article in enumerate(articles, start=1):
            try:
                link_element = article.find_element(By.XPATH, './/a')
                href = link_element.get_attribute("href")

                utils.download_files(logger, utils.set_up_soup(url=href, logger=logger), os.path.join(file_path, resource_name), href, file_types = (".zip",".xlsx",".pdf"))
                print(f"Article {index}: {href}")
            except:
                print(f"Article {index}: No link found")

    # Close WebDriver
    driver.quit()
