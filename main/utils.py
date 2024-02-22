import decimal, locale


def stocks_info(transactions):
    portfolio_data = {}
    data = get_stock_data(transactions)
    total_holding = 0
    stocks_capital = None
    for key in data:
        holding = 0
        stock = {}

        for key_2 in data[key]:
            stocks = data[key][key_2]["stocks"]
            price = data[key][key_2]["avgprice"]
            profit = data[key][key_2]["profit"]

            # each stock profit or loss and holdings
            # if not stocks_capital:
            #     stocks_capital = data[key]
            
            # if key_2 in stocks_capital:
            #     print(stocks_capital, key_2, stocks_capital[key_2])
            #     stocks_capital[key_2]["stocks"] = stocks_capital[key_2]["stocks"] + stocks
            #     stocks_capital[key_2]["avgprice"]
            #     stocks_capital[key_2]["profit"] = stocks_capital[key_2]["profit"] + profit
            # else:
            #     stocks_capital[key_2] = {"stocks": stocks}
            #     stocks_capital[key_2] = {"avgprice": price}
            #     stocks_capital[key_2] = {"profit": profit}

            amount = 0
            if stocks > 0.009:
                amount = (price * decimal.Decimal(stocks)) + profit
                holding += amount

            stock[key_2] = {
                "holding": amount, "profit": data[key][key_2]["profit"]
            }
        total_holding += holding
        portfolio_data[key] = stock
        portfolio_data[key]["holding"] = locale.currency(holding, grouping=True)
    portfolio_data["holding"] = locale.currency(total_holding, grouping=True)
    portfolio_data['stocks'] = stocks_capital
    return portfolio_data

def get_stock_data(transactions):
    data = {}
    for tran in transactions:
        tran_price = tran.price
        if tran.stock.price:
            tran_price = tran.stock.price
        if tran.stock.currency == "USD":
            tran_price = tran.price * decimal.Decimal(1.34)
        tran_stocks = tran.quantity
        tran_type = tran.transaction_type

        if tran.portfolio.id in data:
            if tran.stock.symbol in data[tran.portfolio.id]:

                stocks = data[tran.portfolio.id][tran.stock.symbol]["stocks"]
                profit = data[tran.portfolio.id][tran.stock.symbol]["profit"]
                avg_price = data[tran.portfolio.id][tran.stock.symbol]["avgprice"]
                
                if tran_type == "BY" or tran_type == "DR":
                    prev_total = avg_price * decimal.Decimal(stocks)
                    current_total = tran_price * decimal.Decimal(tran_stocks)
                    total_share = stocks + tran_stocks
                    avg_cost_per_share = (prev_total + current_total) / decimal.Decimal(total_share)
                    data[tran.portfolio.id][tran.stock.symbol]['stocks'] = total_share
                    data[tran.portfolio.id][tran.stock.symbol]['avgprice'] = avg_cost_per_share
                elif tran_type == "SL":
                    # profit = sell price - price * sell stocks
                    # profit = old_profit - curr_profit
                    # stocks = stocks - sell stocks
                    gain_or_loss = (tran_price - avg_price) * decimal.Decimal(tran.quantity)
                    # print(tran_price, avg_price, tran.quantity, tran.transaction_date)
                    final_gain_or_loss = profit + gain_or_loss
                    data[tran.portfolio.id][tran.stock.symbol]["profit"] = final_gain_or_loss
                    data[tran.portfolio.id][tran.stock.symbol]["stocks"] = stocks - tran.quantity
            else:
                data[tran.portfolio.id][tran.stock.symbol] = {
                    "stocks": tran.quantity, "profit": 0, "avgprice": tran_price
                }
        else:
            data[tran.portfolio.id] = {tran.stock.symbol: {
                    "stocks": tran.quantity, "profit": 0, "avgprice": tran_price
                }}
        # print(data)
    # print("!!!!!!!!!!!!!!!!!!!!!!!!", data)
    return data

def dividend_information(transcations, year_count):
    trans = transcations.filter(transaction_type = "DR")
    data = find_dividend_reveived_monthly(trans, year_count)

    total_dividend = data['total_dividend']
    dividend_by_months = data['dividend_by_montly'] 
    dividend_by_stcoks = data['dividend_by_stock'] 
    
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
    }

def find_dividend_reveived_monthly(objects, period=None):
    dividend_received_each_month = {}
    total_received_dividend = 0
    dividend_received_by_stock = {}

    for tran in objects:
        # total dividend reveived
        total_received_dividend += tran.total_price

        # dividend recevied as monthly or annually
        if period and period > 2:
            year = tran.transaction_date.year
            key = str(year)
            if key in dividend_received_each_month:
                dividend_received_each_month[key] += tran.total_price
            else:
                dividend_received_each_month[key] = tran.total_price
        else:
            month = tran.transaction_date.strftime("%B")
            year = tran.transaction_date.year
            key = str(month) +" " + str(year)
            if key in dividend_received_each_month:
                dividend_received_each_month[key] += tran.total_price
            else:
                dividend_received_each_month[key] = tran.total_price
                
        # dividend recevied by each stock
        stock_as_key = tran.stock.symbol
        if stock_as_key in dividend_received_by_stock:
            dividend_received_by_stock[stock_as_key] += tran.total_price
        else:
            dividend_received_by_stock[stock_as_key] = tran.total_price
        
    return {
        "total_dividend": total_received_dividend,
        "dividend_by_montly": dividend_received_each_month,
        "dividend_by_stock": dividend_received_by_stock
    }