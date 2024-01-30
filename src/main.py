from scraper import Scraper
from urlbuilder import URLBuilder  # Import your URLBuilder class


def main() -> None:
    # Define the guitars and amps to search for as a list of URLBuilder instances
    search_items = [
        URLBuilder(item_query="wzmacniacz gitarowy", city="legnica", distance=100),
        URLBuilder(item_query="kolumna gitarowa", city="legnica", distance=100),
        URLBuilder(item_query="wzmacniacz gitarowy", city="zagan", distance=100),
        URLBuilder(item_query="kolumna gitarowa", city="zagan", distance=100),
        URLBuilder(item_query="orange gitarowy", city="legnica", distance=100),
        URLBuilder("mxr micro amp"),
        URLBuilder("boss chorus"),
        URLBuilder("electro-harmonix small clone"),
        URLBuilder("mxr chorus"),
        URLBuilder("electro harmonix holy grail reverb"),
        URLBuilder("boss reverb"),
        URLBuilder("tc electronic hall of fame reverb"),
    ]

    # Create a single Scraper instance
    scraper_instance = Scraper(search_items)

    # Scrape data and create data frames
    scraper_instance.scrape_data()

    # Create spreadsheets
    scraper_instance.create_spreadsheets("upgrade", format_column_widths=True)


if __name__ == "__main__":
    main()
