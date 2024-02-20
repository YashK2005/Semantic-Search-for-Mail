#this file gets the emails from the gmail account
#it then parses the emails (strip html tags, remove newlines, etc.)
#and saves the emails as a .csv file

#for authentication and getting emails
import csv
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.auth.exceptions
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

# for parsing emails
from email import policy
from email.parser import Parser
import base64
from bs4 import BeautifulSoup

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

creds = None
# The file token.json stores the user's access and refresh tokens

if os.path.exists('token.json'):
    try:
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        creds.refresh(Request())
    except google.auth.exceptions.RefreshError as error:
        # if refresh token fails, reset creds to none.
        creds = None
        print(f'An error occurred: {error}')

# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())


emails = [] # indvidiual raw emails stored
CUT_OFF = 100 # maximum number of emails to be downloaded
try:
  service = build("gmail", "v1", credentials=creds)
  gmail_messages = service.users().messages()
  
  has_next_token = True
  next_token = None
  count = 0
  while(has_next_token):
    results = gmail_messages.list(userId='me', pageToken=next_token).execute()
    messages = results["messages"]
    if "nextPageToken" in results:
      next_token = results["nextPageToken"]
    else:
      next_token = None
      has_next_token = False
    size_estimate = results["resultSizeEstimate"]
    print(f"next_token {next_token}, size estimate: {size_estimate}")
    for msg in messages:
      msg_dict = gmail_messages.get(userId='me', id=msg['id'], format='raw').execute()
      emails.append(msg_dict)
    count += len(emails)
    if len(emails) > CUT_OFF:
      has_next_token = False
      next_token = None
except HttpError as error:
  print(f'An error occurred: {error}')

# parser for parsing emails

parser = Parser(policy=policy.default)

# reference content dictionary
content_dictionary = {
}

# parsing email content
counter = 0
for email in emails:
    try:
        msg_str = base64.urlsafe_b64decode(email['raw'].encode('ASCII'))
    
        subject = from_email = to_email = None
        msg = parser.parsestr(msg_str.decode('utf-8'))
        for key in msg.keys():
            if key == "Subject":
                subject = msg.get_all("Subject")
            if key == "From":
                from_email = msg.get_all("From")
            if key == "To":
                to_email = msg.get_all("To")
        #print(f"from: {from_email}, subject: {subject}")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                content = part.get_content()
                soup = BeautifulSoup(content, 'html.parser')
                clear_content = soup.get_text(separator=' ', strip=True)
                cleaned_mssg_body = clear_content.replace('\n', '').replace('\r', '')
                content_dictionary[counter] = {
                    "id": email["id"],
                    "subject": subject,
                    "from": from_email,
                    "to": to_email,
                    "body": cleaned_mssg_body,
                    #"snippet": email["snippet"]
                }
                counter += 1
    except:
        counter += 1
        print("Eror in parsing email")
#print(content_dictionary)


#exporting the values as a .csv
with open('email.csv', 'w', encoding='utf-8', newline = '') as csvfile: 
    fieldnames = ['id','subject','from','to','body']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter = ',')
    writer.writeheader()
    for val in content_dictionary.values():
    	writer.writerow(val)
