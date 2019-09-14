import os
import sys
import time

import eyed3
import requests
import urllib
import urllib.parse

from selenium import webdriver
from selenium.webdriver.common.by import By

# credit to OWADVL and sbha for this part
def scroll (driver):

    SCROLL_PAUSE_TIME = 0.5
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def clean_query(query):
    q = query.replace(" my-free-mp3s.com", "")
    q = urllib.parse.quote(q)

    return q

if __name__ == "__main__":

    if len(sys.argv) != 2:
        exit(1) # bad arguments
    elif not os.path.isfile(sys.argv[1]):
        exit(1) # bad file

    audiofile = eyed3.load(sys.argv[1])
    query = sys.argv[1].split('/')[-1]
    query = clean_query(query)

    # prepare the option for the chrome driver
    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    # start chrome browser
    driver = webdriver.Chrome(options=options)
    driver.get("https://soundcloud.com/search?q=" + query)
    scroll(driver)

    # Grab all results
    tracks = driver.find_elements(By.XPATH, "//li[@class='searchList__item']/div/div")

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

    if not best_guess:
        exit(1)

    # Grab url for artwork
    artwork = best_guess.find_element(By.XPATH, "//a[@class='sound__coverArt']/div/span")
    artwork_url = artwork.get_attribute('style').split('background-image: url("')[1].split('");')[0]

    if not '-t500x500.jpg' in artwork_url:
        pass
        # do something
        # artwork_url = artwork_url.split('-t')[0] + '-t500x500.jpg'

    print(artwork_url)
    urllib.request.urlretrieve(artwork_url,"tmp.jpg")

    audiofile.tag.images.set(3, open('tmp.jpg','rb').read(), 'image/jpeg')
    audiofile.tag.save()
    print(audiofile)

    # print(artwork.get_attribute("style"))

    # print(global_matches)
    # print(best_guess.get_attribute("aria-label"))

    driver.quit()

    # p_elements = driver.find_elements("xpath", "//*[@class='sound__coverArt']")
    # print(p_elements)
