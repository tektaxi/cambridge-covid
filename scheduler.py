from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import tweepy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
import lxml
import smtplib, ssl

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--headless')
driver = webdriver.Chrome(options=chrome_options)

# api variables
consumer_key = ""
consumer_secret = ""
access_token = ""
access_secret = ""



# get html from site k
def getHtml(url, element, target_html):
    driver.get(url)
    target_working = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, target_html)))

    if target_working is not None:
        if element is not None:
            driver.find_element(By.XPATH, element).click()
            time.sleep(2)
        time.sleep(2)
        soup_file = driver.page_source
        soup = BeautifulSoup(soup_file, features="lxml")

    return soup


# parse html for data we need
def parseData(selection):
    if selection == "University":
        url = "https://cityofcambridge.shinyapps.io/COVID19/"
        element_xpath = ('//a[@href="#shiny-tab-university"]')
        target_data = "metric_total"
        soup = getHtml(url, element_xpath, target_data)

        raw_data = soup.findAll('div', class_="rt-td rt-align-left")

        parsed_text = []
        parsed_data = []
        counter = 0
        for item in raw_data:
            item_text = item.get_text()
            if counter % 2 == 0:
                parsed_text.append(item_text)
            else:
                parsed_data.append(item_text)
            counter += 1
        data_dict = dict(zip(parsed_text, parsed_data))

        raw_text = []
        time_string = ""

    elif selection == "cpsd":
        url = "https://www.cpsd.us/covid19data"
        element_xpath = None
        target_data = "ctl00_ContentPlaceHolder1_ctl14_divTabs_0"
        soup = getHtml(url, element_xpath, target_data)

        cps_data = soup.select("div#ctl00_ContentPlaceHolder1_ctl14_divTabs_0 strong")
        # These numbers are the static data from before winter break
        existing = [50, 6, 36, 5, 16, 0, 4]
        existing_num = 0

        parsed_data = []
        parsed_text = ["CPS_confirmed", "in-school-transmission", "CPS_staff", "CPS_staff_onsite_testing",
                       "CPS_students", "CPS_students_onsite_testing", "CPS_athletes"]
        for item in cps_data:
            raw_data = item.get_text()
            if raw_data.isdigit():
                data = int(raw_data) + existing[existing_num]
                parsed_data.append(data)
                existing_num += 1

        data_dict = dict(zip(parsed_text, parsed_data))
        print(data_dict)

        time_string = ""
    else:
        url = "https://cityofcambridge.shinyapps.io/COVID19/"
        element_xpath = None
        target_data = "metric_total"

        soup = getHtml(url, element_xpath, target_data)

        raw_timestamp = soup.find('div', id='text_timestamp')
        time_string = f"{raw_timestamp.get_text()}"

        raw_data = soup.findAll('span', class_='info-box-number')
        raw_text = soup.findAll('span', class_='info-box-text')

        parsed_data = []
        parsed_text = []
        # write about this list for the answers
        for item in raw_data:
            parsed_data.append(item.get_text())
        for jtem in raw_text:
            parsed_text.append(jtem.get_text())
        data_dict = dict(zip(parsed_text, parsed_data))
        print(data_dict)

    return time_string, data_dict
# print(data_dict)


# main code
print('loading')
data = parseData("main-stats")
university_data = parseData("University")
#cpsd_data = parseData("cpsd")

# quit after all data has been called
driver.quit()

data_dict = data[1]
date_updated = data[0]
uni_data_dict = university_data[1]
#cpsd_data_dict = cpsd_data[1]
# print(date_updated)
# print(data_dict)
# print(uni_data_dict)
# print(cpsd_data_dict)


# Create a tweet
print()
print("Here is the tweet being sent")
print()

tweet1 = (f'''Latest COVID-19 data from Cambridge, MA.
{date_updated}
New Cases Today: {data_dict["Newly Reported Cases Today*"]}
Today's Deaths: {data_dict["Newly Reported Deaths Today*"]}
Total Cases: {data_dict["Cumulative Cases"]}
Total Deaths: {data_dict["Total Deaths"]}
Positive Test Rate (last 14 days): {data_dict["Positive Tests*** Over the Last 14 Days"]}
Cases per 100k (7 day average): {data_dict["Confirmed Cases per 100,000 residents** 7 Day Moving Average"]}
#CambMA
''')

'''#Staff: {cpsd_data_dict["CPS_staff"]}
#Students: {cpsd_data_dict["CPS_students"]}
#Student Athletes: {cpsd_data_dict["CPS_athletes"]}
#Confirmed In-School Transmission: {cpsd_data_dict["in-school-transmission"]}}'''

tweet2 = (f'''Latest COVID-19 vaccination data from Cambridge, MA 
Fully Vaccinated Cambridge Residents: {data_dict['Fully Vaccinated Cambridge Residents****']}
Residents With One Vaccine Doses: {data_dict["Residents with One+ Vaccine Doses****"]}
Residents With Booster: {data_dict["Residents with Booster****"]}
#CambMA
''')

print("tweet 1")
print()
print(tweet1)
print()
print("tweet 2")
print(f"tweet 2 length: {len(tweet2)}")
print()
print(tweet2)

# API code from realpython.com
# Authenticate to Twitter
error_message = None
port = 587  # For starttls
smtp_server = "smtp.dreamhost.com"
reciever_email = "notifications@cambridgecovid.tavienpollard.com"
sender_email = "admin@cambridgecovid.tavienpollard.com"

password = ""
message = """\
From: admin@cambridgecovid.tavienpollard.com
Subject: Tweepy Error
There was an error with the tweet
Error: {error_message}"""



auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

# Create API object
api = tweepy.API(auth)
try:
    api.verify_credentials()
    print("Authentication OK")
except:
    print("Error during authentication")

# send tweet
try:
    api.update_status(tweet1)
except Exception as err:
    error_message = err


message = f"""\
From: admin@cambridgecovid.tavienpollard.com
Subject: Tweepy Error 
There was an error with the tweet, {str(error_message)}
"""
print(message)
context = ssl.create_default_context()
if error_message is not None:
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, reciever_email, message)
        print("sent")
        