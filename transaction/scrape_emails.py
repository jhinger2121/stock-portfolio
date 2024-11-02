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
import time
PATH_CREDS = Path(__file__).resolve().parent.parent
NUMBER_OF_EMAILS_TO_SEARCH = 700


class GmailService:
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
        res = []
        # this is only limited to 500 emails even if maxResults=800
        # to fix this use "before:2023/06/01" to get furthur emails
        quaries = ['from:support@wealthsimple.com before:2023/08/01', 'from:support@wealthsimple.com before:2023/11/01', 
             'from:support@wealthsimple.com before:2024/03/01', 'from:support@wealthsimple.com before:2023/07/01',
             'from:support@wealthsimple.com']
        for query in quaries:
            results = self.service.users().messages().list(
                maxResults=NUMBER_OF_EMAILS_TO_SEARCH, userId='me', q=query).execute()
            messages = results.get('messages')
            messages.reverse()
            res += messages
        # result = self.service.users().messages().list(
        # 	maxResults=NUMBER_OF_EMAILS_TO_SEARCH, userId='me',
        # 	q="from:support@wealthsimple.com"
        # 	).execute()
        # results = self.service.users().messages().list(
        # 	maxResults=600, userId='me', q='from:support@wealthsimple.com before:2023/06/01').execute()
        # messages = results.get('messages')
        # print(messages)
        # messages.reverse()
        return res
        

    def get_email_data(self, service, msg):
        time.sleep(.2)
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
            'email_id': msg['id']}

class EmailParser:
    REMOVABLE_CHARS = ["*", " ", "\r", "$", ",", "US"]
    CHAR_R = ["*", " ", "\r", "$", ","]

    @staticmethod
    def extract_field(pattern, text, rem_char=None, group_index=2, default=""):
        match = re.search(pattern, text)
        if match:
            value = match.group(group_index)
            if rem_char:
                for char in rem_char:
                    value = value.replace(char, "")
            return value
        return default

    @staticmethod
    def parse_time(time_str):
        try:
            date_format = "%B %d, %Y %I:%M %p"
            cleaned_date_string = time_str.strip()[:-4]
            return datetime.strptime(cleaned_date_string, date_format)
        except Exception as e:
            print(f"Error parsing time: {e}")
        return None

    def process_body(self, body_string):
        # print("!!!!!!!",body_string)
        data = {}
        data['account'] = self.extract_field(r"(\bAccount:)\s*(.*[\w]+.*)", body_string, self.REMOVABLE_CHARS)
        data['shares'] = self.extract_field(r"(\bShares:)\s*(.*[\d]+.*)", body_string, self.REMOVABLE_CHARS)
        data['avg_price'] = self.extract_field(r"(\bAverage price:)\s*(.*[\d]+.*)", body_string, self.REMOVABLE_CHARS)
        data['total_cost'] = self.extract_field(r"(\bTotal (cost|value):)\s*(.*[\d]+.*)", body_string, self.REMOVABLE_CHARS, group_index=3)
        data['symbol'] = self.extract_field(r"(\bSymbol:)\s*(.*[\w]+.*)", body_string, self.CHAR_R)
        type_ = self.extract_field(r"(\bType:)\s*(.*[\w]+.*)", body_string).replace("*", "")
        if "Buy" in type_:
            type_ = "Buy"
        elif "Sell" in type_:
            type_ =  "Sell"
        data['type'] = type_
        time_str = self.extract_field(r"(\bTime:)\s*(.*[\w]+.*)", body_string).replace("*", "")
        data['time'] = self.parse_time(time_str)
        return data

    def process_body_1(self, body_string):
        # print("!!!!!!!",body_string)
        data = {}
        data['account'] = self.extract_field(r"(\bAccount:)\s*(.*[\w]+.*)", body_string, self.REMOVABLE_CHARS)
        data['shares'] = self.extract_field(r"(\bShares:)\s*(.*[\d]+.*)", body_string, self.REMOVABLE_CHARS)
        data['avg_price'] = self.extract_field(r"(\bAmount:)\s*(.*[\d]+.*)", body_string, self.REMOVABLE_CHARS)
        data['total_cost'] = self.extract_field(r"(\bTotal (cost|value):)\s*(.*[\d]+.*)", body_string, self.REMOVABLE_CHARS, group_index=3)
        data['symbol'] = self.extract_field(r"(\bSymbol:)\s*(.*[\w]+.*)", body_string, self.CHAR_R)

        type_ = self.extract_field(r"(\bType:)\s*(.*[\w]+.*)", body_string).replace("*", "")
        
        data['type'] = "Dividend Reinvestment"

        time_str = self.extract_field(r"(\bTime:)\s*(.*[\w]+.*)", body_string).replace("*", "")
        data['time'] = self.parse_time(time_str)
        return data
    
    def process_email(self, email_data):
        headers = email_data['headers']
        decoded_data = email_data['decoded_data']
        email_id = email_data['email_id']
        subject, sender, date = "", "", ""
        for d in headers:
            if d['name'] == 'Subject':
                subject = d['value']
            if d['name'] == 'From':
                sender = d['value']
            if d['name'] == 'Date':
                date = d['value']

        soup = BeautifulSoup(decoded_data, "html.parser")
        body_string = soup.get_text()

        cleaned_date_string = date.split('(')[0].strip()

        # Parse the date string into a datetime object
        parsed_date = datetime.strptime(cleaned_date_string, '%a, %d %b %Y %H:%M:%S %z')
        data = {
            'subject': subject,
            'sender': sender,
            'date': parsed_date
        }
        # print(body_string)
        data['id'] = email_id
        if "Your order has been filled" in body_string:
            data.update(self.process_body(body_string))
            print("buy sell", data)

            return data
        elif "You earned a dividend" in body_string:
            data.update(self.process_body_1(body_string))
            print("data!!!!!!!!!!", data)
            return data
        

        return None
    
class GmailAnalyzerSingleton:
    _instance = None

    @staticmethod
    def get_instance(scopes):
        if GmailAnalyzerSingleton._instance is None:
            GmailAnalyzerSingleton._instance = GmailService(scopes)
        return GmailAnalyzerSingleton._instance
