from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from datetime import datetime
from django.db.models import Prefetch
from django.core.paginator import Paginator

from main.utils import dividend_information, find_dividend_reveived_monthly, stocks_info
from stocks.forms import TransactionForm, StockForm
from transaction.models import Transaction
from portfolioitem.models import PortfolioItem
from portfolio.models import Portfolio
from stocks.models import Stock
from alert.models import Alert
from transaction.tasks import add, process_gmail_emails
from stocks.tasks import get_data, update_price, reset_data, update_stock_information
# What is the difference between model and form validation in Django?
# work on scraper b4 that study design pattener link is in google chrome
# or work on template to show data (start with designing)
# start working with celery or with making reaquest with request
# 
# Scraper

# IMPORTANT: get dividend amount  each month recieved for last 2 years
#            and how much each stock paid from the dividend
#            and so far how much dividend recived so far in portfolio
# IMPORTANT: use fetch to get holding amount so you don't have repeate
#            everything again and again, we can use this data on multiple
#            locations. (do this later when i almost done with the project)
# IMPORTANT: show each stock info like how much capital gain and lost we 
#            had, dividend received so far, this can be done with the above
#            feature(holding amount)
#IMPORTANT: using "get_transactions_information" function we can alos have
#           total invested amount in portpolio and then we can calculate 
#           performances, moreover, we can also calculate total all total
#           amount (44,479) and its performance
# what to show -- capital loss/gain on homepage, all holdings
MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
]

@login_required
def get_transactions_information(request, portfolio_id=None, year_count=None):
    # detail page request
    if portfolio_id and year_count:
        transcations = Transaction.objects.select_related(
            "stock", "portfolio").filter(user=request.user,
            portfolio__id = portfolio_id
        )
        data = dividend_information(transcations, year_count)
        print("!!!!!!!!!!!!!!", "detail page")
        data_1 = stocks_info(transcations)
        return JsonResponse({
            "total_divided_received": data["total_dividend_received"],
            "dividend": data["dividend"],
            "data": data_1,
        })
    # if reqeust came from homepage 
    elif year_count:
        print("!!!!!!!!!!!!!!", "hompage")
        transcations = Transaction.objects.select_related(
            "stock", "portfolio").filter(user=request.user)
        
        # Charts data(KEYS: total_dividend_received, dividend, dividend_by_stocks)
        data = dividend_information(transcations, year_count)
        
        data_1 = stocks_info(transcations)
        return JsonResponse({
            "total_divided_received": data["total_dividend_received"],
            "dividend": data["dividend"],
            "data": data_1,
        })

    # get total holding amount

# @login_required
# def dividend_received(request, portfolio_slug=None, portfolio_id=None, year_count=None):
#     print("wrongs")
#     data = {}
#     if portfolio_id and year_count:
#         transactions = Transaction.objects.filter(
#             user=request.user, portfolio__id=portfolio_id, transaction_type="DR"
#         )
#         data = find_dividend_reveived_monthly(transactions, year_count)
         
#     elif year_count:
#         transcations = Transaction.objects.filter(transaction_type = "DR")
#         data = find_dividend_reveived_monthly(transcations, year_count)

#     total_dividend = data['total_dividend']
#     dividend_by_months = data['dividend_by_montly'] 
    
#     months = year_count * 12
#     dividend_months = []
#     dividend_values = []
#     count = 0
#     if year_count <=2:
#         for key in dividend_by_months:
#             if count == months:
#                 break
#             dividend_months.append(key)
#             dividend_values.append(dividend_by_months[key])
#     elif year_count > 2:
#         for key in dividend_by_months:
#             if count == year_count:
#                 break
#             dividend_months.append(key)
#             dividend_values.append(dividend_by_months[key])

#     return JsonResponse({
#         "total_divided_received": total_dividend,
#         "dividend": {"months": dividend_months, "values": dividend_values}
#     })
        

@login_required
def dividend_by_months(request, portfolio_slug, portfolio_id, months=6):
    portfolio = get_object_or_404(
        Portfolio, id=portfolio_id, user = request.user
    )
    dividend_earning = []
    dividend_month = []
    msg = []

    for item in portfolio.portfolioitem_set.all():
        foo = item.dividend_by_months(months)
        stock_div = []
        stock_month = []
        for data in foo:
            if "message" in data:
                msg.append(data["message"])
                stock_div = []
                stock_month = []
            else:
                stock_div.append(data["dividend"])
                stock_month.append(data["month"])

        if not dividend_earning and not dividend_month:
            dividend_month = stock_month
            dividend_earning = stock_div
        elif dividend_earning and stock_div:
            for i in range(len(dividend_earning)):
                dividend_earning[i] = dividend_earning[i] + stock_div[i]

    return JsonResponse({
        "dividend": dividend_earning,
        "months": dividend_month,
        "message": msg
    })

@login_required
def DRIP_calculator(request, portfolio_slug, portfolio_id=1, year_count=2):
    portfolio = get_object_or_404(
        Portfolio, id=portfolio_id, user = request.user)

    lvl = []
    for i in range(year_count):
        lvl += MONTHS

    msg = []
    total_earning = []
    for item in portfolio.portfolioitem_set.all():
        dividend_earning_list = item.calculate_DRIP(year_count)
        # print(dividend_earning_list)
        if not dividend_earning_list:
            msg.append(f"{item.stock.symbol}")
        if not total_earning:
            single_stock = []
            for i in range(len(dividend_earning_list)):
                amount = dividend_earning_list[i]['amount']
                left = dividend_earning_list[i]['left']
                total_earning.append(amount + left)
                single_stock.append(amount + left)
        else:
            for i in range(len(dividend_earning_list)):
                val = total_earning[i]
                amount = dividend_earning_list[i]['amount']
                left = dividend_earning_list[i]['left']
                single_stock.append(amount + left)
                if left:
                    total_earning[i] = val + amount + left
                else:
                    total_earning[i] = val + amount
    
    return JsonResponse({
        "data" : total_earning,
        "message": msg,
        "labels": lvl,
        "dividend_per_stock": single_stock,
    })

@login_required
def transactins(request, portfolio_id=None):
    transactions = None
    context = {}
    if portfolio_id:
        transactions = Transaction.objects.prefetch_related(
            Prefetch('portfolio', 
                    queryset=Portfolio.objects.filter(user=request.user)),
            Prefetch('stock', queryset=Stock.objects.all())
        ).filter(user=request.user, portfolio__id = portfolio_id)
        portfolio = get_object_or_404(Portfolio, id = portfolio_id)
        context["portfolio"] = portfolio
    else:
        transactions = Transaction.objects.prefetch_related(
                Prefetch('portfolio', 
                        queryset=Portfolio.objects.filter(user=request.user)),
                Prefetch('stock', queryset=Stock.objects.all())
            ).filter(user=request.user)

    paginator = Paginator(transactions, 25)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context["page_obj"] = page_obj
    return render(request, 'stocks/transactions.html', context)


@login_required
def stock_detail(request, stock_ticker):
    portfolio_item = get_list_or_404(
        PortfolioItem, stock__symbol = stock_ticker,
        portfolio__account__user = request.user
    )
    print(Alert.objects.activate_tracker())

    stock = get_object_or_404(Stock, symbol = stock_ticker)
    context = {'portfolio_item': portfolio_item, 'stock': stock}
    return render(request, 'stocks/stock_detail.html', context)


@login_required
def index(request):
    # reset_data()
    # get_data()
    # update_price()
    # update_stock_information()
    # process_gmail_emails()
    portfolios = Portfolio.objects.prefetch_related(
        Prefetch('portfolioitem_set', 
                 queryset=PortfolioItem.objects.filter(user=request.user))
    ).filter(user=request.user)
    transactions = Transaction.objects.latest_15()
    # portfolio_items = PortfolioItem.objects.filter(user=request.user)
    # for portfolio in portfolios:
        # portfolio.analysis = portfolio.portfolio_gain_or_loss_and_holdings(request.user, portfolio)
    # portfolio = get_list_or_404(Portfolio, account__user = request.user)
    # for port in portfolio:
    #     port.analysis = port.portfolio_items_information()
    context = {"portfolios": portfolios, "transactions": transactions}
    return render(request, 'stocks/dashboard.html', context)

@login_required
def stock_detail(request, portfolio_slug, portfolio_id, stock_symbol):
    port = Portfolio.objects.get(id=portfolio_id)
    stock = Stock.objects.get(symbol = stock_symbol)
    trans = Transaction.objects.filter(user=request.user, portfolio = port, stock = stock)
    content = {"trans": trans}
    return render(request, 'stocks/stock_detail.html', content)
    

@login_required
def portfolio_detail(request, portfolio_slug, portfolio_id, stock_symbol=None):
    try:
        portfolio = Portfolio.objects.prefetch_related(
            Prefetch('portfolioitem_set', 
                    queryset=PortfolioItem.objects.filter(user=request.user)),
            Prefetch('transaction_set', 
                    queryset=Transaction.objects.filter(
                        user=request.user, portfolio__pk = portfolio_id)),
        ).get(pk=portfolio_id, user = request.user)

        portfolio.analysis = portfolio.portfolio_gain_or_loss_and_holdings(request.user, portfolio)
    except Portfolio.DoesNotExist:
        raise Http404("No Portfolio matches the given query.")
    content = {"portfolio": portfolio}
    
    # drft calculator
    if stock_symbol:
        stock = get_object_or_404(Stock, symbol=stock_symbol)
    return render(request, 'stocks/portfolio_detail.html', content)


def submit_transaction(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            portfolio = form.cleaned_data['portfolio']
            stock = form.cleaned_data['stock']
            quantity = form.cleaned_data['quantity']
            price = form.cleaned_data['price']
            transaction_type = form.cleaned_data['transaction_type']
            commission = form.cleaned_data['commission']

            print(portfolio, portfolio.id, "!!!!!!!!!!")
            PortfolioItem.objects.submit_transaction(
                portfolio, stock, quantity, price, 
                transaction_type, commission
            )
            form.save()

            return redirect(reverse("submit_transaction"))
    else:
        form = TransactionForm()

    return render(request, "stocks/add_stock_data.html", {"form": form})

def add_stock(request):
    if request.method == "POST":
        form = StockForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse("/thanks/")
    else:
        form = StockForm()
    return render(request, "stocks/add_stock_data.html", {"form": form})
