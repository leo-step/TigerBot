import discord
from bs4 import BeautifulSoup
import requests
from datetime import date

def get_menus(title, locationNum):
    url = "https://menus.princeton.edu/dining/_Foodpro/online-menu/menuDetails.asp?locationNum={:02d}".format(locationNum)
    text = requests.get(url).text
    soup = BeautifulSoup(text, features="lxml")
    menus = soup.findAll("div", {"class" : "card mealCard"})
    menu_times = ["Breakfast", "Lunch", "Dinner"]
    embeds = []
    for i, menu in enumerate(menus):
        text = menu.text.replace("Nutrition", '').replace('\r', '')
        items = [item.strip() for item in text.split("\n") if item.strip()]
        header = title + " - " + items[0]
        embed = discord.Embed(title=header, url=url, description=date.today().strftime("%m/%d/%Y"))
        items = items[1:]
        if len(items) != 0:
            indices = [i for i, s in enumerate(items) if '--' in s]
            indices.append(len(items))
            for i in range(len(indices)-1):
                embed.add_field(name=items[indices[i]], value='\n'.join(items[indices[i]+1:indices[i+1]]) + "\n", inline=False)
            embed.set_image(url="https://menus.princeton.edu/dining/_Foodpro/online-menu/img/food.jpg")
            embeds.append(embed)
    return embeds

if __name__ == "__main__":
    print(get_menus("Whitman College", 8))
    