"""
main.py
2020/06/30 17:05
"""
import time
import asyncio
import sys
from pathlib import Path

sys.path.append(Path().resolve().parent)
from irc import IRC
from bot import Bot
from account_info import bot_account


class Coordinator:
    def __init__(self):
        self.run_flag = False


async def irc_bot_init_jobs(irc, bot, loop, coordinator):
    index = 0
    # port = bot_account['port_list'][0]
    port = 6667
    for server in bot_account['server_list']:
        if irc.socket_reader is None:
            rflag = await irc.connect(server, port, loop=loop)
            counter = 15
            while irc.socket_reader is None and counter >= 0:
                await asyncio.sleep(1)
                counter -= 1
                print('Init waiting for connect: ', counter, end=' ...\n')
                if rflag == False:
                    bot.not_identified_counter = 12
        else:
            break

    # if irc.socket_reader is not None and bot.identified:
    if irc.socket_reader is not None:
        resp = irc.get_response(bot)
        print('Connection success ... start login now: resp = {r}'.format(r=resp))
        irc.send_usernm_msg(bot)
        # await asyncio.sleep(1)

    # 这一部分还是会有问题，有时候会错过一些消息
    bot.not_identified_counter = 12
    while not bot.identified and bot.not_identified_counter > 0:
        await asyncio.sleep(1)
        bot.not_identified_counter -= 1
        print('Init waiting for bot identified: ', bot.not_identified_counter, end=' ...\n')
    for channel in bot.channels:
        irc.join_channel(channel)
    else:
        print('Opps... connection failed.')


def find_channels_in_text(channels, text):
    for c in channels:
        if c in text:
            return c
    return None


async def run_irc_bot(irc, bot, loop, coordinator):
    counter = 60
    while irc.socket_reader is None: # and coordinator.run_flag:
        await asyncio.sleep(1)
        counter -= 1
        if counter < 0:
            coordinator.run_flag = False
    while coordinator.run_flag:
        text = await irc.get_response(bot)
        if text is not None:
            if len(text) > 0:
                print('main() get_response:<{t}>'.format(t=text))
        else:
            print('0.0')
            # coordinator.run_flag = False
            # break

        channel_in_text = find_channels_in_text(bot.channels, text)
        if "PRIVMSG" in text and channel_in_text is not None:
            data = irc.parse_text(text)
            print('parsed text: ', data)
            if data is not None:
                await irc.do_react(data, bot, channel_in_text)


def main():
    coordinator = Coordinator()
    coordinator.run_flag = True
    irc = IRC()
    bot = Bot(bot_account['usernm'],
              bot_account['pwd'],
              bot_account['channels'],
              bot_account['main_channel']
              )

    loop = asyncio.get_event_loop()
    loop.create_task(irc_bot_init_jobs(irc, bot, loop, coordinator))
    loop.create_task(run_irc_bot(irc, bot, loop, coordinator))
    loop.run_forever()


main()
