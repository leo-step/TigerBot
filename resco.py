from bs4 import BeautifulSoup
from difflib import get_close_matches
from config import resco
import mysql.connector
import os
import pandas as pd
import requests

def is_resco_available(netid="ls3841"):
    url = resco["URL_TEMPLATE"].format(netid)
    text = requests.get(url).text
    if resco["KEYWORD"] in text:
        return True
    return False

def get_college(netid):
    if is_resco_available(netid):
        url = resco["URL_TEMPLATE"].format(netid)
        text = requests.get(url).text
        soup = BeautifulSoup(text, features="lxml")
        college = soup.find('span', {"class" : "expanded-details-value"}).text.strip()
        print("Found {} while checking".format(college))
        if college in resco["COLLEGES"]:
            return college
        else:
            return resco["GET_COLLEGE_ERROR"]
    return resco["RESCO_NA"]

def load_roommate_data(db, cursor):
    sql = "SELECT * FROM roommates"
    cursor.execute(sql)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["discordID", "building", "room"])
    return df

def process_roommate_args(args):
    print("Processing roommate args")
    building = None
    room = None
    valid_halls = resco["HALLS"]
    args = list(filter(lambda arg: arg.lower() != "hall" and arg.lower() != "college", args))
    num_args = len(args)
    if num_args != 2:
        return "$match <hall name> <room number>\nUse dashes(-) if there are any spaces in your hall/room name.", building, room
    else:
        building, room = args[0].lower(), args[1].upper()
        if building in ["1939", "1938", "1937", "1927", "1981", "1967", "1915", "1976"]:
            building = "class-of-" + building
        if building == "wendell" and room[0] == 'C':
            building = "wendell-c"
            room = room[1:]
        elif building == "wendell" and room[0] == 'B':
            building = "wendell-b"
            room = room[1:]
        elif building == "wendell-c" and room[0] == 'C':
            room = room[1:]
        elif building == "wendell-b" and room[0] == 'B':
            room = room[1:]
        if building == "baker" and room[0] == 'E':
            building = "baker-e"
            room = room[1:]
        elif building == "baker" and room[0] == 'S':
            building = "baker-s"
            room = room[1:]
        elif building == "baker-e" and room[0] == 'E':
            room = room[1:]
        elif building == "baker-s" and room[0] == 'S':
            room = room[1:]
        if building not in valid_halls:
            close_matches = get_close_matches(building, valid_halls, cutoff=0.1)
            if len(close_matches) == 0:
                return "Invalid building name. Please try again and/or ask for help.", building, room
            else:
                return "Invalid building name. Did you mean one of these? {}".format(close_matches), building, room
        while len(room) < 3:
            room = "0" + room
        if len(room) > 5:
            return "Invalid room length. Please try again and/or ask for help.", building, room
        if building == "forbes":
            if room[0] == 'A':
                building = "forbes-addition"
            else:
                building = "forbes-main"
        return None, building, room

def add_roommate(discordID, args):
    print("Adding/retrieving roommates")
    msg, building, room = process_roommate_args(args)
    if msg == None:
        print("Connecting to database")
        db = mysql.connector.connect(
            host=os.environ.get("HOST"),
            database=os.environ.get("DATABASE"),
            user=os.environ.get("USER"),
            password=os.environ.get("PASSWORD"))
        cursor = db.cursor()
        params = (discordID, building, room)
        cursor.callproc("ReplaceRoom", params)
        cursor.callproc("FindMatches", params)
        roommates = []
        for result in list(cursor.stored_results())[0]:
            roommates.append(result[0])
        print(roommates)
        if len(roommates) > 0:
            message = "Here are your roommates! "
            for roommateID in roommates:
                message += "<@" + str(roommateID) + "> "
            return message
        else:
            return "No roommates found. You will be notified if one appears!"
    else:
        return msg