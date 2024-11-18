# **Personal Stock Portfolio Management System**  

A web-based application designed to help investors like me automate and streamline the tracking of stock and ETF investments. This system calculates profits, losses, and dividends, providing real-time insights into portfolio performance.  

---

## **Features**  

### Core Functionalities  
- **Real-Time Data Tracking**:  
  Fetches live stock data using [YFinance](https://pypi.org/project/yfinance/) to update portfolio performance metrics.  

- **Profit and Loss Analysis**:  
  Tracks both realized and unrealized gains/losses for individual stocks and ETFs.  

- **Dividend Management**:  
  Logs and aggregates total dividends paid per stock.  

- **Tax Integration**:  
  Accounts for a 15% withholding tax on U.S. stocks in Canada, with automatic exemptions for RRSP accounts.  

- **Responsive Dashboard**:  
  A clean and intuitive interface with charts and tables to visualize portfolio performance.  

---

## **Technical Overview**  

### Tech Stack  
- **Backend**: Django (Python)  
- **Frontend**: HTML, CSS, Bootstrap 5, Javascript
- **Database**: PostgreSQL  
- **APIs**: [YFinance](https://pypi.org/project/yfinance/) for stock data retrieval  

### Architecture  
- MVC (Model-View-Controller) pattern for modular and scalable development.  

### Deployment  
- Local deployment for personal use; future plans for scalability to cloud platforms like AWS or Heroku.  

---

## **How to Install and Run Locally**  

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/yourusername/stock-portfolio.git
   cd stock-portfolio

2. **Install Dependencies**  
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt

3. **Apply Migrations**
   ```bash 
   python manage.py makemigrations
   python manage.py migrate

5. **Run the Server**
   ```bash
   python manage.py runserver

