import html
import os
import sys
import time

import eyed3
import requests
import urllib

from selenium import webdriver
from selenium.webdriver.common.by import By

def scroll (driver):
    # stolen from OWADVL and sbha on stack exchange
    SCROLL_PAUSE_TIME = 0.5
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def parse_query(query):
    q = query.replace(" my-free-mp3s.com", "")
    q = urllib.parse.quote(q)

    return q

def find_best_track(tracks, query):

    # track with most matching words in title
    best_guess = None
    global_matches = 0
    q = query.split("%20")

    for track in tracks:

        local_matches = 0
        for word in q:
            if word in str(track.get_attribute("aria-label")):
                local_matches += 1

        if local_matches > global_matches:
            global_matches = local_matches
            best_guess = track

    return best_guess

def embed_artwork(audiofile, track):
    # Grab url for artwork
    artwork = track.find_element(By.XPATH, "//a[@class='sound__coverArt']/div/span")
    artwork_url = artwork.get_attribute('style').split('background-image: url("')[1].split('");')[0]

    # download and embed artwork
    urllib.request.urlretrieve(artwork_url,"tmp.jpg")
    audiofile.tag.images.set(3, open('tmp.jpg','rb').read(), 'image/jpeg')
    os.remove("tmp.jpg")

def embed_date(audiofile, track):
    # grab date
    date = track.find_element(By.XPATH, "//div[@class='soundTitle__uploadTime']/time")
    year = date.get_attribute('datetime').split('-')[0]
    audiofile.tag.recording_date = year

def embed_artist(audiofile, track):
    title  = track.find_element(By.XPATH, "//div[@class='soundTitle__usernameTitleContainer']/a/span")
    artist = track.find_element(By.XPATH, "//div[@class='soundTitle__usernameTitleContainer']/div/a/span")
    t = html.unescape(title.get_attribute("innerHTML")).split(' - ')[0]
    a = html.unescape(artist.get_attribute("innerHTML"))
    if a in t:
        audiofile.tag.artist = t
    else:
        audiofile.tag.artist = a

def embed_title(audiofile, track):
    title  = track.find_element(By.XPATH, "//div[@class='soundTitle__usernameTitleContainer']/a/span")
    t = html.unescape(title.get_attribute("innerHTML").split(' - ')[-1])
    audiofile.tag.title = t

def print_metadata(audiofile):
    print(audiofile.tag.title)
    print(audiofile.tag.artist)
    print(audiofile.tag.album)
    print(audiofile.tag.album_artist)
    print(audiofile.tag.genre)
    print(audiofile.tag.recording_date)

def main(path):
    audiofile = eyed3.load(path)
    query = path.split('/')[-1]
    query = parse_query(query)

    # prepare the option for the chrome driver
    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    # start chrome browser
    driver = webdriver.Chrome(options=options)
    driver.get("https://soundcloud.com/search?q=" + query)
    scroll(driver)

    # Grab all results
    tracks = driver.find_elements(By.XPATH, "//li[@class='searchList__item']/div/div")
    track = find_best_track(tracks, query)
    if track:
        embed_artwork(audiofile, track)
        embed_date(audiofile, track)
        embed_artist(audiofile, track)
        embed_title(audiofile, track)
        audiofile.tag.save()
    else:
        print('fail:', path)

    driver.quit()


if __name__ == "__main__":

    if len(sys.argv) != 2:
        exit(1) # bad arguments
    path = sys.argv[1]

    # single file
    if os.path.isfile(path):
        main(path)

    # directory
    elif os.path.isdir(path):
        for file in os.listdir(path):
            if file.endswith(".mp3"):
                print(os.path.join(path, file))
                main(os.path.join(path, file))
