import os
import pandas as pd
from io import StringIO
from utils import utils

# Specify folder path and file name for saving out data and informative logging
file_path = "00_scraping-example"
resource_name =  "scrape-ed-express-sample"
# URL to scrape
url = 'https://eddataexpress.ed.gov/download/data-library?page=23'
# File types to download from URL
file_types = ('.zip')

if __name__ == '__main__':
    # Create logger
    logger = utils.create_logger(file_path=file_path, resource_name=resource_name)
    # Set up soup object to parse text; can toggle dynamic=True, headless=False options to see Selenium functionality
    soup = utils.set_up_soup(url=url, logger=logger)
    # Download all files linked in `href` tags that end in `file_types`
    utils.download_files(logger=logger, soup=soup, file_path=file_path, base_url=url, file_types=file_types)

    # BONUS: Download the metadata table on the website and save it as a CSV
    metadata = pd.DataFrame()
    try:
        table = soup.find('table')
        html_string = str(table)
        # Read in the HTML table as a pandas data frame; 
        # in this case, pandas is easier to use than BeautifulSoup because the table is already so nicely formatted, but both can work!
        df = pd.read_html(StringIO(html_string))[0]
        # Change the Zip File column from "Download" text to the actual URL
        zip_file_downloads = table.find_all('a', href=True)
        zip_file_downloads = [entry['href'] for entry in zip_file_downloads]
        df['Zip File'] = zip_file_downloads
        metadata = pd.concat([metadata, df])
        # Save out the metadata table
        data_path = os.path.join(file_path, 'data')
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        logger.info(f"Saving metadata to {data_path}/ed_data_express_metadata.csv")
        metadata.to_csv(f'{data_path}/ed_data_express_metadata.csv', index=False)
    except Exception as e:
        logger.error(f"Failed to get metadata from soup into dataframe: {e}")