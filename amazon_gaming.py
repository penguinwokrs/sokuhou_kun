#!/usr/bin/python3.10
# -*- coding: utf8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from time import sleep

from bs4 import BeautifulSoup
import re

import requests
import json

from datetime import datetime

import os
import sys

from selenium.webdriver.support.wait import WebDriverWait

# Settings
DOMAIN_FILE = './DOMAIN'


def main():
    driver = init_driver()
    game_list = scrap_webpage(driver)
    return post_to_reporter(game_list)


# get token
def settings():
    if len(sys.argv) >= 2:
        return sys.argv[1]
    elif os.path.isfile(DOMAIN_FILE):
        with open(DOMAIN_FILE, 'r') as f:
            return f.read().splitlines()[0]
    else:
        print('DOMAIN not found')
        sys.exit(1)


def init_driver():
    # selenium初期化
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')

    # CHROME_BIN = "./chrome-linux64/chrome"
    # options.binary_location = CHROME_BIN
    # CHROME_DRIVER = "./chromedriver-linux64/chromedriver"
    # service = Service(executable_path=CHROME_DRIVER)
    # driver = webdriver.Chrome(service=service, options=options)

    driver = webdriver.Chrome(options=options)

    # ターゲット♡
    # driver.get('https://gaming.amazon.com/home')
    # sleep(5)
    # スクショ
    # driver.set_window_size(1280,1024)
    # driver.save_screenshot('screenshot.png.png')

    return driver


def scrap_game_details(driver, child_element):
    link_element = child_element.find('a')
    # ゲーム名
    name = link_element.get('aria-label')
    # URL
    path = link_element.get('href').split('?')[0]
    domain_url = 'https://gaming.amazon.com'
    url = domain_url + path
    # サムネ画像
    image_url = child_element.find('img').get('src')

    # ダータゲーム詳細画面から配布終了日(deadline)を取ってくる、ゲームリストに含めておけよメンドくせーな！
    driver.get(url)
    # 日付の要素が表示されるまで待機
    deadline_date = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-a-target="buy-box_availability-callout"]'))
    )
    # 日付取得
    date_string = deadline_date.find_elements(By.TAG_NAME, 'span')[-1].text
    date = date_format(date_string)

    return {
        'url': url,
        'image_url': image_url,
        'date': str(date),
        'name': name
    }


def scrap_webpage(driver):
    # page取得
    driver.get('https://gaming.amazon.com/home')

    # 無料ゲームに移動
    game_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-a-target="offer-filter-button-Game"]'))
    )
    game_button.click()

    # ダータゲームリスト取得
    element = driver.find_element(By.CSS_SELECTOR, '[data-a-target="offer-list-FGWP_FULL"]')
    # workaround
    # CSSの疑似要素だとレンダリングするまで描画されないため、screenshotを実行しないとサムネ画像を表示させる。
    element.screenshot_as_base64
    bs = BeautifulSoup(element.get_attribute('innerHTML'), 'lxml')
    child_elements = bs.find_all(attrs={'data-a-target': 'tw-animation-target'})

    games = []

    for child_element in child_elements:
        game = scrap_game_details(driver, child_element)
        games.append(game)
    driver.quit()
    return games


def post_to_reporter(games):
    return [
        {
            'url': game['url'],
            'image_url': game['image_url'],
            'deadline': game['date'],
            'name': game['name'],
            'platform': 'amazon',
            'is_sent': False
        }
        for game in games
    ]


def date_format(date_string):
    return datetime.strptime(date_string, '%b %d, %Y').date()


if __name__ == "__main__":
    main()
