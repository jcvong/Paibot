# Paibot (Genshin Impact)
A small side project for Genshin Impact, primarily focused at push notifications for PC players utilizing Discord and MongoDB to accurately notify users when their resin (stamina currency) ingame is refilled. This project is (currently) meant to be hosted on Heroku and utilizes MongoDB to store user information.

Core functionalities are implemented; later functionalities might include a roll simulator (figuring out the pity system mechanic), and a database (either by scraping available databases or rebuilding one within MongoDB)

Small QoL (quality of life) addition(s) include a countdown until the game day changes.

# Commands
All commands can be sent in any text channel or DM'd to the bot. Currently, a command sent in a text channel will lead to the bot DMing you, as the commands are meant for personal use; imagine it as asking the bot, "Hey, how much resin do I currently have?" which technically doesn't need to be seen by everyone in the server.

### `/resin [0-159]`
Informs the bot that you currently have 0-159 resin left. The bot will then notify you once your resin recharges back to 160. __This command can also override your current resin stored within the bot;__ for example:

1. You use `/resin 80` to tell the bot you have 80 resin. 
1. You decide to spend 20 resin in a domain.
1. You can use `/resin 60` to tell the bot you now have 60 resin.
1. __The bot will now let you know when your resin recharges from 60, rather than 80.__

### `/resin cancel`
Deletes your current resin information from the bot, and the bot __will not__ notify you when your resin is fully recharged.

### `/mats`
Informs you of the current materials available in Genshin Impact domains for both weapon ascension and character ascension.
