# data-preservation-public


## Set-up:
- **GitHub:** 
    - We use GitHub to collaborate across many different data preservation tasks. If you are new to GitHub, check out Urban's guide on [basic workflow](https://ui-research.github.io/reproducibility-at-urban/git-workflow.html).
    - When you start on a task, you should create a new branch named based on the task you're taking on and push any changes to that branch. When ready, you can open a Pull Request and tag a senior collaborator as a reviewer. Please also feel free to open new issues to either track your progress on a task or flag general obstacles to the team.
- **Folder structure:**
    - For organizational purposes, we recommend creating separate folders for different tasks or domains, with a clear naming structure, such as [Jenny Bryan's naming convention](https://www2.stat.duke.edu/~rcs46/lectures_2015/01-markdown-git/slides/naming-slides/naming-slides.pdf).
- **Logging:** For Python scraping, we use the `logging` package to output informative INFO, WARNING, and ERROR messages into .log files. Each log file will contain the name of the site being scraped and the date the scraping job was run so that files can be tracked. See more info on logging in the [documentation here](https://docs.python.org/3/library/logging.html). **Log files are not pushed to GitHub.**
- **Reusable code:**
    - Any functions that are widely useful across scrapers (e.g. Selenium utilities like clicking a button, logger file creation, etc.) can be stored within `utils\utils.py`.
    - Import these functions into your code by adding this line in your Python code: `from utils import utils`
    - To run your script without error, you will need to use this command line syntax from the root directory so that the utilities module can be recognized and imported. (The script name will change but should use the period-based format of a module.)

      ```python -m folder-where-code-lives.script-name```
- **Programming languages:** You can feel free to use R or Python scripts, depending on your preference. For any dynamic actions that require Selenium, Python is strongly recommended.
- **Virtual environments:**
    - **Python:** We use `venv` for our Python virtual environment. See [this guide](https://ui-research.github.io/reproducibility-at-urban/virtual-environments.html) for how to configure your own. If you install any new packages, please add them to the `requirements.txt` file and push to GitHub so that others can reproduce your code.
    - **R** We use `renv` for our R virtual environment. See the same link above for guidance on setup. 

## Computing Power:
- For very long or intensive jobs, it may make sense to use additional compute power, such as a remote server, cloud resources, or parallel processing. Please reach out to a senior collaborator if you think you need additional resources.

## Instructions on documentation:
- We want to be able to say exactly how and when information was acquired. The log file names and contents should be sufficient for this, and all code should be commented clearly so that others can follow.
- For scraping requests, **anytime documentation can be downloaded alongside data, please do so**. This is impractical for large-scale crawling requests, but when possible, we want to be able to upload metadata, data dictionaries, etc. to the data catalog alongside any information we download.
- What you've scraped should be stored in a running metadata document. This may include the following:
    - Name of Dataset or Site Scraped
    - Short Description of the Data:
    - Date Scraped (final date if over period of time)
    - Date Modified (if editing an existing task)
    - URL(s) where data was scraped from
    - (Where applicable) Unit of Analysis (e.g. individual, household, business, etc.)
    - Geographic Level of Data
    - Time Period of Data
    - Is the data disaggregated by race/ethnicity?
    - Name of Documentation File(s) (e.g., Codebook, Data Dictionary, etc.)
    - (Optional): Name(s) of Data Collector and Data Requestor
    - Link to Box folder where data lives
    - What file types did you scrape?
    - Are any files larger than 5GB?
    - Any other questions/concerns for users of this data?
  
## Suggested approaches by type of web scraping task:
**For large scale web-crawling or bulk downloads of everything from a single page:**
- We generally want to download all links ending in a certain file type (`.pdf, .xlsx, .zip`) that are found in `href` tags within `a` tags on a page.
- These links will often be indirect, so using the `urljoin` module from `urllib` is recommended for constructing the full URL for download. See the illustrative examples section below.
- `utils.download_files` does exactly this!

**For interactive websites**:
- We have many existing utility functions in Selenium for clicking buttons, entering text in boxes, selecting dropdowns, etc. These will be useful for navigating lots of menu options to get to data download options pretty easily.
- Use explicit waits using `WebDriverWait` to wait only until elements become clickable (see Python User Group tutorial [here](https://ui-research.github.io/python-at-urban/content/web-scraping-dynamic.html) for more information on what a `Wait` is in a web scraping context.
- Start by writing code to successfully navigate the menu for one option, *then* put that code into a function that can be iterated over all of the menu options you want.

**Other suggestions**:
  - Make sure you include in your code some logic to check if a file has already been downloaded so that you can restart a scraper from where you left off if the site hangs or the code times out. (`utils.download_files` does this!)
  - For jobs that crawl hundreds of pages, storing a text file of already-visited URLs is similarly useful so that you can skip over the pages you've already visited.
  - Use `try/catch` logic to store useful info in .log files! Again, see the utility functions for good examples of this.


## Closing Out:
When finished with a task, please make sure the following information is stored:
- data is added to a `data` subfolder in the task folder
- log files are added to a `logs` subfolder in the task folder
- Archive the page on the Wayback Machine and add a bookmark to the archived URL. If the site is too complicated to be archived properly, you can save an HTML snapshot to the folder instead.
- A few sanity checks to make sure you've scraped everything you think you should. A few ideas include:
    - Do the number of `hrefs` found by your scraper equal the number of files you have downloaded?
    - Does your log file have any warning or error messages?
    - Do you have coverage across all the geographies/years that you were asked to collect?
    - For larger crawling jobs, if there is a list of "known" relevant resources/reports/data files, try searching for a few to make sure you grabbed them.
