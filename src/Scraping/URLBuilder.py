from dataclasses import dataclass


@dataclass
class URLBuilder:
    item_query: str
    city: str = None
    distance: int = 100

    def build_url(self, page: int = 1) -> str:
        if self.city is None:
            city = "oferty"
            distance_string = ""
        else:
            city = self.city.replace(" ", "-")
            distance_string = f"search%5Bdist%5D={self.distance}&"
        item_query = self.item_query.replace(" ", "-")
        if page > 1:
            url = f"https://www.olx.pl/{city}/q-{item_query}/?page={page}&{distance_string}search%5Border%5D=created_at%3Adesc"
        else:
            url = f"https://www.olx.pl/{city}/q-{item_query}/?{distance_string}search%5Border%5D=created_at%3Adesc"
        print(url)
        return url

    def generate_data_key(self) -> str:
        key = f"{self.item_query.capitalize()}"
        if self.city:
            key += f" - {self.city.capitalize()}"
        if self.distance:
            key += f" - {self.distance}km"
        return key
