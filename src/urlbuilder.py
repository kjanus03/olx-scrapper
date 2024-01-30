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
        if self.city is None:
            city = "oferty"
            distance_string = ""
        else:
            city = self.city.replace(" ", "-")
            distance_string = f"search%5Bdist%5D={self.distance}&"
        item_query = self.item_query.replace(" ", "-")
        url = f"https://www.olx.pl/{city}/q-{item_query}/?{distance_string}search%5Border%5D=created_at%3Adesc"
        return url
