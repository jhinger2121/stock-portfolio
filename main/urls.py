from django.urls import path
from . import views

urlpatterns = [
    # path('stock/<str:stock_ticker>/', views.stock_detail, name="stock_detail"),

    path(
        'portfolio-<str:portfolio_slug>/id=<int:portfolio_id>/', 
        views.portfolio_detail, 
        name='portfolio_detail'
    ),

    # TRANSACTIONS URLS
    path('all-transactions/', views.transactins, name='transactins'),
    path('all-transactions/<int:portfolio_id>/', 
         views.transactins, name='transactins'),


    # FETCH API URLS
    path(
        'portfolio-<str:portfolio_slug>/id=<int:portfolio_id>/DRIP-year-<int:year_count>/',
        views.DRIP_calculator, 
        name='DRIP_calculator'
    ),
    path(
        'portfolio-<str:portfolio_slug>/id=<int:portfolio_id>/dividend-by-months/',
        views.dividend_by_months, 
        name='dividend_by_months'
    ),
    path(
        'portfolio-id=<int:portfolio_id>/total-dividend/year-<int:year_count>/',
        views.get_transactions_information, 
        name='get_transactions_information'
    ),
    path(
        "total-dividend/year-<int:year_count>/",
        views.get_transactions_information, 
        name='get_transactions_information'
    ),
    # path(
    #     'portfolio-<str:portfolio_slug>/id=<int:portfolio_id>/total-dividend/year-<int:year_count>/',
    #     views.dividend_received, 
    #     name='dividend_received'
    # ),
    

    path('', views.index, name="index"),
]