import asyncio
from config import *
from datetime import datetime
import discord
from discord.ext import commands, tasks
from email_verification import is_valid_email, generate_code, send_email
import pandas as pd
from resco import is_resco_available, get_college, add_roommate
import os
from pytz import timezone
from utils import save_member_list, get_countdown, clear_channel
from menu import get_menus

print("Initializing client")
bot_intents = discord.Intents.default()
bot_intents.value = intents["VALUE"]
client = commands.Bot(command_prefix=messages["COMMAND_PREFIX"], intents=bot_intents)

@client.event
async def on_ready():
    print("Logged in as {}".format(client.user))
    print("Initializing channels")
    for channel_name in channels.keys():
        channel_id = channels[channel_name]
        channels[channel_name] = client.get_channel(channel_id)
    print("Starting background tasks")
    time_monitor.start()
    print("Sending start message in channel")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="$help | @Leo S"))

@client.event
async def on_member_join(member):
    await asyncio.sleep(3)
    print("Printing verification message")
    await channels["VERIFICATION"].send(messages["VERIFY_EMAIL"].format(member.id))
    await member.add_roles(discord.utils.get(member.guild.roles, name="DMV Not Started"))

verification_enabled = True
df_verify= pd.DataFrame(columns=["discordID", "code"])
@client.event
async def on_message(message):
    global verification_enabled
    global df_verify
    if message.channel == channels["VERIFICATION"] and message.author.id != client.user.id and verification_enabled:
        discordID = message.author.id
        if discordID not in df_verify["discordID"].values:
            email = message.content
            email = email.lower()
            if is_valid_email(email):
                code = generate_code(20, "abcdefghijklmnopqrstuvwxyz1234567890")
                await channels["VERIFICATION"].send(messages["EMAIL_VALIDATED"].format(discordID))
                await message.author.remove_roles(discord.utils.get(message.guild.roles, name="DMV Not Started"))
                await message.author.add_roles(discord.utils.get(message.guild.roles, name="DMV Pending"))
                send_email(email, code)
                df_verify = df_verify.append({"discordID": discordID, "code": code}, ignore_index=True)
            else:
                await channels["VERIFICATION"].send(messages["EMAIL_INVALID"].format(discordID))
        elif df_verify[df_verify["discordID"]==discordID]["code"].values[0] == message.content.lower():
            df_verify = df_verify[df_verify["discordID"] != discordID]
            await channels["VERIFICATION"].send(messages["VERIFIED"].format(discordID))
            await message.author.remove_roles(discord.utils.get(message.guild.roles, name="DMV Pending"))
            await message.author.remove_roles(discord.utils.get(message.guild.roles, name="DMV Current Member"))
            await message.author.add_roles(discord.utils.get(message.guild.roles, name="DMV Verified"))
            print("Printing welcome message")
            await channels["GENERAL"].send(messages["WELCOME2"].format(discordID, channels["ROLE_WITH_IT"], 
                channels["CONCENTRATIONS"], channels["INTRODUCTIONS"], channels["WHERE_ARE_YOU"], channels["GENIUS_BAR"]))
        else:
            df_verify = df_verify[df_verify["discordID"] != discordID]
            await channels["VERIFICATION"].send(messages["NOT_VERIFIED"].format(discordID))
        await message.delete()
    await client.process_commands(message)
                
@client.command()
async def verify(ctx, param=None):
    global verification_enabled
    if discord.utils.get(ctx.message.guild.roles, name="admin") in ctx.message.author.roles:
        if param==None:
            await ctx.message.channel.send("$verify <on/off/clear>")
        elif param.lower() == "on":
            verification_enabled = True
            await ctx.message.channel.send("Verification enabled.")
        elif param.lower() == "off":
            verification_enabled = False
            await ctx.message.channel.send("Verification disabled.")
        elif param.lower() == "clear":
            async for message in channels["VERIFICATION"].history(limit=None):
                await message.delete()
        else:
            await ctx.message.channel.send("$verify <on/off/clear>")

client.help_command = None
@client.command()
async def help(ctx):
    print("Running help command")
    await ctx.message.channel.send(messages["HELP"])

@client.command()
async def members(ctx):
    print("Saving and sending member list")
    member_list_path = "members.csv"
    save_member_list(ctx.guild.members, member_list_path)
    await ctx.message.channel.send(file=discord.File(member_list_path))

@client.command()
async def match(ctx, *args):
    print("Adding user to roommate database")
    if ctx.message.channel == channels["ROOMMATE_FINDER"]:
        discordID = ctx.message.author.id
        await ctx.message.channel.send("<@" + str(discordID) + "> " + add_roommate(discordID, args))

eastern = timezone('US/Eastern')
previous = datetime.now(eastern)
disabled = False
message_off = False
print("Current time: {}".format(previous))
@tasks.loop(minutes=intervals["TIME_MONITOR_MIN"], count=None)
async def time_monitor():
    global previous
    global disabled
    global message_off
    current = datetime.now(eastern)
    if current.hour >= 7 and previous.hour < 7:
        print("Sending menus")
        for embed in get_menus("Whitman College", 8):
            await channels["WHITMAN_MENU"].send(embed=embed)
        for embed in get_menus("Butler and First Colleges", 2):
            await channels["WUCOX_MENU"].send(embed=embed)
        for embed in get_menus("Rockefeller and Mathey Colleges", 1):
            await channels["ROMA_MENU"].send(embed=embed)
        for embed in get_menus("Forbes College", 3):
            await channels["FORBES_MENU"].send(embed=embed)
        for embed in get_menus("Graduate College", 4):
            await channels["GRAD_MENU"].send(embed=embed)

    if current.hour >= 4 and previous.hour < 4:
        await clear_channel("VERIFICATION")
        menu_channels = ["WHITMAN_MENU", "WUCOX_MENU", "ROMA_MENU", "FORBES_MENU", "GRAD_MENU"]
        for menu_channel in menu_channels:
            await clear_channel(menu_channel)
    
    if current.hour >= 22 and previous.hour < 22:
        message = "Reminder to do your COVID test (due tomorrow at 10am)!"
        if current.weekday() == 1: # sunday(due monday) and tuesday(due wednesday)
            await channels["BUTLER_TRS"].send("<@&884977380681199667> " + message)
            await channels["FORBES_TRS"].send("<@&884977291367690250> " + message)
            await channels["ROCKEFELLER_TRS"].send("<@&884977012698120243> " + message)
        elif current.weekday() == 3: # monday(due tuesday) and wednesday(due thursday)
            await channels["MATHEY_TRS"].send("<@&884977082751410176> " + message)
            await channels["FIRST_TRS"].send("<@&884977319935098900> " + message)
            await channels["WHITMAN_TRS"].send("<@&884977356803035166> " + message) 
        elif current.weekday() == 4: # friday clear
            trs_channels = ["WHITMAN_TRS", "MATHEY_TRS", "FIRST_TRS", "BUTLER_TRS", "FORBES_TRS", "ROCKEFELLER_TRS"]
            for trs_channel in trs_channels:
                await clear_channel(trs_channel)
        
    previous = current
    
# check reactions every x minutes for x hours
@tasks.loop(minutes=intervals["REACTION_CHECK_MIN"], 
    count=int(intervals["REACTION_CHECK_HRS"]*60/intervals["REACTION_CHECK_MIN"]))
async def check_reaction_count(msg_id):
    global message_off
    print("Checking vc poll reaction count")
    msg = await channels["VC_POLL"].fetch_message(msg_id)
    async for user in msg.reactions[0].users():
        await user.add_roles(discord.utils.get(msg.guild.roles, name="Wants to Chat"))
    if msg.reactions[0].count >= messages["VC_POLL_COUNT"]+1 and not message_off:
        print("Sending vc poll success message in channel")
        await channels["GENERAL"].send(messages["VC_POLL_SUCCESS"].format(messages["VC_POLL_COUNT"]))
        message_off = True

client.run(os.environ.get("TOKEN"))
