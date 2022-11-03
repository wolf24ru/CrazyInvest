import asyncio
import json
import config
import requests

url_shares = 'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json?first=350'
url_bpif = 'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQTD/securities.json?first=500'
url_ofz = 'https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQOB/securities.json?first=200'
url_bonds = 'https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQCB/securities.json?first=3000'


async def _download_stock_market_data(url, file_path):
    with requests.get(url) as response:
        if response.status_code == 200:
            with open(file_path, 'w') as file:
                json.dump(response.json(), file)


async def download_data():
    await asyncio.gather(
        _download_stock_market_data(url_ofz, config.ofz_file),
        _download_stock_market_data(url_bonds, config.bonds_file),
        _download_stock_market_data(url_bpif, config.bpif_file),
        _download_stock_market_data(url_shares, config.stocks_file),
    )
