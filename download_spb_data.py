# TODO получить  данные с питерской биржи
# Скорее всего только через полную загрузку и парсер этой таблицы
# https://spbexchange.ru/ru/stocks/inostrannye/Instruments.aspx?csv=download
# TODO настроить на работу раз в сутки за минуту до открытия биржы
#  и затем каждый час до закрытия
#  и через минуту после закрытия

import os
import time
import pathlib
import requests
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

PATH = pathlib.Path(__file__).parent.absolute()


def latest_download_file():
    os.chdir(PATH)
    files = sorted(os.listdir(os.getcwd()), key=os.path.getmtime)
    newest = files[-1]

    return newest


def download_data():
    url_spb = 'https://spbexchange.ru/ru/stocks/inostrannye/Instruments.aspx?csv=download'

    with requests.get(url_spb, allow_redirects=True) as r:
        print(r.status_code)
        if r.status_code == 200:
            with open('SPB.csv', 'wb') as f:
                f.write(r.content)
        else:
            # TODO Тут нужно как-то запустить selenium из докера Примерная инструкция тут https://stackoverflow.com/questions/45323271/how-to-run-selenium-with-chrome-in-docker

            option = webdriver.ChromeOptions()

            prefs = {"download.default_directory": str(PATH)}
            option.add_experimental_option('prefs', prefs)

            driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)
            driver.get(url_spb)
            time.sleep(5)
            driver.close()

            file = latest_download_file()

            if pathlib.Path(file).suffix == '.csv':
                os.renames(file, 'SPB.csv')

    # TODO тут нужна валидация
