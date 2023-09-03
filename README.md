# Anime Scraping Program

This Python program is designed for scraping data from an anime website, processing it, and storing it in a MySQL database. It utilizes web scraping techniques using Selenium and BeautifulSoup, manages a MySQL database for storing anime information and episodes, and transfers files via FTP.

## Features

- Scrapes anime information such as title, description, genres, and episode data.
- Downloads images and thumbnails associated with the anime.
- Stores anime data in a MySQL database.
- Downloads and stores anime episodes in the database.
- Provides a configurable interval for regular data scraping.

## Prerequisites

Before running the program, ensure you have the following prerequisites:

- Python 3.x installed.
- Required Python packages installed (use `pip install -r requirements.txt`).
- MySQL server and database set up.
- Chrome WebDriver installed and path configured.
- FTP server access details.

## Installation

1. Clone this repository to your local machine:

```bash
git clone https://github.com/yourusername/anime-scraping-program.git
```
2. Navigate to the project directory
 ```bash
  cd anime-scraping-program'
  ```
3. Create a virtual environment (optional but recommended)
```bash
   python -m venv venv
```
4. Activate the virtual environment
5. Install the required Python packages
```bash
pip install -r requirements.txt
```
6. Create a .env file in the project root directory with your credentials and configuration options. You can use the provided .env.example as a template.

## Configuration

You can configure the program by editing the .env file in the project root directory. The file contains settings for the database, FTP, WebDriver, and other options.

## Error Handling
The program includes basic error handling to handle exceptions during scraping. Any errors encountered will be logged, and the program will continue running.

## Contributing
Contributions are welcome! If you have suggestions or improvements, please open an issue or submit a pull request.
