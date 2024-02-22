# import the required libraries 
from googleapiclient.discovery import build 
from google_auth_oauthlib.flow import InstalledAppFlow 
from google.auth.transport.requests import Request 
import pickle 
import os.path 
import base64 
import email 
from bs4 import BeautifulSoup 
import re
from datetime import datetime
from pathlib import Path
PATH_CREDS = Path(__file__).resolve().parent.parent
NUMBER_OF_EMAILS_TO_SEARCH =5

class GmailAnalyzer:
	def __init__(self, scopes):
		self.SCOPES = scopes
		self.creds = self.get_credentials()
		self.service = None

	def get_credentials(self):
		# Variable creds will store the user access token. 
		# If no valid token found, we will create one. 
		creds = None

		# The file token.pickle contains the user access token. 
		# Check if it exists 
		if os.path.exists(PATH_CREDS / 'token.pickle'): 

			# Read the token from the file and store it in the variable creds 
			with open(PATH_CREDS / 'token.pickle', 'rb') as token: 
				creds = pickle.load(token) 

		# If credentials are not available or are invalid, ask the user to log in. 
		if not creds or not creds.valid: 
			if creds and creds.expired and creds.refresh_token: 
				creds.refresh(Request()) 
			else: 
				flow = InstalledAppFlow.from_client_secrets_file(PATH_CREDS / 'credentials.json', self.SCOPES) 
				creds = flow.run_local_server(port=0) 

			# Save the access token in token.pickle file for the next run 
			with open(PATH_CREDS / 'token.pickle', 'wb') as token: 
				pickle.dump(creds, token)
		
		self.get_service()
		return creds
	
	def get_service(self):
		pass

	def fetch_emails(self):
		self.service = build('gmail', 'v1', credentials=self.creds)
		# this is only limited to 500 emails even if maxResults=800
		# to fix this use "before:2023/06/01" to get furthur emails
		results = self.service.users().messages().list(
			maxResults=70, userId='me', q='from:support@wealthsimple.com before:2024/01/19').execute()
		# result = self.service.users().messages().list(
		# 	maxResults=NUMBER_OF_EMAILS_TO_SEARCH, userId='me',
		# 	q="from:support@wealthsimple.com"
		# 	).execute()
		# results = self.service.users().messages().list(
		# 	maxResults=600, userId='me', q='from:support@wealthsimple.com before:2023/06/01').execute()
		messages = results.get('messages')
		# print(messages)
		messages.reverse()
		return messages
		

	def get_email_data(self, service, msg):
		txt = service.users().messages().get(userId='me', id=msg['id']).execute()
		payload = txt['payload']
		headers = payload['headers']
		parts = payload.get('parts')[0]
		data = parts['body']['data']
		data = data.replace("-", "+").replace("_", "/")
		decoded_data = base64.b64decode(data)
		return {
			'headers': headers,
			'decoded_data': decoded_data,
			'email_id': msg['id']
		}
	
	def process_email(self, email_data):
		data = {}
		headers = email_data['headers']
		decoded_data = email_data['decoded_data']
		email_id = email_data['email_id']
		for d in headers:
			# print(d)
			# print("Date::!!!!!", d['date'])

			if d['name'] == 'Subject': 
				subject = d['value']
			if d['name'] == 'From': 
				sender = d['value']
				# print("Sender", sender)
			if d['name'] == 'Date':
				date = d['value']
				dt = re.search(r"(\d\d)\s*([\w]+)\s*(\d\d\d\d)\s*(\d\d\:\d\d\:\d\d)", date)
				# data['time'] = dt.group(3) + " " + dt.group(2) + " " + dt.group(1) + " " + dt.group(4)

		soup = BeautifulSoup(decoded_data , "html.parser")
		body_string = soup.get_text()
		char_remov = ["*", " ", "\r", "$", ",", "US"]
		x ="Your order has been filled"
		y = "You made a deposit"
		z = "Your transfer is complete"
		# print(body_string)
		if x in body_string:
			data['id'] = email_id
			r_account = re.search(r"(\bAccount:)\s*(.*[\w]+.*)", body_string)
			account = r_account.group(2)
			for char in char_remov:
				account = account.replace(char, "")
			data["account"] = account
			# print("Account:", account)

			# SHARES
			r_shares = re.search(r"(\bShares:)\s*(.*[\d]+.*)", body_string)
			shares = r_shares.group(2)
			for char in char_remov:
				shares = shares.replace(char, "")
			data["shares"] = shares
			# print("Shares:",shares)

			# Average price: *$22.99*
			avg_pric = re.search(r"(\bAverage price:)\s*(.*[\d]+.*)", body_string)
			avg_price = avg_pric.group(2)
			for char in char_remov:
				avg_price = avg_price.replace(char, "")
			data["avg_price"] = avg_price
			# print("Avg price:",avg_price)

			# Total cost: *$6.86*
			ra_total_cost = re.search(r"(\bTotal cost:)\s*(.*[\d]+.*)", body_string)
			if ra_total_cost:
				total_cost = ra_total_cost.group(2)
				for char in char_remov:
					total_cost = total_cost.replace(char, "")
				data["total_cost"] = total_cost
				# print("Total cost:",total_cost)
			else:
				ra_total_cost = re.search(r"(\bTotal value:)\s*(.*[\d]+.*)", body_string)
				total_cost = ra_total_cost.group(2)
				for char in char_remov:
					total_cost = total_cost.replace(char, "")
				data["total_cost"] = total_cost
				# print("Total cost:",total_cost)


			# Symbol: BCE
			r_symbol = re.search(r"(\bSymbol:)\s*(.*[\w]+.*)", body_string)
			symbol = r_symbol.group(2)
			char_r = ["*", " ", "\r", "$", ","]
			for char in char_r:
				symbol = symbol.replace(char, "")
			data["symbol"] = symbol
			# print("symbol:",symbol)

			# Type: Dividend Reinvestment Buy
			r_type = re.search(r"(\bType:)\s*(.*[\w]+.*)", body_string)
			type_ = str(r_type.group(2)).replace("*", "")
			data["type"] = type_
			# print("type:",type_)

			# Time: October 19, 2023 9:49 AM EDT
			time = re.search(r"(\bTime:)\s*(.*[\w]+.*)", body_string)
			time = str(time.group(2)).replace("*", "")
			
			date_format = "%B %d, %Y %I:%M %p"
			cleaned_date_string = time.strip()
			cleaned_date_string = cleaned_date_string[:-4]
			datetime_object = datetime.strptime(cleaned_date_string, date_format)
			data["time"] = datetime_object

			return data
		# elif y in body_string or z in body_string:
		# 	print("you are in", )
		# 	price = re.search(r"(\bAverage price:)\s*(.*[\d]+.*)", body_string)
		# 	print(price)
		else:
			# if it didn't fit it that means its a "You earned a dividend"email which we don't need
			# print("Unable to find the Gmail data")
			return None


# you earned a dividend
# account: TFSA
#Symbol: BCE

# you order has been filled
# Account: TFSA
# Type: Dividend Reinvestment Buy, Market Buy, Market Sell
# Symbol: CALL
# Shares: 2.4126
# Average price: $10.13
# (Total cost: $24.44) feild cahanged to ("Total value": $690) when you sell
# Time: October 11, 2023 10:01 AM EDT

# We’ll automatically reinvest this dividend back into more shares. If its "ON"

# *IMPORTANT -- The goal is to see what i have in the stocks as bought values not the money 
# 				which is setting ideal in the account. So we will not check "You earned a dividend" Emails
# *IMPORTANT -- every time value comes between those stars (*some value*) ex. Shares: *0.3757*
# 				if those stars gone our program will fale.