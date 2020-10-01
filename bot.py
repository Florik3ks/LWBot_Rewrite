'''
https://discord.com/api/oauth2/authorize?bot_id=760125323580276757&permissions=8&scope=bot
'''

import discord
from discord.ext import commands
from discord.ext import tasks
from discord.ext.commands.errors import CommandNotFound
from discord.ext.commands.errors import MissingRequiredArgument

import traceback
import asyncio
import datetime
import operator
import os

import lwConfig
import lwHelperFunctions
import voteListHandler
import reminderHandler

bot = commands.Bot(command_prefix=lwConfig.prefix)
bot.owner_ids = lwConfig.ownerID


@bot.event
async def on_error(event, *args, **kwargs):
    embed = discord.Embed(title=f'new Error in event {event}()')
    embed.color = discord.Color.red()
    embed.description = f"```{traceback.format_exc()}```"
    embed.set_footer(text=kwargs)
    channel = bot.get_channel(lwConfig.logChannelID)
    await channel.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound) or isinstance(error, MissingRequiredArgument):
        return
    embed = discord.Embed(title=f'new Error in command {ctx.command}()')
    embed.color = discord.Color.red()
    embed.description = f"```{error}```"
    embed.set_footer(text=type(error))
    await ctx.send(embed=embed)


@bot.event
async def on_ready():
    activity = discord.Activity(
        type=discord.ActivityType.watching, name=lwConfig.statusMessage)
    await bot.change_presence(activity=activity, status=discord.enums.Status.dnd)
    e = discord.Embed(title="Bot started")
    e.color = discord.Color.blurple()
    e.timestamp = datetime.datetime.utcnow()
    e.set_footer(text=bot.user.name, icon_url=bot.user.avatar_url)
    channel = bot.get_channel(lwConfig.logChannelID)
    await channel.send(embed=e)


@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel.id == lwConfig.memeChannelID and len(message.attachments) > 0:
        await message.add_reaction(lwHelperFunctions.getEmoji(bot, lwConfig.upvoteEmoji))
        await message.add_reaction(lwHelperFunctions.getEmoji(bot, lwConfig.downoteEmoji))
    if message.content.startswith("awoo"):
        await test(ctx=message, arg=message.content)


@bot.command()
async def ev(ctx, *, arg):
    if await bot.is_owner(ctx.author):
        try:
            await eval(arg, {
                "ctx": ctx,
                "bot": bot,
                "lwHelperFunctions": lwHelperFunctions,
                "discord": discord,
                "datetime": datetime,
                "reminderHandler": reminderHandler,
                "os": os
            })
        except Exception as e:
            if isinstance(e, TypeError):
                pass
            else:
                raise e
    else:
        awoo = lwHelperFunctions.getEmoji(bot, "AwOo")
        e = discord.Embed(title="You are not worthy ")
        e.set_image(url=awoo.url)
        e.color = discord.Color.blurple()
        e.timestamp = datetime.datetime.utcnow()
        e.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=e)


@bot.command()
async def embed(ctx, *args):
    await ctx.send(embed=lwHelperFunctions.simpleEmbed(ctx.author, *args))


@bot.command()
async def test(ctx, *, arg):
    e = discord.Embed(title="testing stuffu")
    e.color = discord.Color.blurple()
    e.description = arg
    e.timestamp = datetime.datetime.utcnow()
    e.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar_url)
    await ctx.send(embed=e)


@bot.command()
async def emotes(ctx):
    e = discord.Embed(title="Emotes:")
    emotes = [f"<:{e.name}:{e.id}>" for e in bot.emojis]
    e.description = ''.join(emotes)
    e.timestamp = datetime.datetime.utcnow()
    e.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar_url)
    m = await ctx.send(embed=e)
    # for i in range(min(20, len(emotes))):
    #    await m.add_reaction(emotes[i])


@bot.command()
async def entries(ctx):
    voteListHandler.deleteOldMessages()
    voteList = voteListHandler.getVoteList()
    e = discord.Embed()
    e.color = discord.Color.purple()
    e.timestamp = datetime.datetime.utcnow()
    e.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar_url)
    e.set_author(name=bot.user, icon_url=bot.user.avatar_url)
    if not len(voteList) > 0:
        e.title = "No entries in the votelist."
        await ctx.send(embed=e)
        return
    e.title = "Entries"
    e.description = "All current entry messages in the votelist.\n\n```[ MessageID:\n Upvotes \u2606, created_at ]```"
    for k in list(voteList.keys()):
        e.add_field(
            name=f"{str(k)}:", value=f"```{str(voteList[k][0])} \u2606, {str(voteList[k][1])}```", inline=False)

    await ctx.send(embed=e)


@bot.command()
async def stats(ctx):
    async with ctx.message.channel.typing():
        voteListHandler.deleteOldMessages()
    voteList = voteListHandler.getVoteList()
    if(len(voteList) > 0):
        vList = {}
        for i in voteList.keys():
            vList[i] = voteList[i][0]
        sortedDict = sorted(
            vList.items(), key=operator.itemgetter(1), reverse=True)
        winnerMessage = await bot.get_channel(lwConfig.memeChannelID).fetch_message(sortedDict[0][0])
        score = voteList[sortedDict[0][0]][0]
        e = discord.Embed()
        e.title = f"Current top voted post with a score of {str(score)} {lwHelperFunctions.getEmoji(bot, lwConfig.upvoteEmoji)}"

        e.description = winnerMessage.content
        e.set_image(url=winnerMessage.attachments[0].url)
        e.set_author(name=winnerMessage.author,
                     icon_url=winnerMessage.author.avatar_url)
        e.color = winnerMessage.guild.get_member(
            winnerMessage.author.id).colour
        date = winnerMessage.created_at
        e.description += f"\n`Message created at:  {str(date).split('.')[0]}`"
        e.timestamp = datetime.datetime.utcnow()
        e.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.channel.send(embed=e)
        if(not lwHelperFunctions.is_url_image(e.image.url)):
            await ctx.message.channel.send(winnerMessage.attachments[0].url)
    else:
        await ctx.message.channel.send("no items in the voting list.")


@bot.command()
async def reminder(ctx, *, arg):
    try:
        time = datetime.datetime.strptime(arg, '%d.%m.%Y %H:%M')
        if time < datetime.datetime.now():
            await ctx.send(embed=lwHelperFunctions.simpleEmbed(ctx.author, "Reminder in the past?", "not allowed."))
            return
        await ctx.send(embed=lwHelperFunctions.simpleEmbed(ctx.author, "Please enter a message for the reminder", "Dont answer for 60 seconds to time out."))
        m = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
    except Exception as e:
        if isinstance(e, TimeoutError):
            await ctx.send(embed=lwHelperFunctions.simpleEmbed(ctx.author, "Timed out.", "Try again if you want to set a reminder."))
        elif isinstance(e, ValueError):
            await ctx.send(embed=lwHelperFunctions.simpleEmbed(ctx.author, "Wrong date format.", "your Date should be in the format\nreminder DAY.MONTH.YEAR HOURS:MINUTES\nExample: reminder 1.10.2020 6:34."))
        return

    reminderHandler.addReminder(ctx.author, time, m.content)


@bot.command()
async def myreminders(ctx):
    r = reminderHandler.getReminder()
    if ctx.author in list(r.keys()):
        await ctx.send(reminder[ctx.author])
    else:
        await ctx.send(embed=lwHelperFunctions.simpleEmbed(ctx.author, "You have no reminders.", f"Type {bot.command_prefix}reminder to create one."))


@bot.listen()
async def on_raw_reaction_add(payload):
    if payload.channel_id != lwConfig.memeChannelID:
        return
    user = bot.get_user(payload.user_id)
    msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    reaction = None
    for reac in msg.reactions:
        if reac.emoji == payload.emoji.name or reac.emoji == payload.emoji:
            reaction = reac
    if reaction == None:
        return
    if payload.emoji.name == lwConfig.deleteEmojiName and msg.author == bot.user and user in msg.mentions:
        if bot.user in await reaction.users().flatten():
            await msg.delete()
        else:
            await reaction.remove(user)
        return
    upvote = lwHelperFunctions.getEmoji(bot, lwConfig.upvoteEmoji)
    downvote = lwHelperFunctions.getEmoji(bot, lwConfig.downoteEmoji)
    if user != bot.user:
        if reaction.message.author == user and (reaction.emoji == upvote or reaction.emoji == downvote):
            await reaction.remove(user)
            errormsg = await reaction.message.channel.send(f"{user.mention} you cannot up/downvote your own post.")
            for i in bot.emojis:
                if i.name == lwConfig.deleteEmojiName:
                    await errormsg.add_reaction(i)
            return
        if reaction.emoji == upvote:
            voteListHandler.changeVotingCounter(reaction.message, 1)
            if reaction.count - 1 >= lwConfig.upvotesForPin and not reaction.message.pinned:
                await reaction.message.pin(reason="good meme")
        elif reaction.emoji == downvote:
            voteListHandler.changeVotingCounter(reaction.message, -1)


@bot.listen()
async def on_raw_reaction_remove(payload):
    if payload.channel_id != lwConfig.memeChannelID:
        return
    user = bot.get_user(payload.user_id)
    msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    reaction = None
    for reac in msg.reactions:
        if reac.emoji == payload.emoji.name or reac.emoji == payload.emoji:
            reaction = reac
    if reaction == None:
        return
    if user != bot.user and user != reaction.message.author:
        if reaction.emoji == lwHelperFunctions.getEmoji(bot, lwConfig.upvoteEmoji):
            voteListHandler.changeVotingCounter(reaction.message, -1)
        elif reaction.emoji == lwHelperFunctions.getEmoji(bot, lwConfig.downoteEmoji):
            voteListHandler.changeVotingCounter(reaction.message, 1)


@tasks.loop(seconds=30)
async def checkReminder():
    return


@tasks.loop(seconds=300)
async def checkGmoWebsite():
    news = await lwHelperFunctions.getGmoNews()
    if news != None:
        channel = bot.get_channel(lwConfig.newsChannelID)
        await channel.send(channel.guild.get_role(lwConfig.gmoRoleID).mention + " " + news)


@checkGmoWebsite.before_loop
async def beforeGmoNews():
    await bot.wait_until_ready()
    print("gmoLoopStart")
    channel = bot.get_channel(lwConfig.logChannelID)
    await channel.send(embed=lwHelperFunctions.simpleEmbed(bot.user, "gmoNewsCheck loop start", arg))


@checkGmoWebsite.after_loop
async def afterGmoNews():
    print("gmoLoop crashed")
    channel = bot.get_channel(lwConfig.logChannelID)
    await channel.send(embed=lwHelperFunctions.simpleEmbed(bot.user, "gmoNewsCheck loop stopped. restarting now", arg))
    checkGmoWebsite.restart()

checkGmoWebsite.start()
checkReminder.start()
bot.run(lwConfig.token)
