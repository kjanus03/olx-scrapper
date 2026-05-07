# OLX Scrapper

<img width="1601" height="936" alt="image" src="https://github.com/user-attachments/assets/938a01f9-5146-4b1e-9c75-a26c7b4617eb" />

## Project Description

OLX Scraper is a Python-based application designed to scrape data from OLX, a popular classifieds website. Provides a graphical user interface (GUI) created with PyQt5 to manage and view the scraped data, export it, and modify scraping settings. The project uses asynchronous web scraping to efficiently gather data.

## Features

- **Data Scraing**: Scrape data from OLX based on user-defined search queries.
- **Data Viewing**: View the scraped data in a sortable table within the GUI.
- **Data Exporting**: Export the scraped data to various formats including CSV.
- **Search Query Management**: Add, edit, and delete search queries.
- **Monitoring Scraping History**: View a history of all past scraping sessions with appropriate timestamps.
- **Settings Management:**: Make changes to options of the Scraper such as page limit and GUI dimensions through a dedicated Settings Window.
- **Dark Mode**: Toggle dark mode for a comfortable viewing experience.

## Installation 

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kjanus03/olx-scrapper.git
   cd olx-scrapper

   ```
  
2. **Create cirtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application!**
   ```bash
   python -m src/main.py
   ```

## Project Overview

### Scraping
The scraping functionality is managed by the Scraper class located in src/Scraping/Scraper.py. This class handles the retrieval of data from OLX using asynchronous web scraping techniques, ensuring efficient and fast data collection. The search queries are defined in the config.json file located in the Resources directory.

### Exporting
Exporting the scraped data is managed by the ExportManager class in src/Exporting/ExportManager.py. Users can export data to various formats such as CSV or Excel spreadsheets.

### GUI
The graphical user interface is created using PyQt5 and its elements are located in the src/GUI directory.

### Resources
The Resources directory contains essential configuration files and utility scripts:

- **config.json**: Configuration file for search queries and application settings.
- **scraping_history.json**: JSON file storing the history of scraping sessions.
- **input_validation.py**: Utility functions for validating user inputs in the menu.

## Usage Example

### Manage Search Queries
Click on the 'Search Queries' button to edit the scrape queries.

<img width="1603" height="937" alt="image" src="https://github.com/user-attachments/assets/ed024ce1-1831-4886-8b8c-291e3e5469b3" />
<img width="1604" height="942" alt="image" src="https://github.com/user-attachments/assets/c4de479b-bcce-4efe-b968-270074032da6" />

### Scrape Data
Click on the 'Scrape Data' button to start scraping data based on the search queries.

<img width="1607" height="938" alt="image" src="https://github.com/user-attachments/assets/4cf37371-2ef3-49dd-8e9b-c196b87c2279" />

### View Data
View the scrapped data in sortable tables.

<img width="1597" height="934" alt="image" src="https://github.com/user-attachments/assets/463ece32-d230-4c2b-8f32-75733197bf96" />

### Export Data
Use the "Export" button to save the data in the tables. Pick the desired export format from a dropdown menu and specify the path to the output.

<img width="540" height="790" alt="image" src="https://github.com/user-attachments/assets/08928768-bb0b-481e-9d02-c9c549be74f4" />

### Edit Settings
Use the "Settings" button to change output filename, page limit, and GUI dimensions. Toggle the Dark Mode checkbox in accordance with your preferences.

<img width="512" height="771" alt="image" src="https://github.com/user-attachments/assets/d91f8652-68dd-4ac8-9179-75ff41050f1c" />

## Project Structure

```
olx-scrapper
├── README.md
├── generate_tree.py
├── requirements.txt
├── src/
│   ├── .cache
│   ├── generate_docs.py
│   ├── main.py
│   ├── requirements.txt
│   ├── Exporting/
│   │   ├── ExportManager.py
│   │   ├── SpreadsheetManager.py
│   │   └── formatting.py
│   ├── GUI/
│   │   ├── ClickableDelegate.py
│   │   ├── Controller.py
│   │   ├── DataFrameModel.py
│   │   ├── ExportDialog.py
│   │   ├── ImageDialog.py
│   │   ├── MainWindow.py
│   │   ├── ScrapingHistoryDialog.py
│   │   ├── SearchQueriesDialog.py
│   │   ├── SettingsDialog.py
│   │   ├── icons/
│   │   │   ├── add_icon.png
│   │   │   ├── remove_icon.png
│   │   │   ├── scraper_icon.png
│   │   │   ├── svg/
│   │   ├── stylesheets/
│   │   │   ├── modern_dark.qss
│   │   │   └── modern_light.qss
│   │   ├── widgets/
│   │   │   ├── CellDelegates.py
│   │   │   ├── EmptyState.py
│   │   │   ├── IconProvider.py
│   │   │   ├── SearchBar.py
│   │   │   ├── Toast.py
│   │   │   └── __init__.py
│   ├── Output/
│   │   ├── scraped_data.pdf
│   │   └── scraped_data.xlsx
│   ├── Resources/
│   │   ├── config.json
│   │   ├── input_validation.py
│   │   ├── scraping_history.json
│   │   ├── seen_listings.json
│   │   └── utils.py
│   ├── Scraping/
│   │   ├── Scraper.py
│   │   └── URLBuilder.py
```

## Requirements

- aiohttp==3.9.0
- aiosignal==1.4.0
- attrs==26.1.0
- beautifulsoup4==4.11.1
- certifi==2026.4.22
- charset-normalizer==3.4.7
- dicttoxml==1.7.16
- et_xmlfile==2.0.0
- fpdf==1.7.2
- frozenlist==1.8.0
- idna==3.13
- multidict==6.7.1
- numpy==2.4.4
- openpyxl==3.1.2
- pandas==3.0.2
- propcache==0.4.1
- PyQt5==5.15.10
- PyQt5-Qt5==5.15.2
- PyQt5_sip==12.13.0
- python-dateutil==2.9.0.post0
- requests==2.32.3
- setuptools==69.5.1
- six==1.17.0
- soupsieve==2.8.3
- tzdata==2026.2
- urllib3==2.6.3
- yarl==1.23.0

## Documentation

The documentation for the project is available at the following links:

- [ExportManager](https://kjanus03.github.io/olx-scrapper/Exporting.ExportManager.html)
- [Formatting](https://kjanus03.github.io/olx-scrapper/Exporting.formatting.html)
- [SpreadsheetManager](https://kjanus03.github.io/olx-scrapper/Exporting.SpreadsheetManager.html)
- [ClickableDelegate](https://kjanus03.github.io/olx-scrapper/GUI.ClickableDelegate.html)
- [Controller](https://kjanus03.github.io/olx-scrapper/GUI.Controller.html)
- [DataFrameModel](https://kjanus03.github.io/olx-scrapper/GUI.DataFrameModel.html)
- [ExportDialog](https://kjanus03.github.io/olx-scrapper/GUI.ExportDialog.html)
- [ImageDialog](https://kjanus03.github.io/olx-scrapper/GUI.ImageDialog.html)
- [MainWindow](https://kjanus03.github.io/olx-scrapper/GUI.MainWindow.html)
- [ScrapingHistoryDialog](https://kjanus03.github.io/olx-scrapper/GUI.ScrapingHistoryDialog.html)
- [SearchQueriesDialog](https://kjanus03.github.io/olx-scrapper/GUI.SearchQueriesDialog.html)
- [SettingsDialog](https://kjanus03.github.io/olx-scrapper/GUI.SettingsDialog.html)
- [Input Validation](https://kjanus03.github.io/olx-scrapper/Resources.input_validation.html)
- [Utils](https://kjanus03.github.io/olx-scrapper/Resources.utils.html)
- [Scraper](https://kjanus03.github.io/olx-scrapper/Scraping.Scraper.html)
- [URLBuilder](https://kjanus03.github.io/olx-scrapper/Scraping.URLBuilder.html)
- [Main](https://kjanus03.github.io/olx-scrapper/main.html)



## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any features, bug fixes, or enhancements.
