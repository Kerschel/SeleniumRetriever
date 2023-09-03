import requests
from time import sleep
import mysql.connector
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as soup
import re
import ftplib
from decouple import Config

config = Config()

# Database configuration
DB_HOST = config.get('DB_HOST')
DB_USER = config.get('DB_USER')
DB_PASSWORD = config.get('DB_PASSWORD')
DB_NAME = config.get('DB_NAME')

# FTP configuration
FTP_HOST = config.get('FTP_HOST')
FTP_USER = config.get('FTP_USER')
FTP_PASSWORD = config.get('FTP_PASSWORD')

# Chrome WebDriver configuration
CHROME_DRIVER_LOCATION = config.get('CHROME_DRIVER_LOCATION')
CHROME_BINARY_LOCATION = config.get('CHROME_BINARY_LOCATION')

# Other configuration options
DIRECTORY = config.get('DIRECTORY')
IMAGE_SITE = config.get('IMAGE_SITE')
THUMB_SERVER_PATH = config.get('THUMB_SERVER_PATH')
THUMB_DIRECT = config.get('THUMB_DIRECT')

DB_CONFIG = {
    "host": DB_HOST,
    "user": DB_USER,
    "passwd": DB_PASSWORD,
    "database": DB_NAME
}

DB = mysql.connector.connect(**DB_CONFIG)
CURSOR = DB.cursor(buffered=True)

# Initialize FTP session
import ftplib
SESSION = ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASSWORD)

# Set up Chrome WebDriver options
CHROME_OPTIONS = Options()
CHROME_OPTIONS.binary_location = CHROME_BINARY_LOCATION
CHROME_OPTIONS.headless = True
CHROME_OPTIONS.add_argument("--window-size=1920,1200")
DRIVER = webdriver.Chrome(executable_path=CHROME_DRIVER_LOCATION, options=CHROME_OPTIONS)


# Initialize MySQL database connection
DB = mysql.connector.connect(**DB_CONFIG)
CURSOR = DB.cursor(buffered=True)

class Scrape:
    def slugify(self, s):
        s = s.lower().strip()
        s = re.sub(r'[^\w\s-]', '', s)
        s = re.sub(r'[\s_-]+', '-', s)
        s = re.sub(r'^-+|-+$', '', s)
        return s

    def download_image(self, image_url, slug):
        extension = image_url.split('/')[-1].split('.')[-1].split("?")[0]
        r = requests.get(image_url, allow_redirects=True)
        filename = f"{slug}.{extension}"
        open(f"{DIRECTORY}{slug}.{extension}", 'wb').write(r.content)
        file = open(f"{DIRECTORY}{slug}.{extension}", 'rb')
        SESSION.storbinary(f'STOR {DIRECTORY}{filename}', file)
        file.close()
        return filename

    def download_thumb(self, image_url, slug, episode, season):
        image_url = "https://www.anitube.biz" + image_url
        extension = image_url.split('/')[-1].split('.')[-1].split("?")[0]
        r = requests.get(image_url, allow_redirects=True)
        filename = f"{slug}-{episode}-season-{season}.{extension}"
        open(f"{THUMB_SERVER_PATH}{filename}", 'wb').write(r.content)
        return filename

    def episodes(self, url, slug, title, img):
        season_number = 1 if "season" not in slug else slug.split("season-")[-1].split("-")[0]

        DRIVER.get(url)
        page_soup_website = soup(DRIVER.page_source, "html.parser")
        episode_list = page_soup_website.findAll("div", {"class": "AniPageContainerLista"})[0].findAll("a")

        meta_data = page_soup_website.findAll("div", {"class": "boxAnimeSobreLinha"})
        year = meta_data[-1].text.strip().replace("Ano:", "")
        genre = meta_data[1].text.strip().replace("Genero:", "").split(",")
        genre = ",".join([gen.strip() for gen in genre])
        now = datetime.datetime.now()
        description = page_soup_website.findAll("div", {"id": "sinopse2"})[0].text

        try:
            episode_count = float(episode_list[-1].text.split("Episódio ")[-1])
        except:
            try:
                episode_count = float(episode_list[-1].text.split("Episodio ")[-1])
            except:
                episode_count = float(len(episode_list[-1].text.split("Episodio ")))

        slug_season = slug + "-season-" + str(season_number)
        print(slug_season)
        if episode_count > 0:
            sql_select_query = """SELECT COUNT(*),total_episode FROM info WHERE slug_season = %s"""
            CURSOR.execute(sql_select_query, (slug_season,))
            data = CURSOR.fetchall()[0]
            exist = data[0]
            ep_amt = data[1]
            image = None

            if not exist:
                image = IMAGE_SITE + str(self.download_image(img, slug))
                print("New Anime Inserted")
                insert_website = """INSERT INTO info (title,slug,image,description,total_episode,genres,rating,season,
                                    `release`,added_date,slug_season) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) """
                CURSOR.execute(insert_website, (title, slug, image, description, episode_count, genre, "NA", season_number,
                                              year, now, slug_season))
                DB.commit()
            else:
                if float(ep_amt) != float(episode_count):
                    update_website = """UPDATE info SET total_episode = %s, added_date = %s WHERE slug = %s """
                    CURSOR.execute(update_website, (episode_count, now, slug,))
                    DB.commit()
                    print("Anime Update")
            for ep in episode_list:
                try:
                    try:
                        episode_number = float(ep.text.split("Episódio ")[-1])
                    except:
                        episode_number = float(ep.text.split("Episodio ")[-1])
                    if not image:
                        image = IMAGE_SITE + str(self.download_image(img, slug))

                    select_episode = """SELECT COUNT(*) FROM episodes WHERE anime_id = %s AND episode = %s AND season = %s """
                    CURSOR.execute(select_episode, (slug, episode_number, season_number))
                    data = CURSOR.fetchall()[0]
                    exist = data[0]
                    if not exist:
                        ep_link = ep.get('href')
                        DRIVER.get(ep_link)
                        page_soup_website = soup(DRIVER.page_source, "html.parser")
                        episode = page_soup_website.findAll("div", {"id": "player"})[0].find("a").get("href")
                        DRIVER.get(episode)
                        page_soup_website = soup(DRIVER.page_source, "html.parser")
                        episodes = page_soup_website.findAll("div", {"class": "plyr__video-wrapper"})

                        episode_release = page_soup_website.findAll("span", {"class": "date"})[0].text
                        link_br = episodes[0].find("video").get("src")
                        link_en = episodes[1].find("video").get("src")
                        
                        print("New Episode ", slug, f"{episode_number} / {episode_count}")
                        insert_website = """INSERT INTO episodes (anime_id,episode,embed,embed_multi,season,thumbnail,
                                            slug_season,episode_release,episode_year) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) """
                        CURSOR.execute(insert_website, (slug, episode_number, link_br, link_en, season_number, image,
                                                      slug_season, episode_release, year))
                        DB.commit()
                    else:
                        print("Skipping episodes ", f"{episode_number} / {episode_count}")
                except:
                    pass

    def latest(self, sub_or_dub, start, end):
        for page_num in range(start, end, -1):
            print("Page ", page_num)
            url = sub_or_dub
            url += str(page_num)
            DRIVER.get(url)
            sleep(2)
            page_soup = soup(DRIVER.page_source, "html.parser")
            home_video_blocks = page_soup.findAll("div", {"class": "itemE"})
            for block in home_video_blocks:
                link = block.find('a').get('href')
                image = block.find('div', {"class": "thumb"}).find('img').get("src")
                text = block.find('a').text
                DRIVER.get(link)
                prelim_website = soup(DRIVER.page_source, "html.parser")
                if prelim_website.findAll("div", {"class": "controles"}):
                    anime_home_link = prelim_website.findAll("div", {"class": "controles"})[0].findAll("a")
                    ani_link = anime_home_link[1].get("href")
                    slug = ani_link.split("/")[-1]

                    DRIVER.get(ani_link)
                    episodes_page_outside = soup(DRIVER.page_source, "html.parser")

                    pagination = episodes_page_outside.find("ul", {"class": "content-pagination"})
                    if pagination:
                        DRIVER.get(pagination.findAll("li")[-2].find('a').get('href'))
                        episodes_page_outside = soup(DRIVER.page_source, "html.parser")

                    episode_blocks = episodes_page_outside.findAll("div", {"class": "itemE"})
                    try:
                        if "Todos" in episode_blocks[-1].find('a').text:
                            anime_link_inside = episode_blocks[-1].find('a').get('href')
                            title = episode_blocks[-1].find('a').text.split(" Todos")[0][:-1].strip()
                            slug = self.slugify(title)
                            self.episodes(anime_link_inside, slug, title, image)
                    except:
                        pass

if __name__ == "__main__":
    session = ftplib.FTP( FTP_HOST,  FTP_USER, FTP_PASSWORD)
    website = BASE_URL
    Scrape().latest(website, 1, 0)
    session.quit()
    sleep(3600)
