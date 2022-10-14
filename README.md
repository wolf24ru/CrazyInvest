# CrazyInvest

## Что может:
Программа выдает рандомные финансовые инструменты, такие как акции и облигации, с Питерской и Московской бирже.

Для Питерской биржи стоит ограничение на выдачу Облигаций, так как слишком мало брокеров владеют данными позициями  

## Как использовать:
 - Установить [python 3.10](https://www.python.org/downloads/)
 - Клонировать файлы репозитория  
 - Установить зависимости: 
```shell
pip install -r requirements.txt
```
- Создать python файл для запуска скрипта `main.py` с содержимым:
```python
from invest import CrazyInvest

if __name__ == '__main__':
    
    limit = 4000,
    asset = 'stock',
    stock_market = ['MB']
    
    random_activ = CrazyInvest(limit, asset, stock_market=stock_market)
    random_activ.print_asset() # Вывести в консоль выбранную акцию с информацией по ней
    random_activ.crate_img() # Создать изображение с информацией по активу
```

Клас CrazyInvest примет следующие аргументы:   
```python
CrazyInvest(limit=None, asset: str='stock', stock_market: list=['MB'], tz=timezone.utc):
```
- `limit` - лимит по сумме (`int`), по умолчанию не установлен;
- `asset` - вид актива **акция** `'stock'`(по умолчанию) | **облигация** `'bond'`
- `stock_market` -  список бирж: `MB` - **Московская биржа** | `SPB` - **Санкт Петербургская биржа**. По умолчанию `['MB']`
- `tz` - Временная зона, по умолчанию `timezone.utc`
