or# OLX Scrapper

## Project Description

OLX Scraper is a Python-based application designed to scrape data from OLX, a popular classifieds website. The application provides a graphical user interface (GUI) created using PyQt5 to manage and view the scraped data, export it, and modify scraping settings. The project uses asynchronous web scraping to efficiently gather data.

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

## Running the Application

1. **Start the application**:
   ```bash
   python src/main.py
   ```

## Usage Example

### Manage Search Queries
Click on the 'View Search Queries' button to edit the scrape queries.

![image](https://github.com/kjanus03/olx-scrapper/assets/61358355/1c3d6de5-d9d9-4389-9063-1e909daa5477)
![image](https://github.com/kjanus03/olx-scrapper/assets/61358355/c8e4fac6-5cef-48f4-9c3c-7354483e6092)

### Scrape Data
Click on the 'Scrape Data' button to start scraping data based on the search queries.

![image](https://github.com/kjanus03/olx-scrapper/assets/61358355/e459ad0e-20c7-462d-8754-74cfebd3f14c)

### View Data
Click on the 'View Data' button to view the sortable table with the scraped data.

![image](https://github.com/kjanus03/olx-scrapper/assets/61358355/74538c80-409c-4a0c-94b3-0b9172f1fe9e)

### Export Data
Use the "Export Data" button to save the data in the tables. Pick the desired export format from a dropdown menu and specify the path to the output.

![image](https://github.com/kjanus03/olx-scrapper/assets/61358355/4731001a-3543-4830-9bf1-b969a70f36d6)

### Edit Settings
Use the "Settings" button to change output filename, page limit, and GUI dimensions. Toggle the Dark Mode checkbox in accordance with your preferences.

![image](https://github.com/kjanus03/olx-scrapper/assets/61358355/4a580b79-2ad6-4bd4-a632-ad491375dd5e)

## Project Structure

```
olx-scrapper
│
├── src
│   ├── Exporting
│   │   ├── ExportManager.py
│   │   ├── formatting.py
│   │   └── SpreadsheetManager.py
│   ├── GUI
│   │   ├── icons
│   │   ├── stylesheets
│   │   ├── ClickableDelegate.py
│   │   ├── Controller.py
│   │   ├── DataFrameModel.py
│   │   ├── ExportDialog.py
│   │   ├── ImageDialog.py
│   │   ├── MainWindow.py
│   │   ├── ScrapingHistoryDialog.py
│   │   ├── SearchQueriesDialog.py
│   │   └── SettingsDialog.py
│   ├── Resources
│   │   ├── config.json
│   │   ├── input_validation.py
│   │   ├── scraping_history.json
│   │   └── utils.py
│   ├── Scraping
│   │   ├── Scraper.py
│   │   └── URLBuilder.py
│   ├── Output
│   ├── requirements.txt
│   └── main.py
├── .gitignore 
└── README.md
```

## Requirements

- Python 3.9+
- aiohttp==3.9.0
- beautifulsoup4==4.11.1
- dicttoxml==1.7.16
- fpdf==1.7.2
- openpyxl==3.1.2
- pandas==1.4.4
- PyQt5==5.15.10
- PyQt5_sip==12.13.0
- Requests==2.32.3


## Documentation

The documentation for the project is available at the following links:
## Documentation

The documentation for the project is available at the following links:

- [ExportManager](https://kjanus03.github.io/olx-scrapper/Exporting/Exporting.ExportManager.html)
- [Formatting](https://kjanus03.github.io/olx-scrapper/Exporting/Exporting.formatting.html)
- [SpreadsheetManager](https://kjanus03.github.io/olx-scrapper/Exporting/Exporting.SpreadsheetManager.html)
- [ClickableDelegate](https://kjanus03.github.io/olx-scrapper/GUI/GUI.ClickableDelegate.html)
- [Controller](https://kjanus03.github.io/olx-scrapper/GUI/GUI.Controller.html)
- [DataFrameModel](https://kjanus03.github.io/olx-scrapper/GUI/GUI.DataFrameModel.html)
- [ExportDialog](https://kjanus03.github.io/olx-scrapper/GUI/GUI.ExportDialog.html)
- [ImageDialog](https://kjanus03.github.io/olx-scrapper/GUI/GUI.ImageDialog.html)
- [MainWindow](https://kjanus03.github.io/olx-scrapper/GUI/GUI.MainWindow.html)
- [ScrapingHistoryDialog](https://kjanus03.github.io/olx-scrapper/GUI/GUI.ScrapingHistoryDialog.html)
- [SearchQueriesDialog](https://kjanus03.github.io/olx-scrapper/GUI/GUI.SearchQueriesDialog.html)
- [SettingsDialog](https://kjanus03.github.io/olx-scrapper/GUI/GUI.SettingsDialog.html)
- [Input Validation](https://kjanus03.github.io/olx-scrapper/Resources/Resources.input_validation.html)
- [Utils](https://kjanus03.github.io/olx-scrapper/Resources/Resources.utils.html)
- [Scraper](https://kjanus03.github.io/olx-scrapper/Scraping/Scraping.Scraper.html)
- [URLBuilder](https://kjanus03.github.io/olx-scrapper/Scraping/Scraping.URLBuilder.html)
- [Main](https://kjanus03.github.io/olx-scrapper/main.html)



## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any features, bug fixes, or enhancements.
