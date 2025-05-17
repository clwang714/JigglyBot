import discord
import logging
import logging.handlers
import regex as re
import aiofiles
import json
import datetime
import time
from dateutil.parser import parse
from dateutil.tz import gettz
from pytz import timezone
from urllib.parse import urljoin, urlparse

from jigglyglobals import *



###########################################################
#####             FUNCTION IMPLEMENTATIONS
###########################################################

async def send_message(logger, output_channel, message):
    output_msg = await output_channel.send(message.content[len(str(output_channel.id))+6:])
    await message.channel.send('Sending msg to channel: ' + output_msg.jump_url)
    logger.info('----------------------------------------------------------------------')
    logger.info(f'Sending msg to channel: {output_channel}')
    logger.info('')
    logger.info(message.content[len(str(output_channel.id))+6:])
    logger.info('----------------------------------------------------------------------\n\n')


async def generate_timestamp(logger, message):
    index = message.content.find('!time ')
    header = '# ' + message.content[:index]
    if header.strip() == '#':
        header = ''

    tail = message.content[index+6:]
    tail = re.sub('(?<=[0-9]+) min', 'min', tail, flags=re.IGNORECASE)
    tail = re.sub('(?<=[0-9]+) sec', 'sec', tail, flags=re.IGNORECASE)
    tail = re.sub('(?<=[0-9]+) p ', 'p ', tail, flags=re.IGNORECASE)
    tail = re.sub('(?<=[0-9]+) a ', 'a ', tail, flags=re.IGNORECASE)
    tail = re.sub('Tues', ' Tuesday ', tail, flags=re.IGNORECASE)
    tail = re.sub('Thurs', ' Thursday ', tail, flags=re.IGNORECASE)
    tail = re.sub('Hawaii|hast| (?<=[0-9]*)ht', ' HAST ', tail, flags=re.IGNORECASE)
    tail = re.sub('Alaskan|akst|adt', ' AKST ', tail, flags=re.IGNORECASE)
    tail = re.sub('Pacific|West|Cali|Seattle|Oregon| (?<=[0-9]*)pst| (?<=[0-9]*)pdt| (?<=[0-9]*)pt', ' PST ', tail, flags=re.IGNORECASE)
    tail = re.sub('Mountain|Denver|Colorado| (?<=[0-9]*)mst| (?<=[0-9]*)mdt| (?<=[0-9]*)mt', ' MST ', tail, flags=re.IGNORECASE)
    tail = re.sub('Central|Chicago|Texas|Minnesota|Houston|Dallas|Austin| (?<=[0-9]*)cst| (?<=[0-9]*)cdt| (?<=[0-9]*)ct', ' CST ', tail, flags=re.IGNORECASE)
    tail = re.sub('East| NY|New York|Boston|Florida|Philly|Detroit| DC| (?<=[0-9]*)est| (?<=[0-9]*)edt| (?<=[0-9]*)et', ' EST ', tail, flags=re.IGNORECASE)
    # parse for datetime and convert to pacific time
    # (because idk it's necessary for the timestamp thingy to work)
    ts = None
    try:
        ts = parse(tail, fuzzy=True, tzinfos=timezone_info).astimezone()#gettz("America/Los_Angeles"))
    except ValueError:
        await message.reply(f'### Not a valid timestamp!')
        return

    timestamp = str(time.mktime(ts.timetuple()))[:-2]
    await message.reply(f'{header}\n## <t:{timestamp}:F>\n## <t:{timestamp}:R>', )


async def botscan(logger, guild, message):
    total = 0
    count = 0
    await message.reply(f'### Scanning for botters in {guild}')
    async with aiofiles.open('../bot_logs/' + str(guild) + '.json', 'a', encoding="utf-8") as f:
        for member in guild.members:
            if member.activities and (any((bot_name in activity.name.lower() and all(app_name not in activity.name.lower() for app_name in whitelisted_apps)) for activity in list(member.activities) for bot_name in bot_names)
            or any((hasattr(activity, 'application_id') and bot_id == activity.application_id) for activity in list(member.activities) for bot_id in bot_ids)):
                activities = []
                for activity in member.activities:
                    if hasattr(activity, 'application_id'):
                        activities.append({activity.name: activity.application_id})
                    else:
                        activities.append({activity.name: 'unknown id'})
                if activities:
                    output_str = '{"activities": ' + json.dumps(activities) + ', "name": "' + str(member.display_name) + '", "username": "' + member.name + '", "user_id": ' + str(member.id) + '", "timestamp": ' + str(datetime.datetime.now().replace(microsecond=0)) + '}\n'
                    await f.write(output_str)
                    msg = f'### <@{member.id}> currently running {[next(iter(activity)) for activity in activities]}'
                    for activity in activities:
                        if hasattr(activity, 'assets'):
                            if activity['assets']['small_image_url']:
                                msg += '\n' + activity['assets']['small_image_url']
                            elif activity['assets']['large_image_url']:
                                msg += '\n' + activity['assets']['large_image_url']
                    await message.reply(msg)
                    count += 1
            total += 1
        await f.write('\n\n')
    await message.reply(f'### {total} members scanned, {count} potential botters found in {guild}')
    logger.info('----------------------------------------------------------------------')
    logger.info(f'{total} members scanned, {count} potential botters found in {guild}')
    logger.info('----------------------------------------------------------------------\n\n')

# async def forward_link(logger, output_channel, message):
#     output_header = ''
#     output_str = '##'
#     if message.embeds:
#         output_header = '# [' + message.embeds[0].title + '](' + message.embeds[0].url + ')\n'
#         output_str += '#'
#     output_str += ' ' + re.sub('<@&[0-9]*>', '', message.content)       #strip mentions
#     output_str = re.sub('\n', '\n### ', output_str)                     #header new lines
#     output_roles = f'### <@&{free_role}>'                                #free roles
#     for role in message.role_mentions:
#         if role.id in roles1 and roles2[roles1[role.id]] != -1:
#             output_roles += (' <@&' + str(roles2[roles1[role.id]]) + '>')
#     for domain in domain_roles:
#         if domain in message.content:
#             output_roles += (' <@&' + str(domain_roles[domain]) + '>')
#     if 'https://' in message.content and all(domain not in message.content for domain in domain_roles):
#         output_roles += (' <@&' + str(domain_roles['other_retailers']) + '>')
#     message_ids[(message.channel.id, message.id)] = (output_channel.id, (await output_channel.send(output_header + output_str + '\n' + output_roles + '\n**Sent by: <@' + str(message.author.id) + '>**')).id)
#     message_ids_rev[message_ids[(message.channel.id, message.id)]] = (message.channel.id, message.id)
#     logger.info('----------------------------------------------------------------------')
#     logger.info(f'Received msg from {message.channel}: {message.id}')
#     logger.info(f'Sending msg to {output_channel}: {message_ids[(message.channel.id, message.id)][1]}')
#     logger.info('----------------------------------------------------------------------\n\n')

async def forward_link_embed(client, logger, output_channel, message, msg_str):
    if msg_str:
        (msg, embed) = await generate_embed_msg(client, logger, output_channel, message, msg_str, '')
        id = (await output_channel.send(msg, embed=embed)).id
        logger.info('----------------------------------------------------------------------')
        logger.info(f'Received multiple links from {message.channel}: {message.id}')
        logger.info(f'Sending additional msg to {output_channel}: {id}')
        logger.info('----------------------------------------------------------------------\n\n')
    else:
        (msg, embed) = await generate_embed_msg(client, logger, output_channel, message, '', '')
        if (message.channel.id, message.id) not in message_ids:
            message_ids[(message.channel.id, message.id)] = [(output_channel.id, (await output_channel.send(msg, embed=embed)).id)]
            message_ids_rev[message_ids[(message.channel.id, message.id)][-1]] = (message.channel.id, message.id)
        else:
            message_ids[(message.channel.id, message.id)].append((output_channel.id, (await output_channel.send(msg, embed=embed)).id))
            message_ids_rev[message_ids[(message.channel.id, message.id)][-1]] = (message.channel.id, message.id)
        logger.info('----------------------------------------------------------------------')
        logger.info(f'Received msg from {message.channel}: {message.id}')
        logger.info(f'Sending msg to {output_channel}: {message_ids[(message.channel.id, message.id)][-1][1]}')
        logger.info('----------------------------------------------------------------------\n\n')

async def update_link_embed(client, logger, output_channel, message, msg_to_edit):
    main_url = ''
    msg_str = ''
    words = []
    for word in message.content.split():
        if 'https://' in word:
            temp = urlparse(word)
            url = temp.scheme + "://" + temp.netloc + temp.path
            if main_url == '':
                words.append('\n')
                main_url = url
            else:
                words.append(url+'\n')
        else:
            words.append(word)
    (msg, embed) = await generate_embed_msg(client, logger, output_channel, message, msg_str, main_url)
    await msg_to_edit.edit(content=msg, embed=embed)

async def remove_tracking(logger, output_channel, message):
    msg_to_forward = message
    words = []
    tracking = False
    for word in message.content.split():
        if 'https://' in word:
            temp = urlparse(word)
            url = temp.scheme + "://" + temp.netloc + temp.path
            diff_str = word.replace(url, '')
            logger.info(f'{diff_str}')
            if 'bestbuy.com' in url and (re.match(r".*skuId=[0-9]+", diff_str) or re.match(r"\?skuId=[0-9]+(&sb_share_source=PDP)?", diff_str)):
                i = word.find('skuId=')
                url += '?' + word[i:i+13]
                logger.info('----------------------------------------------------------------------')
                logger.info(f'sku = {word[i:i+13]}')
                logger.info(f'url: {url}')
                logger.info('----------------------------------------------------------------------\n\n')


            if all(role not in message.author.roles for role in mod_roles) and word != url and not diff_str=='#'+temp.fragment and not diff_str=='?' and not re.match(r"\?skuId=[0-9]+(&sb_share_source=PDP)?", diff_str):
                logger.info('----------------------------------------------------------------------')
                logger.info(f'Cleaning up url: {word}')
                logger.info(f'New url: {url}')
                logger.info('----------------------------------------------------------------------\n\n')
                tracking = True
            words.append(url+'\n')
        else:
            words.append(word)
    if tracking:
        msg_str = ' '.join(words)
        msg_str = re.sub('\n\n', '\n', msg_str)
        msg_str = re.sub('\n\n', '\n', msg_str)
        msg_str = re.sub('\n ', '\n', msg_str)                  #trim whitespace
        msg_str = re.sub('\n ', '\n', msg_str)                  #trim whitespace
        msg_str = re.sub('\n(?!$)', '\n### ', msg_str)                  #formatting
        msg_str = '## Clean your URLs! <:wigglystare:1354384557452951613> <:wigglystare:1354384557452951613>\n### '+ msg_str
        msg_to_forward = await message.reply(msg_str)
        await message.delete()
    else:
        pass
    return msg_to_forward

async def log_message(client, logger, output_channel, message, type):
    if type == 'bulk_info':
        payload = message
        embed_dict = {
            "author": {
                "name": client.get_guild(payload.guild_id).name,
                "icon_url": output_channel.guild.icon.url
            },
            "description": f'**Bulk deletion in <#{payload.channel_id}>, deleted {len(payload.message_ids)} messages**\n',
            "flags": 0,
            "color": 15049215, # hex code 0xe5a1ff
            "timestamp": str(datetime.datetime.now(timezone)),
            "type": "rich"
        }
        embed=discord.Embed.from_dict(embed_dict)
        await output_channel.send(embed=embed)
        return


    if message.author.display_name != message.author.name:
        length = len(message.author.display_name+message.author.name)
        name_str = message.author.display_name + '   |   @' + message.author.name
    else:
        name_str = '@' + message.author.name

    embed_dict = {
        "author": {
            "name": name_str,
            "icon_url": message.author.display_avatar.url,
        },
        "description": f'** Message sent by <@{message.author.id}> deleted in <#{message.channel.id}>**\n',
        "footer": {
            "text": f'Author: {message.author.id}  |  Message ID: {message.id}'
        },
        "flags": 0,
        "color": 15049215, # hex code 0xe5a1ff
        "timestamp": str(datetime.datetime.now(timezone)),
        "type": "rich"
    }
    if type == 'bulk':
        embed_dict["description"] = f'**Message sent by <@{message.author.id}> bulk deleted in <#{message.channel.id}>**\n'

    if message.content:
        embed_dict['description'] += message.content
        embed=discord.Embed.from_dict(embed_dict)
        await output_channel.send(embed=embed)

    if type == 'bulk':
        embed_dict["description"] = f'**Media sent by <@{message.author.id}> bulk deleted in <#{message.channel.id}>**\n'
    else:
        embed_dict['description'] = f'**Media sent by <@{message.author.id}> deleted in <#{message.channel.id}>**\n'
    for attachment in message.attachments:
        new_msg = None
        try:
            new_msg = await archive_channels[message.channel.guild.id].send(file=(await attachment.to_file(use_cached=True)))
        except discord.errors.NotFound:
            new_msg = await archive_channels[message.channel.guild.id].send(file=(await attachment.to_file(use_cached=False)))
        new_url = new_msg.attachments[0].url.replace('cdn.discordapp.com', 'media.discordapp.net')
        embed_dict['image'] = {'url': new_url}
        embed=discord.Embed.from_dict(embed_dict)
        await output_channel.send(embed=embed)


async def botter_alert(logger, member):
    # to avoid spam
    if member.id in botter_detection_count and botter_detection_count[member.id] >= 2:
        return

    activities = []
    for activity in member.activities:
        if hasattr(activity, 'application_id'):
            activities.append({activity.name: activity.application_id})
        else:
            activities.append({activity.name: 'unknown id'})
    if activities:
        output_str = '{"activities": ' + json.dumps(activities) + ', "name": "' + str(member.display_name) + '", "username": "' + member.name + '", "user_id": ' + str(member.id) + '", "timestamp": ' + str(datetime.datetime.now().replace(microsecond=0)) + '}\n'
        logger.info('----------------------------------------------------------------------')
        if member.id in botter_detection_count:
            botter_detection_count[member.id] += 1
        else:
            botter_detection_count[member.id] = 1

        for channel in bot_channels:
            msg = f'### {' '.join(['<@' + str(id) + '>' for id in bot_mentions[channel.id]])} Potential botter found in {member.guild.name}! <@{str(member.id)}> currently running {[next(iter(activity)) for activity in activities]}'
            for activity in activities:
                if hasattr(activity, 'assets'):
                    if activity['assets']['small_image_url']:
                        msg += '\n' + activity['assets']['small_image_url']
                    elif activity['assets']['large_image_url']:
                        msg += '\n' + activity['assets']['large_image_url']
            await channel.send(msg, silent=True)
            async with aiofiles.open('../bot_logs/unified_log.json', 'a', encoding="utf-8") as f:
                await f.write(output_str)
                await f.write('\n')
            logger.info(f'Potential botter detected in {member.guild}, sending message to {channel.guild}{' '*(35-len(str(member.guild)+str(channel.guild)))} - {channel}')
        logger.info('----------------------------------------------------------------------\n\n')

async def generate_embed_msg(client, logger, output_channel, message, msg_str, embed_url):
    words = []
    no_urls = []
    output_header = ''
    main_url = ''
    msg_str = msg_str if msg_str else message.content
    for word in msg_str.split():
        if 'https://' in word:
            temp = urlparse(word)
            url = temp.scheme + "://" + temp.netloc + temp.path
            diff_str = word.replace(url, '')
            logger.info(f'{diff_str}')
            if 'bestbuy.com' in url and re.match(r".*skuId=[0-9]+.*", diff_str):
                i = word.find('skuId=')
                url += '?' + word[i:i+13]

            if main_url == '':
                if words:
                    words.append('\n')
                    no_urls.append('\n')
                main_url = url
            else:
                words.append(url+'\n')
                no_urls.append('\n')
        elif '#' not in word:
            words.append(word)
            no_urls.append(word)

    output_header = f'# [{message.embeds[0].title}]({embed_url})' if embed_url and message.embeds else f'# [{message.embeds[0].title}]({main_url})' if message.embeds else '# '+embed_url if embed_url else '# '+main_url if main_url else ''
    output_str = ' '.join(no_urls)


    output_str = re.sub('Clean your URLs! <:wigglystare:1354384557452951613> <:wigglystare:1354384557452951613> ', '', output_str)  #remove the tracking thingy
    output_str = re.sub('<@&[0-9]*>', '', output_str)                                #strip mentions
    output_str = re.sub('\n\n', '\n', output_str)                                    #strip extra lines
    output_str = re.sub('\n\n', '\n', output_str)                                    #strip extra lines
    output_str = re.sub('(?<=^)[\n# ]*', '', output_str)                              #strip leading lines
    output_str = re.sub('\n', '\n### ', output_str)                                 #formatting
    output_str = re.sub('\n### $', '', output_str)                                  #formatting
    output_str = '## ' + output_str if output_str.strip() else ''

    tail = ' '.join(words)
    if 'https://' in tail and not embed_url:         #dont recurse on edited messages
        main_url = embed_url if embed_url else main_url
        await forward_link_embed(client, logger, output_channel, message, msg_str[msg_str.find(main_url)+len(main_url):]) #output_str[output_str.find('https://'):])


    output_roles = f'### <@&{free_role}>'        #free roles
    for role in message.role_mentions:
        if role.id in roles1 and roles2[roles1[role.id]] != -1:
            output_roles += (' <@&' + str(roles2[roles1[role.id]]) + '>')

    for domain in domain_roles:
        if domain in (embed_url if embed_url else msg_str):
            output_roles += (' <@&' + str(domain_roles[domain]) + '>')

    if 'https://' in msg_str and all(domain not in msg_str for domain in domain_roles):
        output_roles += (' <@&' + str(domain_roles['other_retailers']) + '>')

    output_roles += '\n'+message.jump_url

    if message.author.name == 'JigglyBot' and message.reference.cached_message:
        og_author = message.reference.cached_message.author
        if og_author.display_name != og_author.name:
            length = len(og_author.display_name+og_author.name)
            name_str = og_author.display_name + '   |   @' + og_author.name
        else:
            name_str = '@' + og_author.name
    else:
        if message.author.display_name != message.author.name:
            length = len(message.author.display_name+message.author.name)
            name_str = message.author.display_name + '   |   @' + message.author.name
        else:
            name_str = '@' + message.author.name

    site = ''
    for domain in domain_names:
        if domain in main_url:
            site = domain_names[domain]

    # logger.info('')
    # logger.info(output_str)
    # logger.info(output_str[-4:])
    # logger.info('')
    embed_dict = {
        "title": (message.embeds[0].title if message.embeds else main_url),
        "author": {
            "name": name_str,
            "icon_url": message.author.display_avatar.url
        },
        "description": output_str,
        "footer": {
            "text": main_url
            #"icon_url": message.author.display_avatar.url
        },
        "url": (main_url if message.embeds and message.embeds[0].url else None),
        #"image": ({'url':message.embeds[0].thumbnail.url} if message.embeds and message.embeds[0].thumbnail else None),
        "thumbnail": ({'url':message.embeds[0].thumbnail.url} if message.embeds and message.embeds[0].thumbnail else None),
        "color": (message.embeds[0].color.value if message.embeds and message.embeds[0].color else 15049215),
        "flags": 0,
        "timestamp": str(datetime.datetime.now(timezone)),
        "type": "rich"
    }
    # panda_links_channel = client.get_channel(panda_links_id)
    # logger.info('----------------------------------------------------------------------')
    # logger.info(f'output_channel = {output_channel.id}, type: {type(output_channel.id)}')
    # logger.info(f'panda_channel = {panda_links_id}, type: {type(panda_links_id)}')
    # logger.info(f'equal? {output_channel.id == panda_links_id}')
    # logger.info('----------------------------------------------------------------------\n\n')
    # hardcoded panda forwarding, don't include any pings
    if output_channel.id == panda_links_id:
        return (output_header+'\n'+message.jump_url, discord.Embed.from_dict(embed_dict))
    else:
        return (output_header+'\n'+output_roles, discord.Embed.from_dict(embed_dict))

async def print_leaderboard(client, logger, message, channel):
    output_str = '## <:espfetti:1350942179522121891> Code Card Leaderboards <:espfetti:1350942179522121891>\n```'
    if message:
        search_id = message.author.id

    with open('random_data/code_card_leaderboard.json', 'r') as f:
        leaderboard = json.load(f)
        top_users = dict(sorted(leaderboard.items(), key=lambda item: item[1], reverse=True))
        if message.mentions:
            search_id = message.mentions[0].id
            if str(search_id) not in leaderboard:
                leaderboard[str(search_id)] = 0
        count = 0
        found = False
        for (user, total) in top_users.items():
            count += 1
            found = (found or user == str(search_id))
            if count <= leaderboard_count:
                guild = client.get_guild(prem_id)
                name = (await guild.fetch_member(user)).display_name
                output_str += f'\n{count}. {name}{' '*(31-len(name)-len(str(count)))}|{' '*(4-len(str(total)))}{total}'
                if '⚡' in name:
                    output_str = output_str.replace('                        ', '                       ')
                if count == leaderboard_count and found:
                    break
            elif count > leaderboard_count and found:
                guild = client.get_guild(prem_id)
                name = (await guild.fetch_member(user)).display_name
                output_str += f'\n{' '*15}.\n{' '*15}.\n{count}. {name}{' '*(31-len(name)-len(str(count)))}|{' '*(4-len(str(total)))}{total}'
                if '⚡' in name:
                    output_str = output_str.replace('                        ', '                       ')
                break
            elif count > leaderboard_count:
                pass

    await channel.send(output_str+'\n```')