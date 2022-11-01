import pathlib

path_file = pathlib.Path(__file__).parent.resolve()
stocks_file = path_file / 'data_json/stock.json'
bpif_file = path_file / 'data_json/bpif.json'
ofz_file = path_file / 'data_json/ofz.json'
bonds_file = path_file / 'data_json/bonds.json'

cpb_file = path_file / 'spb_data/SPB.csv'

_for_img = path_file / 'for_img'

vector = _for_img / 'Vector.png'
green_chart = _for_img / 'green_chart.png'
red_chart = _for_img / 'red_chart.png'