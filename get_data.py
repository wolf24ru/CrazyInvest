from download_msb_data import download_data as msb
from download_spb_data import download_data as spd
import asyncio

if __name__ == '__main__':
    asyncio.run(msb())
    asyncio.run(spd())