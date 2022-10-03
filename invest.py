"""
старт https://habr.com/ru/post/495324/
как работает api на мосбирже https://habr.com/ru/post/486716/

href="https://www.cbr-xml-daily.ru/ API для курсов ЦБ РФ

акции https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities?first=350
?БПИФ https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQTD/securities?first=500
ОФЗ https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQOB/securities?first=200
облигации https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQCB/securities?first=3000
"""

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
from pathlib import Path
from datetime import date, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont, ImageFilter

path_file = pathlib.Path(__file__).parent.resolve()
sys.path.append(str(path_file))

import config
from download_msb_data import download_data as msbd
from download_spb_data import download_data as spbd


class CrazyInvest:
    def __init__(self, limit=None, asset: str = 'stock', stock_market: list = ['MB'], tz=timezone.utc):
        self.limit = limit
        self._get_spb_stock_exchange()
        self._get_msb_stock_exchange()
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
        match self.asset:

            case 'stock':
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
                    self.choice_table = pandas.concat([self.spb_table_stock,
                                                       self.main_table_stocks_ru],
                                                      ignore_index=True).sample().values[0]
                elif 'MB' in self.stock_market:
                    self.choice_table = self.main_table_bonds_ru.sample().values[0]
                elif 'SPB' in self.stock_market:
                    self.choice_table = self.spb_table_bond.sample().values[0]
                else:
                    print("O no. You didn't choose any stock market")
                    raise Exception('stock market not chosen')
            case _:
                raise Exception('incorrect asset name')

        self.asset_choice = self.choice_obj(self.choice_table)

    @property
    def inform(self) -> str:
        return f'''
сокращенно: {self.asset_choice['sec_id']}
наименование: {self.asset_choice['full_name']}
цена: {self.asset_choice['price_str']}
количество: {self.asset_choice['quantity']}
изменение за месяц: {self.asset_choice['price_increase']:.{2}f} %
isn: {self.asset_choice['isn']}
'''

    def telegram_text(self) -> str:
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
        width = 1040
        height = 560

        img = Image.new(mode="RGBA", size=(width, height), color=(255, 255, 255, 100))
        draw_background = ImageDraw.Draw(img)

        draw_background.rounded_rectangle((0, 0, width, height), fill=(45, 144, 235), radius=0)
        draw_background.rounded_rectangle((20, 20, width - 20, height - 20), fill=(255, 255, 255), radius=10)

        # Создание дуги
        end_arc = 180 + (1.8 * self.asset_choice['price_increase'])
        antialias = 4
        w = width * antialias
        h = height * antialias
        img_arc = Image.new(size=(w, h), mode='RGBA', color=(255, 255, 255, 100))
        img_arc.putalpha(0)
        draw_arc = ImageDraw.Draw(img_arc)

        draw_arc.arc([((w / 2) - 192 * antialias, 38 * antialias),
                      ((w / 2) + 192 * antialias, 422 * antialias)],
                     start=0, end=360,
                     fill=(161, 161, 161, 100), width=5 * antialias)
        if end_arc >= 180:
            color_percent = (1, 149, 25)
            draw_arc.arc([((w / 2) - 200 * antialias, 30 * antialias),
                          ((w / 2) + 200 * antialias, 430 * antialias)],
                         start=180, end=end_arc,
                         fill=color_percent, width=20 * antialias)
        else:
            color_percent = 'red'
            draw_arc.arc([((w / 2) - 200 * antialias, 30 * antialias),
                          ((w / 2) + 200 * antialias, 430 * antialias)],
                         start=end_arc, end=180,
                         fill=color_percent, width=20 * antialias)
        img_arc = img_arc.resize((width, height), Image.Resampling.LANCZOS)
        img_arc = img_arc.filter(ImageFilter.SMOOTH)

        # добавление текста

        path_font_main = str(config.font_heavy)
        path_font_second = str(config.font_book)

        font_main = ImageFont.truetype(path_font_main, 80)
        font_secoond = ImageFont.truetype(path_font_second, 80)
        font_2_b = ImageFont.truetype(path_font_main, 50)
        font_2_s = ImageFont.truetype(path_font_second, 50)
        font_3_s = ImageFont.truetype(path_font_second, 24)
        font_3_b = ImageFont.truetype(path_font_main, 24)

        img_text = Image.new(mode="RGBA", size=(width, height), color=(255, 255, 255, 100))
        draw_text = ImageDraw.Draw(img_text)
        img_text.putalpha(0)

        draw_text.text(((width / 2) - 205, 220), f'{self.asset_choice["price_increase"]:.{2}f} %/мс',
                       fill=color_percent, anchor="rs", font=font_3_s)
        draw_text.text((width / 2, 220), self.asset_choice['sec_id'], fill="black", anchor="ms", font=font_main)
        draw_text.text((width / 2, 290), f"{self.asset_choice['quantity'] } шт.",
                       fill="black", anchor="ms", font=font_2_b)
        draw_text.text((width / 2, 340), self.asset_choice['full_name'], fill="black", anchor="ms", font=font_3_b)
        draw_text.text((width / 2, 400), self.asset_choice['price_str'], fill="black", anchor="ms", font=font_2_b)
        draw_text.text((width / 6, 530), self.asset_choice['isn'], fill="black", anchor="ms", font=font_3_s)
        draw_text.text((width - (width / 4), 530), str(self.date_create), fill="black", anchor="ms",
                       font=font_3_s)

        img.alpha_composite(img_arc, (0, 0))
        img.alpha_composite(img_text, (0, 0))
        img_name = config.path_file / f"img/{str(self.date_create).split('.')[0]}.png"
        img.save(img_name, "PNG")
        return Path(img_name).resolve()

    def print_asset(self):
        print(f'''
{'-' * 60}
{self.inform}
{'-' * 28}
{self.date_create}
{'-' * 60}
''')

    @staticmethod
    def _is_integer(n: float) -> bool:
        try:
            float(n)
        except ValueError:
            return False
        else:
            return float(n).is_integer()

    def percentage_change(self, price: float, seci: str, boardid: str) -> float:
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
        path = pathlib.Path(path)
        if not path.exists():
            asyncio.run(acton())

    def _get_msb_stock_exchange(self):
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
        data = json_dict['securities']['data']
        columns = json_dict['securities']['metadata']

        df = pandas.DataFrame(data=data, columns=columns)

        short_table = df[['SECID', 'SECNAME', 'ISIN', 'PREVPRICE', 'BOARDID']]
        return short_table

    def _get_spb_stock_exchange(self):
        """Получить данные с питерской биржи"""
        self.file_exist(config.cpb_file, spbd)

        spb_table = pandas.read_csv(config.cpb_file, sep=';')

        # название e_full_name
        # код s_RTS_code
        # ис_код s_ISIN_code
        # вид актива s_sec_type_name_dop
        spb_table = spb_table[['s_RTS_code', 's_ISIN_code', 'e_full_name', 's_sec_type_name_dop']]
        spb_table.rename(columns={'s_RTS_code': 'SECID', 'e_full_name': 'SECNAME', 's_ISIN_code': 'ISIN'}, inplace=True)

        # сортируем в разные таблицы по виду актива (акции, облигации)
        spb_table_stock = spb_table[(spb_table.s_sec_type_name_dop == 'Акции')]
        self.spb_table_stock = spb_table_stock[['SECID', 'SECNAME', 'ISIN']]

        spb_table_bond = spb_table[(spb_table.s_sec_type_name_dop == 'Облигации')]
        self.spb_table_bond = spb_table_bond[['SECID', 'SECNAME', 'ISIN']]

    @staticmethod
    def _get_currency_price(currency: str) -> str:
        all_currencies = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
        return all_currencies['Valute'][currency]['Value']

    def _get_current_price(self, sec_id_choice: str) -> dict:
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
            print(er)
            print(sec_id_choice)
            exit()
