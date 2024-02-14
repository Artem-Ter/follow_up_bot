import requests
import pandas as pd
import csv

from forex_python.converter import CurrencyRates
from utils import (get_file_path,
                   load_previous_data,
                   save_data_to_file)


def get_exchange_rate():
    currency_rates = CurrencyRates()
    exchange_rate = currency_rates.get_rate('USD', 'BRL')
    return round(exchange_rate, 2)


def get_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        rows = csv.DictReader(file)
        last_trading_date_filepath = get_file_path('last_trading_date.json')
        last_update = load_previous_data(last_trading_date_filepath)
        date = last_update['date']
        new_update = date
        open_orders_filepath = get_file_path('open_orders.json')
        orders = load_previous_data(open_orders_filepath)
        prev_trading_data_filepath = get_file_path('prev_trading_data.json')
        prev_data = load_previous_data(prev_trading_data_filepath)
        initial_data = prev_data['initial_data']
        current_data = prev_data['current_data']
        for row in rows:
            operation_date = row['Date(UTC)']
            if operation_date == date:
                break
            if operation_date > new_update:
                new_update = operation_date
            row_key = row['Market']
            my_dict = {
                "type": row['Type'],
                "ex_rate": float(row['Price']),
                "crypto": float(row['Amount']),
                "currency": float(row['Total'])
            }
            orders[row_key] = orders.get(row_key, list()) + [my_dict]
        last_update['date'] = new_update
        save_data_to_file(last_trading_date_filepath, last_update)
        for key, value in orders.items():
            currency_type = key[3:]
            orders[key] = get_open_orders(value, current_data, currency_type)
        save_data_to_file(open_orders_filepath, orders)
        brl_usd = get_exchange_rate()
        curr_brl = current_data['BRL']
        curr_fdusd = current_data['FDUSD']
        curr_crypto = current_data['crypto']
        current_data['ex_rate'] = -(curr_brl
                                    + curr_fdusd * brl_usd) / curr_crypto
        prev_data['current_data'] = current_data
        save_data_to_file(prev_trading_data_filepath, prev_data)
        init_crypto = initial_data["crypto"]
        init_brl = initial_data["BRL"]
        init_fdusd = initial_data["FDUSD"]
        report = {
            'overview': [
                {"status": "initial_data",
                    "ex_rate": initial_data["ex_rate"],
                    "crypto": init_crypto,
                    "BRL": init_brl,
                    "FDUSD": init_fdusd},
                {"status": "current_data",
                    "ex_rate": current_data['ex_rate'],
                    "crypto": curr_crypto,
                    "BRL": curr_brl,
                    "FDUSD": curr_fdusd},
                {"status": "total",
                    "ex_rate": "",
                    "crypto": curr_crypto - init_crypto,
                    "BRL": curr_brl - init_brl,
                    "FDUSD": curr_fdusd - init_fdusd},
            ]
        }
        for key, value in orders.items():
            new_key = f'open_orders_{key}'
            report[new_key] = value
        return report


def get_open_orders(orders, current_data, currency_type):
    sorted_data = sorted(orders, key=lambda item: item['ex_rate'])
    result = list()
    accum_crypto = 0
    accum_currency = 0
    temp_buy = []
    for item in sorted_data:
        curr_type = item['type']
        if curr_type == 'BUY':
            temp_buy += [item]
        else:
            sell_currency = item['currency']
            sell_crypto = item['crypto']
            sell_ex_rate = item['ex_rate']
            while temp_buy:
                buy_item = temp_buy.pop()
                buy_currency = buy_item['currency']
                buy_crypto = buy_item['crypto']
                buy_ex_rate = buy_item['ex_rate']
                sell_crypto -= buy_crypto
                sell_currency -= buy_currency
                if sell_crypto == 0:
                    accum_currency += sell_currency
                    break
                if sell_currency == 0:
                    accum_crypto -= sell_crypto
                    sell_crypto = 0
                    break
                if sell_crypto < 0:
                    currency = buy_ex_rate * (-sell_crypto)
                    buy_dict = {
                        "type": 'BUY',
                        "ex_rate": buy_ex_rate,
                        "crypto": -sell_crypto,
                        "currency": currency
                    }
                    temp_buy += [buy_dict]
                    accum_currency += (sell_currency + currency)
                    sell_crypto = 0
                    break
            if sell_crypto:
                currency = sell_ex_rate * sell_crypto
                accum_currency += (sell_currency - currency)
                if sell_crypto < 0.01 and result:
                    item = result.pop()
                    sell_crypto += item['crypto']
                    currency += item['currency']
                    sell_ex_rate = round(currency / sell_crypto, 2)
                sell_dict = {
                    "type": 'SELL',
                    "ex_rate": sell_ex_rate,
                    "crypto": sell_crypto,
                    "currency": currency
                }
                result += [sell_dict]
    current_data[currency_type] = current_data.get(currency_type, 0) + accum_currency
    current_data['crypto'] = current_data.get('crypto', 0) + accum_crypto
    result += temp_buy
    return result


def get_btc_brl_price():
    url = 'https://api.binance.com/api/v3/ticker/price'
    params = {'symbol': 'BTCBRL'}

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data['price']
    else:
        return None


def get_report(file_path):
    # Convert DataFrame to XLS file
    report_file_name = 'trading_report.xlsx'
    report = get_data(file_path)

    with pd.ExcelWriter(report_file_name, engine='xlsxwriter') as writer:
        for sheet_name, sheet_data in report.items():
            df = pd.DataFrame(sheet_data)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return report_file_name
