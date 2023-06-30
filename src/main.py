from utils import get_url, create_spreadsheets
from scraper import scrap_data


def main() -> None:
    """"""
    # jazzmaster
    url1 = get_url("jazzmaster gitara", "legnica")
    # jaguar
    url2 = get_url("jaguar gitara", "legnica")
    # stratocaster
    url3 = get_url("stratocaster gitara", "legnica")
    # telecaster
    url4 = get_url("telecaster gitara", "legnica")
    # amps
    url5 = get_url("wzmacniacz", "legnica")
    # Ibanez tube screamer
    url6 = get_url("ibanez tube screamer")
    # proco rat distortion
    url7 = get_url("proco rat distortion")
    # mxr micro amp
    url8 = get_url("mxr micro amp")
    # boss ds-1
    url9 = get_url("boss ds-1")
    # boss ds-2
    url10 = get_url("boss ds-2")

    dataFrames = [scrap_data(url) for url in [url1, url2, url3, url4, url5, url6, url7, url8, url9, url10]]
    sheetNames = ["Jazzmaster", "Jaguar", "Stratocaster", "Telecaster", "Amps", "Ibanez Tube Screamer",
                  "Proco Rat Distortion", "MXR Micro Amp", "Boss DS-1", "Boss DS-2"]

    create_spreadsheets(dataFrames, sheetNames, "guitars")

if __name__ == "__main__":
    main()
