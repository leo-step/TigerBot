from bs4 import BeautifulSoup
from email.message import EmailMessage
import os
import pandas as pd
import random
import re
import requests
import smtplib
import ssl

def get_soup(email, username):
    url = "https://www.princeton.edu/search/people-advanced?e={}&ef=eq".format(email)
    text = requests.get(url).text
    soup = BeautifulSoup(text, features="lxml")
    if soup.find("p", {"class" : "padme"}) != None:
        url = "https://www.princeton.edu/search/people-advanced?i={}&if=eq".format(username)
        text = requests.get(url).text
        soup = BeautifulSoup(text, features="lxml")
    if soup.find("p", {"class" : "padme"}) != None:
        return None
    return soup

def is_valid_student(email):
    username, domain = email.split('@')
    print("Username: " + username)
    print("Domain: " + domain)
    if domain != "princeton.edu":
        print("Invalid domain")
        return False
    soup = get_soup(email, username)
    if soup == None:
        print("No results found on APS")
        return False
    department = soup.find("div", {"class" : "people-search-result-department"}).text.strip()
    print("Department: " + department)
    if department != "Undergraduate Class of 2025":
        print("Invalid year")
        return False
    APS_email = soup.find("div", {"class" : "people-search-email"}).text.strip()
    netID = soup.findAll("span", {"class" : "expanded-details-value"})[-1].text.strip()
    print("APS email: " + APS_email)
    print("NetID: " + netID)
    if APS_email != email and username != netID:
        print("Invalid email/netID match")
        return False
    return True

def is_valid_email(email):
    email = email.strip()
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.match(regex, email) and is_valid_student(email):
        print("Sending email to " + email)
        return True
    return False

def generate_code(length, alphabet):
    code = ""
    for i in range(length):
        code += alphabet[random.randint(0, len(alphabet)-1)]
    return code

def send_email(email, code):
    msg = EmailMessage()
    msg["To"] = email
    msg["From"] = os.environ.get("EMAIL")
    msg["Subject"] = "Princeton C/O 2025 Discord Verification Code"
    msg.set_content("Your verification code is: {}".format(code))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
        server.login(msg["From"], os.environ.get("EMAIL_PASSWORD"))
        server.send_message(msg)
        print("Sent email")
        server.quit()

def verify_email(email):
    if is_valid_email(email):
        code = generate_code(20, "abcdefghijklmnopqrstuvwxyz1234567890")
        send_email(email, code)
        print("Enter the verification code you received by email: ", end="")
        if code == input():
            print("Verified")
            return True
        else:
            print("Not verified")
            return False
    else:
        print("Not verified")
        return False

if __name__ == "__main__":
    print(verify_email("leo.stepanewk@gmail.com"))