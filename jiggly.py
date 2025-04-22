import discord
import logging
import logging.handlers
# import regex as re
import aiofiles
import aiohttp
import asyncio
# import json
import datetime
# import time
# import zoneinfo
# from dateutil.parser import parse
# from dateutil.tz import gettz
# from pytz import timezone

from jigglyglobals import *
from jigglylib import *

intents = discord.Intents.all()
allowed_mentions = allowed_mentions=discord.AllowedMentions(everyone=False,users=True,roles=True,replied_user=True)
client = discord.Client(intents=intents, max_messages=500000, activity=discord.CustomActivity('💜ko-fi.com/jiggly714💜', emoji=discord.PartialEmoji.from_str('💜')))

#####################################################
###              LOGGING TO EXTERNAL FILE
#####################################################
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.DEBUG)

handler = logging.handlers.RotatingFileHandler(
    filename='../logs/discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

###########################################################################################################
###                                              MAIN CLIENT
###########################################################################################################


################################################
###                 STARTUP
###############################################
@client.event
async def on_ready():
    for (input, output) in channel_ids.items():
        channel_ids_rev[output] = input
        channels[client.get_channel(input)] = client.get_channel(output)
        channels_rev[client.get_channel(output)] = client.get_channel(input)

    for id in deals_mod_role_ids:
        mod_roles.append(client.get_guild(deals_id).get_role(id))
    for id in prem_mod_role_ids:
        mod_roles.append(client.get_guild(prem_id).get_role(id))

    global deals_logging_output
    global prem_logging_output
    global panda_links_channel
    deals_logging_output = client.get_channel(deals_logging_output_id)
    prem_logging_output = client.get_channel(prem_logging_output_id)
    panda_links_channel = client.get_channel(panda_links_id)

    for (guild, channel) in archive_channel_ids.items():
        archive_channels[guild] = client.get_channel(channel)

    for id in bot_channel_ids:
        bot_channels.append(client.get_channel(id))

    emojis = [emoji for emoji in client.emojis]

    logger.info('')
    logger.info('----------------------------------------------------------------------')
    logger.info(f'Logged in as {client.user} (ID: {client.user.id})')
    logger.info('----------------------------------------------------------------------')
    logger.info('')
    logger.info('----------------------------------------------------------------------')
    logger.info('-                            CHANNEL LIST                            -')
    logger.info('----------------------------------------------------------------------')
    logger.info('')
    for (input, output) in channels.items():
        head = f'{input.guild}'
        head = f'{head}{' '*(18-len(head))} - {input}'
        head = f'{head}{' '*(56-len(head))}     -->     {output.guild}'
        logger.info(f'{head}{' '*(89-len(head))} - {output}')
    logger.info('')
    if panda_links_channel:
        logger.info(f'Forwarding links to {panda_links_channel.guild} - {panda_links_channel}')
    logger.info('')
    if deals_logging_output:
        logger.info(f'Logging deleted messages from {client.get_guild(deals_id)} in:       {deals_logging_output.guild} - {deals_logging_output}')
    if prem_logging_output:
        logger.info(f'Logging deleted messages from {prem_logging_output.guild} in: {prem_logging_output.guild} - {prem_logging_output}')
    logger.info('')
    for (guild, channel) in archive_channels.items():

        logger.info(f'Archiving media logs for {client.get_guild(guild).name} in: {' '*(18-len(client.get_guild(guild).name))}{archive_channels[guild]}')
    logger.info('')
    for channel in bot_channels:
        logger.info(f'Logging botters in: {' '*(18-len(str(channel.guild)))}{channel.guild} - {channel}')
    logger.info('')
    logger.info('----------------------------------------------------------------------\n\n')
    logger.info(default_emojis)


################################################
###             MESSAGE EVENTS
###############################################
@client.event
async def on_message(message):
    if message.author == client.user:           # ignore self just in case
        return


    #####################################################
    ###             TIMESTAMP GENERATOR
    #####################################################
    if '!time ' in message.content:
        await generate_timestamp(logger, message)

    #####################################################
    ###                 BOT CATCHER
    #####################################################
    if message.content.startswith('!botscan ') and (message.channel.id == dm_channel_id or any(role in message.author.roles for role in mod_roles)):
        if 'deals' in message.content:
            await botscan(logger, client.get_guild(deals_id), message)
        elif 'premium' in message.content:
            await botscan(logger, client.get_guild(prem_id), message)
        elif 'panda' in message.content:
            await botscan(logger, client.get_guild(panda_id), message)

    ################################################
    ###                 DM COMMANDS
    ###############################################
    if message.channel.id == dm_channel_id: #DM
        if message.content.startswith('!say '):
            await send_message(logger, client.get_channel(int(message.content.split()[1])), message)

        # elif message.content.startswith('!copy contents'):
        #     input_channel = client.get_guild(deals_id).get_thread(1345099806221144217)
        #     output_channel = client.get_channel(1351635196574957660)
        #     count = 0
        #     async for msg in input_channel.history(oldest_first=True, limit=None):
        #         if msg.type == discord.MessageType.default and (not msg.reference or msg.reference.type != discord.MessageReferenceType.forward):
        #             async with aiohttp.ClientSession() as session:
        #                 webhook = discord.Webhook.from_url(contents_webhook, session=session)
        #                 await webhook.send(content=msg.content, embeds=msg.embeds, files=[await attachment.to_file() for attachment in msg.attachments], username=msg.author.display_name, avatar_url=msg.author.display_avatar.url, allowed_mentions=discord.AllowedMentions(everyone=False,users=False,roles=False), silent=True)
        #             count += 1
        #             await asyncio.sleep(.5)
        #     logger.info('--------------------------------------------------------')
        #     logger.info(f'{count} messages found in {input_channel}')
        #     logger.info(f'Fowarded {count} messages to {output_channel}')
        #     logger.info('--------------------------------------------------------\n\n')

        elif message.content.startswith('!copy success'):
            input_channel = client.get_channel(success_prem_id)
            output_channel = client.get_channel(success_deals_id)
            count = 0
            async for msg in input_channel.history(oldest_first=True, limit=None):
                if msg.type == discord.MessageType.default and (not msg.reference or msg.reference.type != discord.MessageReferenceType.forward):
                    async with aiohttp.ClientSession() as session:
                        webhook = discord.Webhook.from_url(success_webhook, session=session)
                        await webhook.send(content=msg.content, embeds=msg.embeds, files=[await attachment.to_file() for attachment in msg.attachments], username=msg.author.display_name, avatar_url=msg.author.display_avatar.url, allowed_mentions=discord.AllowedMentions(everyone=False,users=False,roles=False))
                    count += 1
                    await asyncio.sleep(.5)
            logger.info('--------------------------------------------------------')
            logger.info(f'{count} messages found in {input_channel}')
            logger.info(f'Fowarded {count} messages to {output_channel}')
            logger.info('--------------------------------------------------------\n\n')

        elif message.content.startswith('!guilds'):
            logger.info('--------------------------------------------------------')
            logger.info('Printing all guilds:')
            for guild in client.guilds:
                logger.info('')
                logger.info(f'Guild name: {guild}')
                logger.info(f'   - member count: {guild.member_count}')
                logger.info(f'   - id: {guild.id}')
            logger.info('--------------------------------------------------------\n\n')

        elif message.content.startswith('!channels '):
            guild = client.get_guild(int(message.content[10:]))
            logger.info('--------------------------------------------------------')
            logger.info(f'Printing all channels for guild {guild}:')
            for channel in guild.channels:
                logger.info('')
                logger.info(f'Channel name: {channel}')
                logger.info(f'   - type: {channel.type}')
                logger.info(f'   - id: {channel.id}')
            logger.info('--------------------------------------------------------\n\n')

        elif message.content.startswith('!messages '):
            words = message.content.split()
            channel = client.get_channel(int(words[1]))
            try:
                num_msgs = words[2]
            except IndexError:
                num_msgs = 50
            logger.info('--------------------------------------------------------')
            logger.info(f'Printing last {num_msgs} messages for {channel.name}:')
            logger.info('')
            msgs = [msg async for msg in channel.history(oldest_first=False, limit=num_msgs)]
            for msg in reversed(msgs):
                logger.info(f'{msg.created_at.astimezone().replace(microsecond=0,tzinfo=None)} - {msg.author.name}: {msg.content}')
            logger.info('--------------------------------------------------------\n\n')


    #################################
    ###     SERVER MESSAGES
    ################################
    if message.channel.id in channel_ids:

        #####################################################
        ###             CONTENTS CHANNEL FORWARDING
        #####################################################
        if message.channel.id in [contents_deals_id, contents_prem_id] and discord.MessageType.default and not message.thread:
            if message.author.id in [taiyaki_id, sora_id]: #taiyaki, sora
                output_channel = channels[message.channel]
                content = ''
                if message.attachments and not message.content.startswith('## '):
                    content='## ' + message.content
                    await message.channel.send(content=content, embeds=message.embeds, files=[await attachment.to_file() for attachment in message.attachments])#, allowed_mentions=discord.AllowedMentions(everyone=False,users=False,roles=False), silent=True)
                    await message.delete()
                await output_channel.send(content=content, embeds=message.embeds, files=[await attachment.to_file() for attachment in message.attachments])#, allowed_mentions=discord.AllowedMentions(everyone=False,users=False,roles=False), silent=True)
                logger.info('----------------------------------------------------------------------')
                logger.info(f'Received msg from {message.author.display_name} in {message.channel}')
                logger.info(f'Forwarding msg to {output_channel}')
                logger.info('----------------------------------------------------------------------\n\n')

        #####################################################
        ###             SUCCESS CHANNEL FORWARDING
        #####################################################
        if message.channel.id in [success_prem_id] and discord.MessageType.default and not message.thread and message.attachments and (not message.reference or message.reference.type != discord.MessageReferenceType.forward):
            output_channel = channels[message.channel]
            logger.info('----------------------------------------------------------------------')
            logger.info(f'Received msg from {message.author.display_name} in {message.channel}')
            logger.info('----------------------------------------------------------------------')
            message_ids[(message.channel.id, message.id)] = []
            await asyncio.sleep(120)        # wait 2 minutes before posting

            try:
                _ = await message.channel.fetch_message(message.id)
            except Exception as e:
                logger.info('----------------------------------------------------------------------')
                logger.info(f'Success from {message.author.display_name} deleted, aborting forwarded message')
                logger.info('----------------------------------------------------------------------\n\n')
                return

            if (message.channel.id, message.id) in message_ids:     #if message hasn't been deleted
                async with aiohttp.ClientSession() as session:
                    webhook = discord.Webhook.from_url(success_webhook, session=session)
                    new_msg = await webhook.send(content=message.content, embeds=message.embeds, files=[await attachment.to_file() for attachment in message.attachments], username=message.author.display_name, avatar_url=message.author.display_avatar.url, allowed_mentions=discord.AllowedMentions(everyone=False,users=False,roles=False), wait=True)
                message_ids[(message.channel.id, message.id)] = [(output_channel.id, new_msg.id)]
                message_ids_rev[message_ids[(message.channel.id, message.id)][-1]] = (message.channel.id, message.id)
                logger.info('----------------------------------------------------------------------')
                logger.info(f'Forwarding msg from {message.author.display_name} to {output_channel}')
                logger.info('----------------------------------------------------------------------\n\n')


        ##############################################
        ###             LINKS ONLY FORWARDING
        ###############################################
        # elif message.channel.id in [links_deals_id, jigglytest_1] and discord.MessageType.default and not message.thread:
        #     if 'https://' in message.content or message.role_mentions:
        #         if any(domain in message.content for domain in whitelisted_domains) or any(role in message.author.roles for role in mod_roles):
        #             await forward_link(logger, channels[message.channel], message)

        #premium links only
        elif message.channel.id in [links_prem_id]:
             if 'https://' in message.content or message.role_mentions:
                 if any(domain in message.content for domain in whitelisted_domains) or any(role in message.author.roles for role in mod_roles):
                     await forward_link_embed(client, logger, channels[message.channel], message, '')

        #links only + test channel
        elif message.channel.id in [links_deals_id]:
            if 'https://' in message.content or message.role_mentions:
                if any(domain in message.content for domain in whitelisted_domains) or any(role in message.author.roles for role in mod_roles):
                    msg_to_forward = await remove_tracking(logger, message.channel, message)
                    await forward_link_embed(client, logger, channels[message.channel], msg_to_forward, '')
                    # hardcoded panda link forwarding
                    # (easiest implementation without changing everything else)
                    # logger.info('----------------------------------------------------------------------')
                    # logger.info(f'panda_channel = {panda_links_channel}')
                    # logger.info('----------------------------------------------------------------------\n\n')
                    await forward_link_embed(client, logger, panda_links_channel, msg_to_forward, '')


##############################################
###             MESSAGE EDITED
###############################################
@client.event
async def on_message_edit(before, after):
    message = after
    # if message.author == client.user:           # ignore self just in case
    #     return
    #

    if message.channel.id in [links_deals_id, links_prem_id, test_channel_id]:
        for i in range(15):  # attempt for 3 seconds
            if (message.channel.id, message.id) in message_ids:
                for msg in message_ids[(message.channel.id,message.id)]:
                    output_channel = client.get_channel(msg[0])
                    msg_to_edit = await output_channel.fetch_message(msg[1])
                    await update_link_embed(client, logger, channels[message.channel], message, msg_to_edit)
                    logger.info('----------------------------------------------------------------------')
                    logger.info(f'Incoming msg edited, editing outgoing msg: {output_channel.id, msg_to_edit.id}')
                    logger.info('----------------------------------------------------------------------\n\n')
                break
            await asyncio.sleep(.2)




##############################################
###             MESSAGE DELETED
###############################################
@client.event
async def on_message_delete(message):
    # if message.author == client.user:           # ignore self just in case
    #     return

    ##############################################
    ###             BAD LINK / FAKE PINGS
    ###############################################
    if message.channel.id in channel_ids and message.channel.id not in [success_prem_id] and (message.channel.id,message.id) in message_ids:
        for msg in message_ids[(message.channel.id,message.id)]:
            output_channel = client.get_channel(msg[0])
            msg_to_edit = await output_channel.fetch_message(msg[1])
            logger.info('----------------------------------------------------------------------')
            await msg_to_edit.edit(content='### Link removed, sorry for fake ping', embed=None)
            logger.info(f'Incoming link post deleted, editing outgoing msg: {output_channel.id, msg_to_edit.id}')
            logger.info('----------------------------------------------------------------------\n\n')

    ##############################################
    ###             DELETED SUCCESS POST
    ###############################################
    if message.channel.id in [success_prem_id] and (message.channel.id,message.id) in message_ids:
        output_channel = channels[message.channel]
        try:
            msg_to_delete = await output_channel.fetch_message(message_ids[(message.channel.id,message.id)][-1][1])
            # del message_ids_rev[message_ids[(message.channel.id, message.id)]]
            del message_ids[(message.channel.id, message.id)]
            await msg_to_delete.delete()
            logger.info('----------------------------------------------------------------------')
            logger.info(f'Success from {message.author.display_name} deleted, deleting outgoing msg')
            logger.info('----------------------------------------------------------------------\n\n')
        except Exception as e:
            logger.info('----------------------------------------------------------------------')
            logger.info(e)
            logger.info(f'Success from {message.author.display_name} deleted, aborting forwarded message')
            logger.info('----------------------------------------------------------------------\n\n')

    #####################################################
    ###                 DELETE LOGS
    ####################################################
    elif message.author != client.user:           # ignore self just in case
        if message.channel.category_id in deals_logging_category_ids or message.channel.id in deals_logging_channel_ids:
            await log_message(client, logger, deals_logging_output, message, 'default')
        elif message.channel.category_id in prem_logging_category_ids or message.channel.id in prem_logging_channel_ids:
            await log_message(client, logger, prem_logging_output, message, 'default')

#####################################################
###                BULK DELETE LOGS
####################################################
@client.event
async def on_bulk_message_delete(messages):
    for message in messages:
        if message.channel.category_id in deals_logging_category_ids or message.channel.id in deals_logging_channel_ids:
            await log_message(client, logger, deals_logging_output, message, 'bulk')
        elif message.channel.category_id in prem_logging_category_ids or message.channel.id in prem_logging_channel_ids:
            await log_message(client, logger, prem_logging_output, message, 'bulk')

@client.event
async def on_raw_bulk_message_delete(payload):
    if client.get_channel(payload.channel_id).category_id in deals_logging_category_ids or payload.channel_id in deals_logging_channel_ids:
        await log_message(client, logger, deals_logging_output, payload, 'bulk_info')
    elif client.get_channel(payload.channel_id).category_id in prem_logging_category_ids or payload.channel_id in prem_logging_channel_ids:
        await log_message(client, logger, prem_logging_output, payload, 'bulk_info')


##############################################
###             REACTIONS
###############################################
@client.event
async def on_reaction_add(reaction, user):
    output_channel = None
    msg_to_react = None
    if user == client.user:           # ignore self just in case
        return

    ##############################################
    ###             REACTION MIRRORING
    ###############################################
    if reaction.emoji in emojis or reaction.emoji in default_emojis:
        if reaction.message.channel.id in channel_ids or reaction.message.channel.id in channel_ids_rev:
            if reaction.message.channel.id not in reactions:
                reactions[reaction.message.channel.id] = {}
            if reaction.message.id not in reactions[reaction.message.channel.id]:
                reactions[reaction.message.channel.id][reaction.message.id] = []
            if reaction.emoji not in reactions[reaction.message.channel.id][reaction.message.id]:
                reactions[reaction.message.channel.id][reaction.message.id].append(reaction.emoji)
                if reaction.message.channel in channels:
                    for msg in message_ids[(reaction.message.channel.id, reaction.message.id)]:
                        try:
                            output_channel = client.get_channel(msg[0])
                            msg_to_react = await output_channel.fetch_message(msg[1])
                            logger.info('----------------------------------------------------------------------')
                            logger.info(f'Adding react: {reaction.emoji} from user {user.id} to forwarded msg: {msg_to_react.id}')
                            logger.info('----------------------------------------------------------------------\n\n')
                        except (NameError, KeyError):
                            pass
                elif reaction.message.channel in channels_rev:
                    try:
                        output_channel = client.get_channel(message_ids_rev[(reaction.message.channel.id, reaction.message.id)][0])
                        msg_to_react = await output_channel.fetch_message(message_ids_rev[(reaction.message.channel.id, reaction.message.id)][1])
                        logger.info('----------------------------------------------------------------------')
                        logger.info(f'Adding react: {reaction.emoji} from user {user.id} to original msg: {msg_to_react.id}')
                        logger.info('----------------------------------------------------------------------\n\n')
                    except (NameError, KeyError):
                        pass
                try:
                    await msg_to_react.add_reaction(reaction.emoji)
                except (NameError, AttributeError):
                    pass

    ##############################################
    ###             REACTION LOGGING
    ###############################################
    async with aiofiles.open('../react_logs/log.json', 'a', encoding="utf-8") as f:
        output_str = ''
        if isinstance(reaction.emoji, str):
            output_str = '{"react": "' + reaction.emoji + '", "name": "' + str(user.display_name) + '", "username": "' + user.name + '", "time": "' + str(datetime.datetime.now().replace(microsecond=0)) + '", "user_id": '+ str(user.id) + ', "guild": ' + str(reaction.message.channel.guild) + ', "channel": ' + str(reaction.message.channel) + ', "message_id": ' + str(reaction.message.id) + '}\n'
        else:
            output_str = '{"react": "' + reaction.emoji.name + '", "name": "' + str(user.display_name) + '", "username": "' + user.name +  '", "time": "' + str(datetime.datetime.now().replace(microsecond=0)) + '", "user_id": '+ str(user.id) + ', "guild": ' + str(reaction.message.channel.guild) + ', "channel": ' + str(reaction.message.channel) + ', "message_id": ' + str(reaction.message.id) + '}\n'
        await f.write(output_str)



##############################################
###             PRESENCE UPDATES
###############################################
@client.event
async def on_presence_update(before, after):
    member = after
    if member.activities and (any((bot_name in activity.name.lower() and all(app_name not in activity.name.lower() for app_name in whitelisted_apps)) for activity in list(member.activities) for bot_name in bot_names)
    or any((hasattr(activity, 'application_id') and bot_id == activity.application_id) for activity in list(member.activities) for bot_id in bot_ids)):
        await botter_alert(logger, member)

###########################################################
#####           NON FUNCTIONAL (REACTION DELETION LOGS)
###############################################################
# @client.event
# async def on_reaction_remove(reaction, user):
#     if user == client.user:           # ignore self just in case
#         return
#
#     async with aiofiles.open('../react_logs/log.json', 'a', encoding="utf-8") as f:
#         output_str = ''
#         if isinstance(reaction.emoji, str):
#             output_str = '{"react": "' + reaction.emoji + ' - DEL", "nickname": "' + str(user.nick) + '", "username": "' + user.name + '", "time": "' + str(datetime.datetime.now().replace(microsecond=0)) + '", "user_id": '+ str(user.id) + ', "guild": ' + str(message.channel.guild) + ', "channel": ' + str(reaction.message.channel) + ', "message_id": ' + str(reaction.message.id) + '}\n'
#         else:
#             output_str = '{"react": "' + reaction.emoji.name + ' - DEL", "nickname": "' + str(user.nick) + '", "username": "' + user.name +  '", "time": "' + str(datetime.datetime.now().replace(microsecond=0)) + '", "user_id": '+ str(user.id) + ', "guild": ' + str(message.channel.guild) + ', "channel": ' + str(reaction.message.channel) + ', "message_id": ' + str(reaction.message.id) + '}\n'
#         await f.write(output_str)



###########################################################
#####                     RUN PROGRAM
###########################################################
# Suppress the default configuration since we have our own
try:
    client.run(bot_token, log_handler=None)
except discord.errors.HTTPException as e:
    print(e)



