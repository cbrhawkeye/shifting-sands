from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import sys
import re

from pprint import pp

url = sys.argv[1]
fqdn = url.split('//')[1]

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--headless")
options.add_argument("--user-data-dir=/tmp/chrome-selenium")
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(10)

def process_browser_log_entry(entry):
    response = json.loads(entry['message'])['message']
    return response

driver.get(url)

browser_log = driver.get_log('performance')
events = [process_browser_log_entry(entry) for entry in browser_log]
#events = [event for event in events if event['method'] == 'Network.responseReceived' or event['method'] == 'Network.requestWillBeSent']
events = [event for event in events if 'Network.' in event['method']]

# Dump JSON to file
out = open("output_%s.json" % fqdn, "w")
out.write(json.dumps(events))
out.close()

driver.quit()

documents = {}
for e in events:
    if 'requestId' in e['params']:
        requestId = e['params']['requestId']
        if requestId not in documents:
            documents[requestId] = {}
    method = e['method']

    if e['method'] == 'Network.requestWillBeSent':
        # Required keys: document_url, method, url
        documents[requestId]['request'] = {
            'document_url': e['params']['documentURL'],
            'method': e['params']['request']['method'],
            'url': e['params']['request']['url'],
            'headers': e['params']['request']['headers']
        }

    elif e['method'] == 'Network.responseReceived':
        # Required keys: headers['content-type'], url, type, status
        documents[requestId]['response'] = {
            'status': e['params']['response']['status'],
            'url': e['params']['response']['url'],
            'type': e['params']['type']
        }
        # Convert all header keys to lowercase
        headers = e['params']['response']['headers']
        headers = {k.lower():v for k,v in headers.items()}
        if 'content-type' in headers:
            documents[requestId]['response']['content-type'] = headers['content-type']

for d in documents:
    # Remove anything served by the browser itself via "chrome://"
    if 'request' in documents[d]:
        if re.match('^http.*', documents[d]['request']['document_url']) == None:
            # Cannot delete key during iteration so just empty it
            del documents[d]['request']
    if 'response' in documents[d]:
        if re.match('^http.*', documents[d]['response']['url']) == None:
            # Cannot delete key during iteration so just empty it
            del documents[d]['response']

pp(documents)
out = open("network_%s.json" % fqdn, "w")
out.write(json.dumps(documents))
out.close()
