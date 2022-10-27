import pathlib

path_file = pathlib.Path(__file__).parent.resolve()
stocks_file = path_file / 'data_json/stock.json'
bpif_file = path_file / 'data_json/bpif.json'
ofz_file = path_file / 'data_json/ofz.json'
bonds_file = path_file / 'data_json/bonds.json'

font_heavy = path_file / 'font/Garet-Heavy.ttf'
font_book = path_file / 'font/Garet-Book.ttf'

spb_file = path_file / 'spb_data/SPB.csv'
