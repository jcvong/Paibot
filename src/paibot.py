import discord
import pytz
from discord.ext import tasks, commands
from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Union, Optional

zone = "America/Anchorage"
bot = commands.Bot(command_prefix=commands.when_mentioned_or("/"))
config = {}

with open("config.txt", "r") as setup:
    for var in ["token", "mongoURL"]:
        config[var] = setup.readline().split(" ")[2].strip()

cluster = MongoClient(config["mongoURL"])
db = cluster["genshin"]

db["resin-notifs"].delete_many({})
print("[PAIBOT] Cleared resin-notif collection")

@bot.event    
async def on_ready():
    print("[PAIBOT] Connected to Discord")
    checkResin.start()

@bot.command(
    name="mats",
    help="Prints the materials available today")
async def dailyMats(ctx):
    async with ctx.typing():
        day = datetime.now(pytz.timezone(zone))
        resetTimer = resetString()
        talentMats = ""
        weaponMats = ""
    
        embed = discord.Embed()
        view = db["daily-materials"]
    
        embed.set_footer(text="\N{ALARM CLOCK}" + f" {resetTimer} until reset.")
       
        for item in view.find({"day": {"$regex": f".*{day.strftime('%A').lower()}.*"}}):
            if item["type"] == "talent":
                talentMats += u"\u2022 " + item["name"] + " - "
                talentMats += f"*{', '.join(c[:1].upper() + c[1:] for c in item['characters'].split(','))}*\n"
            else:
                weaponMats += u"\u2022 " + item["name"] + " (" + item["location"] + ")\n"
        
        talentMats += u"\u200b\n"
        weaponMats += u"\u200b\n"
        embed.add_field(name="Talent Materials", value=talentMats)
        embed.add_field(name="Weapon Materials", value=weaponMats, inline=False)
        
    await ctx.send(embed=embed)

@bot.command(
    name="resin",
    help="Sends you a direct message when your resin is fully recharged")
async def resinTimer(ctx, resin: Union[int, str] = None):  
    view = db["resin-notifs"]
    resetTimer = resetString()
    user = bot.get_user(ctx.author.id)
    
    if ctx.channel.type == discord.ChannelType.private:
        await ctx.trigger_typing()
    else:
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
   
    embed = discord.Embed()
    embed.set_author(name=f"Resin Reminder{'' if (resin == 'cancel' or resin == 'check') else ': ' + str(resin) + '/160'}", url=discord.Embed.Empty, 
                     icon_url="https://cdn.discordapp.com/attachments/775287257350799380/775287646813028412/136.png")
    
    if type(resin) is str:
        if resin.lower() == "cancel" and view.count_documents({"uid": ctx.author.id}) == 1:
            view.delete_one({"uid": ctx.author.id})

            embed.description = "Paibot will no longer notify you when your resin is full."
            embed.set_footer(text=u"\u200b\n" + "\N{ALARM CLOCK}" + f" {resetTimer} until reset.")
            
            await user.send(embed=embed)
            
            print(f"[{ctx.author.id}|RESIN] Resin notification cancelled")
        elif resin.lower() == "check" and view.count_documents({"uid": ctx.author.id}) == 1:
            entry = view.find_one({"uid": ctx.author.id})
            resinDelta = datetime.now(pytz.timezone(zone)).astimezone(pytz.utc) - entry["startTime"].replace(tzinfo=pytz.utc)
            timeDelta = entry["untilFull"].replace(tzinfo=pytz.utc) - datetime.now(pytz.timezone(zone)).astimezone(pytz.utc)
            
            hours = int(timeDelta.total_seconds()) // 3600
            minutes = (int(timeDelta.total_seconds()) % 3600) // 60
            
            embed.description = f"You currently have **{entry['startResin'] + int(resinDelta.total_seconds() // (60 * 1))}/160** resin.\nYour resin will be full in **{hours} hour(s) and {minutes} minutes**."
            embed.set_footer(text=u"\u200b\n" + 
                         "\N{NO ENTRY SIGN}" + f' To cancel, use "/resin cancel" command.\n' + 
                         "\N{PUSHPIN}" + f' To update, use "/resin [0-119]" command.\n' +
                         u"\u200b\n" +
                         "\N{ALARM CLOCK}" + f" {resetTimer} until reset.")
            
            await user.send(embed=embed)
        elif view.count_documents({"uid": ctx.author.id}) != 1:
            await ctx.send("No old notification exists. Use `/resin [0-119]` command to set up a notification.")
        else:
            await ctx.send("Incorrect format. Use `/resin cancel` to cancel notifications.")
    elif (type(resin) is int and (resin < 0 or resin >= 160)) or resin is None:
        await ctx.send("Incorrect format. Use `/resin [0-159]` command.")   
    else:
        hours = ((160 - resin) * 1) // 60
        minutes = ((160 - resin) * 1) % 60
        recharge = datetime.now(pytz.timezone(zone)) + timedelta(minutes = (160 - resin) * 1) #change to actual resin rate (8)
        
        embed.description = f"Paibot will remind you when your resin is full.\nSee you in **{hours} hour(s) and {minutes} minute(s)**, traveler!"
        embed.set_footer(text=u"\u200b\n" + 
                         "\N{NO ENTRY SIGN}" + f' To cancel, use "/resin cancel" command.\n' + 
                         "\N{PUSHPIN}" + f' To update, use "/resin [0-119]" command.\n' +
                         u"\u200b\n" +
                         "\N{ALARM CLOCK}" + f" {resetTimer} until reset.")
        
        await user.send(embed=embed)

        if view.count_documents({"uid": ctx.author.id}) == 1:
            print(f"[{ctx.author.id}|RESIN] Old notification found, updating..")
            view.update_one({"uid": ctx.author.id}, {"$set": {"untilFull": recharge}})
        else:    
            view.insert_one({
                "uid": ctx.author.id,
                "startResin": resin,
                "startTime": datetime.now(pytz.timezone(zone)), 
                "untilFull": recharge
            })
        
        print(f"[{ctx.author.id}|RESIN] Notification set ({resin}/160)")

@tasks.loop(seconds=20.0)
async def checkResin():
    view = db["resin-notifs"]
    resetTimer = resetString()
    query = datetime.now(pytz.timezone(zone)).astimezone(pytz.utc)

    for result in view.find({"untilFull": {"$lte": query}}):
        user = bot.get_user(result["uid"])
        view.delete_one({"uid" : result["uid"]})
        
        embed = discord.Embed()
        embed.set_author(name="Resin Reminder: 160/160", url=discord.Embed.Empty, icon_url="https://cdn.discordapp.com/attachments/775287257350799380/775287646813028412/136.png")
        embed.description = "Your resin is full, traveler."
        embed.set_footer(text="\N{ALARM CLOCK}" + f" {resetTimer} until reset.")
        
        await user.send(embed=embed)
        
        print(f"[{user.id}|RESIN] Resin reached max, purging from collection")

def resetString(day: Optional[datetime] = None):
    if day is None:
        day = datetime.now(pytz.timezone(zone))
    
    resetHour = '' if 23 - day.hour == 0 else str(23 - day.hour) + " hour(s)"
    resetMin = '' if 59 - day.minute == 0 else str(59 - day.minute) + " minute(s)"
    
    return f"{resetHour}{'' if (resetHour == '' or resetMin == '') else ' and '}{resetMin}"

bot.run(config["token"])