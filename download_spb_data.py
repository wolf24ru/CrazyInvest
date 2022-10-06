import os
import time
import pathlib
import requests
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
import config


def latest_download_file():
    path_download = config.path_file / 'spb_data'

    os.chdir(path_download)
    files = sorted(os.listdir(os.getcwd()), key=os.path.getmtime)

    if files:
        newest = files[-1]
        return newest
    else:
        raise Exception('dir is empty')


async def download_data():
    url_spb = 'https://spbexchange.ru/ru/stocks/inostrannye/Instruments.aspx?csv=download'
    path_file = config.path_file / 'spb_data/SPB.csv'

    with requests.get(url_spb, allow_redirects=True) as r:
        print(r.status_code)
        if r.status_code == 200:
            with open(path_file, 'wb') as f:
                f.write(r.content)
        else:
            driver = webdriver.Remote('http://selenium:4444/wd/hub', desired_capabilities=DesiredCapabilities.CHROME)
            driver.get(url_spb)
            time.sleep(5)
            driver.close()

            file = latest_download_file()

            if pathlib.Path(file).suffix == '.csv':
                os.renames(file, 'SPB.csv')

    # TODO тут нужна валидация
