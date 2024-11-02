import decimal, locale
from django.conf import settings

locale.setlocale(locale.LC_ALL, '')

def stocks_info(transactions):
    portfolio_data = {}
    total_holding = decimal.Decimal(0)
    stocks_capital = {}

    data = get_stock_data(transactions)

    for portfolio_id, stocks in data.items():
        portfolio_holding = decimal.Decimal(0)
        portfolio_stock_info = {}

        for stock_symbol, stock_data in stocks.items():
            quantity = stock_data["stocks"]
            avg_price = stock_data["avgprice"]
            profit = stock_data["profit"]

            if quantity > decimal.Decimal(0.009):
                holding_amount = (avg_price * decimal.Decimal(quantity)) + profit
                portfolio_holding += holding_amount

                portfolio_stock_info[stock_symbol] = {
                    "holding": float(holding_amount),
                    "profit": float(profit)
                }

                if stock_symbol in stocks_capital:
                    stocks_capital[stock_symbol]["stocks"] += quantity
                    stocks_capital[stock_symbol]["profit"] += profit
                else:
                    stocks_capital[stock_symbol] = {
                        "stocks": quantity,
                        "avgprice": avg_price,
                        "profit": profit
                    }

        total_holding += portfolio_holding
        portfolio_data[portfolio_id] = portfolio_stock_info
        portfolio_data[portfolio_id]["holding"] = locale.currency(float(portfolio_holding), grouping=True)

    portfolio_data["holding"] = locale.currency(float(total_holding), grouping=True)
    portfolio_data['stocks'] = stocks_capital

    return portfolio_data

def get_stock_data(transactions):
    data = {}

    for transaction in transactions:
        # Determine the price of the transaction
        transaction_price = transaction.price
        if transaction.stock.price:
            transaction_price = transaction.stock.price

        # Convert price to USD if necessary
        if transaction.stock.currency == "USD":
            transaction_price = transaction.price * decimal.Decimal(settings.CAD_TO_USD)

        transaction_quantity = transaction.quantity
        transaction_type = transaction.transaction_type
        portfolio_id = transaction.portfolio.id
        stock_symbol = transaction.stock.symbol

        if portfolio_id not in data:
            data[portfolio_id] = {}

        if stock_symbol not in data[portfolio_id]:
            data[portfolio_id][stock_symbol] = {
                "stocks": 0,
                "profit": 0,
                "avgprice": 0
            }

        stock_data = data[portfolio_id][stock_symbol]
        current_stocks = stock_data["stocks"]
        current_profit = stock_data["profit"]
        current_avg_price = stock_data["avgprice"]

        if transaction_type in ["BY", "DR"]:
            total_shares = current_stocks + transaction_quantity
            if total_shares == 0:
                new_avg_price = 0
            else:
                prev_total_cost = current_avg_price * decimal.Decimal(current_stocks)
                new_total_cost = transaction_price * decimal.Decimal(transaction_quantity)
                new_avg_price = (prev_total_cost + new_total_cost) / decimal.Decimal(total_shares)
            
            stock_data["stocks"] = total_shares
            stock_data["avgprice"] = new_avg_price

        elif transaction_type == "SL":
            gain_or_loss = (transaction_price - current_avg_price) * decimal.Decimal(transaction_quantity)
            stock_data["profit"] = current_profit + gain_or_loss
            stock_data["stocks"] = current_stocks - transaction_quantity

        data[portfolio_id][stock_symbol] = stock_data

    return data


def dividend_information(transcations, year_count):
    trans = transcations.filter(transaction_type = "DR")
    data = find_dividend_received_monthly(trans, year_count)

    total_dividend = data['total_dividend']
    dividend_by_months = data['dividend_by_monthly'] 
    dividend_by_stcoks = data['dividend_by_stock']
    dividend_by_annually = data['dividend_by_annually']
    
    months = year_count * 12
    dividend_months = []
    dividend_values = []
    count = 0
    if year_count <=2:
        for key in dividend_by_months:
            if count == months:
                break
            dividend_months.append(key)
            dividend_values.append(dividend_by_months[key])
    elif year_count > 2:
        for key in dividend_by_months:
            if count == year_count:
                break
            dividend_months.append(key)
            dividend_values.append(dividend_by_months[key])

    return {
        "total_dividend_received": total_dividend,
        "dividend": {"months": dividend_months, "values": dividend_values},
        "dividend_by_stocks": dividend_by_stcoks,
        "dividend_by_annually": dividend_by_annually
    }

import decimal
from datetime import datetime
from django.conf import settings

def find_dividend_received_monthly(objects, period=None):
    dividend_received_each_month = {}
    dividend_annual_based = {}
    total_received_dividend = 0
    dividend_received_by_stock = {}

    for tran in objects:
        # Set transaction price (to USD or CAD)
        total_price = tran.price
        if tran.stock.currency == "USD":
            total_price *= decimal.Decimal(settings.CAD_TO_USD)
        total_price = round(total_price, 2)

        # Update total dividend received
        total_received_dividend += total_price

        # Extract date components
        month = str(tran.transaction_date.strftime("%B"))
        day = str(tran.transaction_date.day)
        year = str(tran.transaction_date.year)
        date = f"{month} {day}"
        symbol = tran.stock.symbol

        # Update annual-based dividend data
        if year not in dividend_annual_based:
            dividend_annual_based[year] = {"total": 0}
        if month not in dividend_annual_based[year]:
            dividend_annual_based[year][month] = {"total": 0, "stocks": {}}
        
        dividend_annual_based[year]["total"] += total_price
        dividend_annual_based[year][month]["total"] += total_price

        dividend_annual_based[year][month]["stocks"] = []
        dividend_annual_based[year][month]["stocks"].append({
            "symbol": symbol,
            "total_price": total_price,
            "date": tran.transaction_date
        })

        # Update dividend received each month based on period
        if period and period > 2:
            year_key = str(year)
            if year_key in dividend_received_each_month:
                dividend_received_each_month[year_key] += total_price
            else:
                dividend_received_each_month[year_key] = total_price
        else:
            month_year_key = f"{month} {year}"
            if month_year_key in dividend_received_each_month:
                dividend_received_each_month[month_year_key] += total_price
            else:
                dividend_received_each_month[month_year_key] = total_price

        # Update dividend received by each stock
        if symbol in dividend_received_by_stock:
            dividend_received_by_stock[symbol] += total_price
        else:
            dividend_received_by_stock[symbol] = total_price
    # sorted_dividend_received_by_stock = dict(sorted(dividend_received_by_stock.items(), key=lambda item: item[1], reverse=True))
    
    stock_symbols = list(dividend_received_by_stock.keys())
    stock_amounts = list(dividend_received_by_stock.values())

    return {
        "total_dividend": total_received_dividend,
        "dividend_by_monthly": dividend_received_each_month,
        "dividend_by_stock": {'stock_symbols':stock_symbols,
                              'stock_amounts': stock_amounts},
        "dividend_by_annually": dividend_annual_based
    }
