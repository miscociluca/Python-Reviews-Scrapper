# -*- coding: utf-8 -*-
from googlemaps import GoogleMapsScraper
from facebook import FacebookScraper
from opentable import OpenTableScraper
from tripadvisor import TripAdvisorScraper
from datetime import datetime, timedelta
import argparse
import csv

HEADERS = ['UserName','Date', 'Post', 'IsResponded', 'Response','PostUrl']

def csv_writer(source,path='data/', outfile='reviews.csv',):
    targetfile = open(path + outfile, mode='w', encoding='utf-8', newline='\n')
    writer = csv.writer(targetfile, quoting=csv.QUOTE_MINIMAL)
    h = HEADERS
    writer.writerow(h)
    return writer


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reviews Response Scrapers.')
    required_parser = parser.add_argument_group("required arguments")
    required_parser.add_argument('-source', help="The Source of the Page(Facebook,Google,OpenTable,TripAdvisor,Yelp)", required=True)
    required_parser.add_argument('-page', help="The Url of the Page you want to scrape", required=True)
    parser.add_argument('-N', type=int, default=100, help='Number of reviews to scrape FOR (Google,Facebook) ONLY!') 
    parser.add_argument('-place', dest='place', action='store_true', help='Scrape place metadata')
    parser.add_argument('-debug', dest='debug', action='store_true', help='Run scraper using browser graphical interface')
    parser.set_defaults(place=False, debug=False)

    args = parser.parse_args()
    
    if args.source == 'Google':
        writer = csv_writer('Google')

        with GoogleMapsScraper(debug=args.debug) as scraper:
            
            url = args.page
            error = scraper.sort_by_date(url)
            if error == 0:
                n = 0
                while n < args.N:
                    reviews = scraper.get_reviews(n)

                    for r in reviews:
                        row_data = list(r.values())
                        writer.writerow(row_data)

                    n += len(reviews)
                                
    if args.source == 'Facebook':
        writer = csv_writer('Facebook')
        with FacebookScraper(debug=args.debug) as scraper:
            
            url = args.page
            reviews = scraper.get_reviews(url,args.N)

            for r in reviews:
                row_data = list(r.values())
                writer.writerow(row_data)
    
    if args.source == 'OpenTable':
        writer = csv_writer('OpenTable')
        with OpenTableScraper(debug=args.debug) as scraper:
            
            url = args.page
            reviews = scraper.get_reviews(url,args.N)
            for r in reviews:
                for rev in r:
                    row_data = list(rev.values())
                    writer.writerow(row_data)

    if args.source == 'TripAdvisor':
        writer = csv_writer('TripAdvisor')
        with TripAdvisorScraper(debug=args.debug) as scraper:
            
            url = args.page
            reviews = scraper.get_reviews(url,args.N)
            for r in reviews:
                for rev in r:
                    row_data = list(rev.values())
                    writer.writerow(row_data)






