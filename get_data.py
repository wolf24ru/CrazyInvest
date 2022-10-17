from download_msb_data import download_data as msb
from download_spb_data import download_data as spd
import asyncio
from datetime import datetime
from time import sleep
import logging
import config
print('staring')
logging.basicConfig(
    filename=config.path_file / 'logs/log.txt',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def job():
    logging.info("Start run download MB")
    asyncio.run(msb())
    logging.info("Start run download SPB")
    asyncio.run(spd())


if __name__ == '__main__':
    in_hours = [4, 6, 8, 10, 12, 14, 16, 18, 20]
    job()

    while True:
        _weekday_now = datetime.now().isoweekday()
        _hour_now = datetime.now().hour
        _minute_now = datetime.now().minute
        if (_weekday_now < 6) & (_hour_now in in_hours) & (_minute_now == 50):
            job()
            sleep(7100)
        sleep(1)
