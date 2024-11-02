from django.urls import path
from . import views

urlpatterns = [
    # path('stock/<str:stock_ticker>/', views.stock_detail, name="stock_detail"),

    # get emails using celery
    path('get_emails/', views.get_emails, name='get_emails'),
    
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
    
    # protfolio-management
    path(
        'portfolio-<str:portfolio_slug>/id=<int:portfolio_id>/protfolio-management/',
        views.single_portfolio_management, 
        name='single_portfolio_management'
    ),

    path(
        'protfolio-management/',
        views.homepage_portfolio_management, 
        name='homepage_portfolio_management'
    ),
    

    path('', views.index, name="index"),
]