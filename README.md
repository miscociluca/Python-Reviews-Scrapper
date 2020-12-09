# Reviews Scraper
Scraper of Google Maps,Facebook,OpenTable,TripAdvisor reviews.



## Installation
Follow these steps to use the scraper:
- Download Chromedrive from [here](https://chromedriver.storage.googleapis.com/index.html?path=2.45/).
- Install Python packages from requirements file, either using pip, conda or virtualenv:

        conda create --name scraping python=3.6 --file requirements.txt

**Note**: Python >= 3.6 is required.

## Usage
The scraper needs three main parameters as input:
- `-source`: The Source of the Page(Facebook,Google,OpenTable,TripAdvisor,Yelp)
- `-page`: The Url of the Page you want to scrape
- `-N`: number of reviews to retrieve, starting from the most recent (default: 100)

Example:

  `python scraper.py -source Google -page https://www.google.com/maps/place/Americana+Bar/@53.3235271,-6.2529374,17z/data=!4m7!3m6!1s0x0:0xa32d2b7ae6ef6887!8m2!3d53.3235271!4d-6.2507487!9m1!1b1-N 50`


For a basic description of logic and approach about this software development, have a look at the [Medium post](https://towardsdatascience.com/scraping-google-maps-reviews-in-python-2b153c655fc2)
