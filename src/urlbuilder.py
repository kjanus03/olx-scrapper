from dataclasses import dataclass


@dataclass
class URLBuilder:
    """Builds a URL for the given item query, given a city and distance.
    The city should be in Poland, e.g. 'legnica', 'wroclaw', 'zagan'.
    The distance is in kilometers. """
    item_query: str
    city: str = None
    distance: int = 100

    def build_url(self) -> str:
        """
        Builds a URL for the given item query, city, and distance.
        :return: URL string
        """
        if self.city is None:
            city = "oferty"
            distance_string = ""
        else:
            city = self.city.replace(" ", "-")
            distance_string = f"search%5Bdist%5D={self.distance}&"
        item_query = self.item_query.replace(" ", "-")
        url = f"https://www.olx.pl/{city}/q-monitor {item_query}/?{distance_string}search%5Border%5D=created_at%3Adesc"
        return url

    def generate_data_key(self) -> str:
        """Returns a key for the data frame that will be created from the scraped data."""
        key = f"{self.item_query.capitalize()}"
        if self.city:
            key += f" - {self.city.capitalize()}"
        return key
