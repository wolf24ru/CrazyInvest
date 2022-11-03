import asyncio
import sys
import json
import pathlib
import random

import requests
import pandas
import math
import yfinance as yf
import datetime
from time import sleep
from pathlib import Path
from datetime import date, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont

path_file = pathlib.Path(__file__).parent.resolve()
sys.path.append(str(path_file))

import config
from download_mb_data import download_data as msbd
from download_spb_data import download_data as spbd


class CrazyInvest:
    def __init__(self, limit=None, asset: str = 'stock', stock_market: list = ['MB'], tz=timezone.utc):
        """
        Инициализация

        Parameters:
            limit (int): Целочисленный лимит активов
            asset (str): Вид актива. Доступно 2 варианта:'stock' или 'bond'
            stock_market (list): Список используемых бирж: MB - МосБиржа; SPB - Питерская Биржа.
            tz (timezone): Временная зона
        """
        self.limit = limit
        self._get_spb_stock_exchange()
        self._get_mb_stock_exchange()
        self.asset = asset
        self.date_create = datetime.datetime.now(tz)
        self.stock_market = stock_market

        self.choice()

        if self.limit:
            if self._is_integer(self.limit) and self.limit >= 300:
                while self.asset_choice['price_ru'] >= self.limit:
                    # print(self.asset_choice)
                    self.choice()
            else:
                error_str = 'limit amount is not number'
                raise Exception(error_str)

    def choice(self):
        """
        Определения актива и биржи с дальнейшим получением конкретного актива
        """
        match self.asset:
            # Выбор актива
            case 'stock':
                # выбор биржи
                if ('MB' in self.stock_market) & ('SPB' in self.stock_market):
                    self.choice_table = pandas.concat([self.spb_table_stock,
                                                       self.main_table_stocks_ru],
                                                      ignore_index=True).sample().values[0]
                elif 'MB' in self.stock_market:
                    self.choice_table = self.main_table_stocks_ru.sample().values[0]
                elif 'SPB' in self.stock_market:
                    self.choice_table = self.spb_table_stock.sample().values[0]
                else:
                    print("O no. You didn't choose any stock market")
                    raise Exception('stock market not chosen')

            case 'bond':
                if ('MB' in self.stock_market) & ('SPB' in self.stock_market):
                    self.choice_table = self.main_table_bonds_ru.sample().values[0]
                elif 'MB' in self.stock_market:
                    self.choice_table = self.main_table_bonds_ru.sample().values[0]
                elif 'SPB' in self.stock_market:
                    raise Exception('At the moment you cannot use bonds from the St. Petersburg Stock Exchange')
                else:
                    print("O no. You didn't choose any stock market")
                    raise Exception('stock market not chosen')
            case _:
                raise Exception('incorrect asset name')

        # итоговое получение актива
        self.asset_choice = self.choice_obj(self.choice_table)

    @property
    def inform(self) -> str:
        """
        Подготовка информации для вывода
        Returns:
            (str) Возвращает готовую строку с данными
        """
        return f'''
сокращенно: {self.asset_choice['sec_id']}
наименование: {self.asset_choice['full_name']}
цена: {self.asset_choice['price_str']}
количество: {self.asset_choice['quantity']}
изменение за месяц: {self.asset_choice['price_increase']:.{2}f} %
isn: {self.asset_choice['isn']}
'''

    def telegram_text(self) -> str:
        """
        Подготовка информации для вывода в telegram в формате markdown
        Returns:
            (str) Возвращает готовую строку с данными и преобразованными элементами.
        """
        if self.asset_choice['price_increase'] > 0:
            emoji = '📈'
        else:
            emoji = '📉'

        return f'''
Сокращенно: `{self.asset_choice['sec_id']}`
Наименование: *{self.asset_choice['full_name']}*
Цена: {self.asset_choice['price_str']}
Количество: {self.asset_choice['quantity']}
Изменение за месяц: {emoji}{self.asset_choice['price_increase']:.{2}f} %
isn: {self.asset_choice['isn']}

{self.date_create}
'''.replace('.', '\.').replace('-', '\-')\
            .replace('(', '\(').replace(')', '\)')\
            .replace('+', '\+')

    def crate_img(self) -> Path:
        """
        Создает изображение используя данные актива.
        Returns:
            (Path) Возвращает полный путь до изображения.
        """
        width = 950
        height = 1150

        img = Image.new(mode="RGBA", size=(width, height), color=(21, 21, 21))

        # добавление фона
        background_vector = Image.open(config.vector, formats=["PNG"])
        img.paste(background_vector, (0, 0), background_vector)

        # добавление шрифтов
        path_font_montserrat_extrabold = config.path_file / "font/Montserrat-ExtraBold.ttf"
        path_font_montserrat_medium = config.path_file / "font/Montserrat-Medium.ttf"
        path_font_montserrat_light = config.path_file / "font/Montserrat-Light.ttf"
        path_font_montserrat_seambold = config.path_file / "font/Montserrat-SemiBold.ttf"
        path_font_montserrat_regular = config.path_file / "font/Montserrat-Regular.ttf"

        ticker = self.asset_choice['sec_id']

        if len(ticker) <= 10:
            font_ticker = ImageFont.truetype(str(path_font_montserrat_extrabold), 128)
        elif 15 >= len(ticker) > 10:
            size = 128 - ((len(ticker) - 10) * 7)
            font_ticker = ImageFont.truetype(str(path_font_montserrat_extrabold), size)
        else:
            font_ticker = ImageFont.truetype(str(path_font_montserrat_extrabold), 23)
        font_full_name = ImageFont.truetype(str(path_font_montserrat_medium), 32)
        font_price = ImageFont.truetype(str(path_font_montserrat_light), 110)
        font_other = ImageFont.truetype(str(path_font_montserrat_medium), 32)
        font_percent = ImageFont.truetype(str(path_font_montserrat_seambold), 84)
        font_id = ImageFont.truetype(str(path_font_montserrat_seambold), 32)
        font_date = ImageFont.truetype(str(path_font_montserrat_regular), 32)

        # Выбор цвета относительно процентов за месяц
        if self.asset_choice['price_increase'] >= 0:
            chart_img = Image.open(config.green_chart, formats=["PNG"])
            color_accent = (203, 252, 1)
            price_increase = self.asset_choice['price_increase']
        elif self.asset_choice['price_increase'] == 'nan':
            price_increase = 0
        else:
            price_increase = self.asset_choice['price_increase']
            chart_img = Image.open(config.red_chart, formats=["PNG"])
            color_accent = (252, 1, 1)

        img.paste(chart_img, (0, 0), chart_img)

        img_text = Image.new(mode="RGBA", size=(width, height), color=(255, 255, 255))
        draw_text = ImageDraw.Draw(img_text)
        img_text.putalpha(0)

        # добавление текста
        draw_text.text((width / 2, 230), self.asset_choice['sec_id'],
                       fill="white", anchor="ms", font=font_ticker)
        draw_text.text((width / 2, 290), self.asset_choice['full_name'],
                       fill="white", anchor="ms", font=font_full_name)
        price = self.asset_choice['price']
        price_ru = self.asset_choice['price_ru']
        currency = 'руб'
        if price != price_ru:
            currency = price["currency"]
            price = price["stock_current_prise"]
            draw_text.text((width / 2, 400), f'({price} {currency})',
                           fill="white", anchor="ms", font=font_other)
        draw_text.text((width / 2, 500), f"{price_ru:.{2}f}",
                       fill="white", anchor="ms", font=font_price)
        draw_text.text((405, 550), 'RUB', fill=color_accent, anchor="rs",
                       font=font_other)
        draw_text.text((540, 550), f'{self.asset_choice["quantity"]} ШТ',
                       fill=color_accent, anchor="ls", font=font_other)
        draw_text.line([(435, 540), (510, 540)], fill=color_accent, width=2)
        draw_text.text(((width / 2), 745),
                       f'{price_increase:.{2}f}%',
                       fill=color_accent, anchor="ms", font=font_percent)
        draw_text.text((width / 2, 1080), self.asset_choice['isn'],
                       fill="white", anchor="ms", font=font_id)
        draw_text.text((width / 2, 1120), str(self.date_create),
                       fill="white", anchor="ms", font=font_date)

        img.alpha_composite(img_text, (0, 0))
        img_name = config.path_file / f"img/{str(self.date_create).split('.')[0]}.png"
        img.save(img_name, "PNG")
        return Path(img_name).resolve()

    def print_asset(self):
        """
        Функция для вывода результата с подготовленными данными в консоль
        """
        print(f'''
{'-' * 60}
{self.inform}
{'-' * 28}
{self.date_create}
{'-' * 60}
''')

    @staticmethod
    def _is_integer(n: float) -> bool:
        """
        Проверка на число
        Returns:
            (bool) является ли числом
        """
        try:
            float(n)
        except ValueError:
            return False
        else:
            return float(n).is_integer()

    def percentage_change(self, price: float, seci: str, boardid: str) -> float:
        """
        Изменения цены за последний месяц в процентах с МосБиржи

        Parameters:
            price (float): Текущая цена
            seci (str): Тикет актива
            boardid (str): вид актива

        Returns:
            percent(float): Месячное изменение цены в процентах
        """
        day = date.today() - timedelta(days=30)
        percent = 0
        match self.asset:
            case 'stock':
                url = f'http://iss.moex.com/iss/history/engines/stock/markets/shares/boards/{boardid}/securities/{seci}.json?iss.meta=off&iss.only=history&history.columns=SECID,TRADEDATE,CLOSE&limit=1&from={day}'
            case 'bond':
                url = f'http://iss.moex.com/iss/bonds/engines/stock/markets/shares/boards/{boardid}/securities/{seci}.json?iss.meta=off&iss.only=history&history.columns=SECID,TRADEDATE,CLOSE&limit=1&from={day}'
            case _:
                url = ''
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()

            prise_1mo = data['history']['data'][0][2]
            if prise_1mo:
                percent = (price - prise_1mo) / prise_1mo * 100
        return percent

    def choice_obj(self, data: list) -> dict:
        """
        Преобразование выбранного актива

        Parameters:
            data (list): Данные выбранного актива

        Returns:
            return (dict): Словарь преобразованных данных
        """
        # Проверка наличия записей в графе с ценой
        try:
            data_nan = math.isnan(data[3])
        except IndexError:
            data_nan = True

        if data_nan:
            price = self._get_current_price(data[0])
            price_str = f'({price["stock_current_prise"]} {price["currency"]}) {price["rub_prise"]:.{2}f} руб.'
            price_ru = price["rub_prise"]
            price_increase = price["price_increase"]
        else:
            price = data[3]
            price_ru = data[3]
            price_str = f'{data[3]} руб.'
            price_increase = self.percentage_change(price_ru, data[0], data[4])

        quantity = 1
        if self.limit:
            if self.limit >= price_ru:
                int_div = int(self.limit // price_ru) + 1
                quantity = random.choice(range(1, int_div))
        return {
            'sec_id': data[0],
            'full_name': data[1],
            'isn': data[2],
            'price': price,
            'price_str': price_str,
            'price_ru': price_ru,
            'quantity': quantity,
            'price_increase': price_increase
        }

    @staticmethod
    def file_exist(path: str, acton):
        """
        Проверка существования файла

        Parameters:
            path (str): Путь до файла
            acton: Функция по запуску загрузки файла
        """
        path = pathlib.Path(path)
        if not path.exists():
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                loop.create_task(acton())
                sleep(4)
            else:
                asyncio.run(acton())
                sleep(4)

    def _get_mb_stock_exchange(self):
        """
        Загрузка данных из json
        """
        # open JSON
        for file_name in [config.stocks_file, config.bpif_file,
                          config.ofz_file, config.bonds_file]:
            self.file_exist(file_name, msbd)

        with open(config.stocks_file, 'r') as file:
            shares_json = json.load(file)

        with open(config.bpif_file, 'r') as file:
            bpif_json = json.load(file)

        with open(config.ofz_file, 'r') as file:
            ofz_json = json.load(file)

        with open(config.bonds_file, 'r') as file:
            bonds_json = json.load(file)

        # Акции и пифы
        self.main_table_stocks_ru = pandas.concat([self._get_short_table(shares_json),
                                                   self._get_short_table(bpif_json)],
                                                  ignore_index=True)

        # Облигации и ОФЗ
        self.main_table_bonds_ru = pandas.concat([self._get_short_table(ofz_json),
                                                  self._get_short_table(bonds_json)],
                                                 ignore_index=True)

    @staticmethod
    def _get_short_table(json_dict: dict) -> pandas.DataFrame:
        """
        Получение укороченной таблицы, только с необходимыми столбцами

        Parameters:
            json_dict (dict): json данные таблицы
        """
        data = json_dict['securities']['data']
        columns = json_dict['securities']['metadata']

        df = pandas.DataFrame(data=data, columns=columns)

        short_table = df[['SECID', 'SECNAME', 'ISIN', 'PREVPRICE', 'BOARDID']]
        return short_table

    def _get_spb_stock_exchange(self):
        """
        Получить данные с питерской биржи
        """
        self.file_exist(config.spb_file, spbd)

        spb_table = pandas.read_csv(config.spb_file, sep=';')

        # название e_full_name
        # код s_RTS_code
        # ис_код s_ISIN_code
        # вид актива s_sec_type_name_dop
        spb_table = spb_table[['s_RTS_code', 's_ISIN_code', 'e_full_name', 's_sec_type_name_dop']]
        spb_table.rename(columns={'s_RTS_code': 'SECID', 'e_full_name': 'SECNAME', 's_ISIN_code': 'ISIN'}, inplace=True)

        # сортируем в разные таблицы по виду актива (акции, облигации)
        spb_table_stock = spb_table[(spb_table.s_sec_type_name_dop == 'Акции')]
        self.spb_table_stock = spb_table_stock[['SECID', 'SECNAME', 'ISIN']]

        # spb_table_bond = spb_table[(spb_table.s_sec_type_name_dop == 'Облигации')]
        # self.spb_table_bond = spb_table_bond[['SECID', 'SECNAME', 'ISIN']]

    @staticmethod
    def _get_currency_price(currency: str) -> str:
        """
        Получение текучего курса рубля относительно валюты.

        Parameters:
            currency(str): Валюта к которой необходимо найти курс.
        Returns:
            all_currencies(str): Текущая стоимость валюты в рублях
        """
        all_currencies = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
        return all_currencies['Valute'][currency]['Value']

    def _get_current_price(self, sec_id_choice: str) -> dict:
        """
        Получение текущей цены актива с СПБ

        Parameters:
            sec_id_choice(str): Тикер актива для поиска
        Returns:
            info(dict): Словарь с ключевыми значениями актива:
                stock_current_prise - стоимость в валюте
                currency - валюта
                rub_prise - стоимость в рублях
                price_increase - изменение в цены за месяц в процентах
        """
        msft = yf.Ticker(sec_id_choice)
        try:
            stock_current_prise = msft.info['currentPrice']
            currency = msft.info['financialCurrency']
            dollar_prise = self._get_currency_price(currency)
            rub_prise = stock_current_prise * dollar_prise

            hist = msft.history(period="1mo")
            open_1mo = hist['Open'][0]
            price_increase = (stock_current_prise - open_1mo) / open_1mo * 100

            return {'stock_current_prise': stock_current_prise,
                    'currency': currency,
                    'rub_prise': rub_prise,
                    'price_increase': price_increase}
        except KeyError as er:
            if msft.info['regularMarketPrice'] is None:
                print('f')
                self.choice()
            Exception(er)
