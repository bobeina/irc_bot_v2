"""
irc.py
bot class
2020/06/30 17:35
"""
import re
import sys
from pathlib import Path
import random
import socket, asyncio
import errno

import time


sys.path.append(Path().resolve().parent)


class IRC:
    def __init__(self):
        """
        原先版本的socket屏蔽
        """
        # Define the socket
        # self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = None
        self.socket_reader = None
        self.socket_writer = None

    async def chat(self, channel, msg):
        # Transfer data
        data = bytes("PRIVMSG " + channel + " :" + msg + "\r\n", "UTF-8")
        print('sending data: ', data)
        self.socket_writer.write(data)

    async def connect(self, server, port, loop):
        # self.socket = socket.create_connection((server, port), 10)
        print('IRC.connect(): connecting {s}:{p} ...'.format(s=server, p=port))
        # self.socket_reader, self.socket_writer = await asyncio.open_connection(server, port, loop=loop)
        fut = asyncio.open_connection(server, port, loop=loop) #, ssl=True)
        try:
            # Wait for 3 seconds, then raise TimeoutError
            self.socket_reader, self.socket_writer = await asyncio.wait_for(fut, timeout=8)
        except asyncio.TimeoutError:
            print("Timeout, skipping {}".format(server))
            self.socket_reader, self.socket_writer = None, None
            return False
        except Exception as e:
            print(e)
            return False
        print('-'*50)
        return True
        # return fut

    def send_usernm_msg(self, bot):
        self.socket_writer.write(bytes("USER " + bot.nick + " " + bot.nick + " " + bot.nick + " :" + bot.real_name + "\r\n", "UTF-8"))
        # self.socket_writer.write(bytes("NICK " + bot_nick + "\n", "UTF-8"))
        # self.socket_writer.write(bytes("NICKSERV IDENTIFY " + bot_nick_pass + "\n", "UTF-8"))

    def join_channel(self, channel):
        join_msg = bytes("JOIN " + channel + "\r\n", "UTF-8")
        self.socket_writer.write(join_msg)

    #============================================
    # 一些自动响应
    def check_rizon_pong(self, text):
        # pong_pattern = re.compile('\:.*?\.rizon\..*? 513 WoodGolemMulder \:To connect type \/QUOTE PONG (\d*)')
        pong_pattern = re.compile(r':(\w+\.){2}\w+ 513 WoodGolemMulder \:To connect type \/QUOTE PONG (\d*)')
        pong = pong_pattern.match(text)
        print('check_rizon_pong(): ', pong)
        if pong is not None:
            return pong.group(1)
        return None

    def check_Indent_info(self, text):
        pattern1 = re.compile(r'\:(\w+\.){2}\w+ NOTICE \* \:\*\*\* ((Checking Ident)|(No Ident response))')
        # pattern2 = re.compile(r'\:(\w+\.){2}\w+ NOTICE \* \:\*\*\* Checking Ident')
        checking_Indent = pattern1.match(text)
        print('check_Indent_info(): checking_Indent: {nr2}'.format(
            nr2=checking_Indent
        ))
        if checking_Indent is not None:
            return True
        return False

    def check_not_registered_info(self, text):
        pattern1 = re.compile(r'\:(\w+\.){2}\w+ 451 WoodGolemMulder \:You have not registered')
        not_registered_1 = pattern1.match(text)
        print('check_not_registered_info(): not_registered_1 - {nr1}'.format(
            nr1=not_registered_1
        ))
        if not_registered_1 is not None:
            return True
        return False

    def check_registered_info(self, text):
        # pattern = re.compile(r' :(\w+\.){2}\w+ 451 WoodGolemMulder :You have not registered')
        pattern = re.compile(r'\:NickServ\!service\@rizon\.net NOTICE WoodGolemMulder \:You are already identified')
        # ':NickServ!service@rizon.net NOTICE WoodGolemMulder :You are already identified.'
        not_registered = pattern.match(text)
        print('check_registered_info(): ', not_registered)
        if not_registered is not None:
            return True
        return False

    def check_registered_and_protected_info(self, text):
        # pattern = re.compile(r' :(\w+\.){2}\w+ 451 WoodGolemMulder :You have not registered')
        pattern = re.compile(r'\:NickServ\!service\@rizon\.net NOTICE WoodGolemMulder :This nickname is registered and protected\. If it is your')
        # ':NickServ!service@rizon.net NOTICE WoodGolemMulder :You are already identified.'
        nnp = pattern.match(text)
        print('check_registered_and_protected_info(): ', nnp)
        if nnp is not None:
            return True
        return False

    def check_recognized_info(self, text):
        # pattern = re.compile(r' :(\w+\.){2}\w+ 451 WoodGolemMulder :You have not registered')
        pattern = re.compile(r'\:NickServ\!service\@rizon\.net NOTICE WoodGolemMulder :Password accepted - you are now recognized\.')
        # ':NickServ!service@rizon.net NOTICE WoodGolemMulder :You are already identified.'
        nnp = pattern.match(text)
        print('check_recognized_info(): ', nnp)
        if nnp is not None:
            return True
        return False

    async def get_response(self, bot):
        # time.sleep(1)
        # Get the response
        raw_resp = await self.socket_reader.read(4096)
        resp = raw_resp.decode("UTF-8")
        print('='*100)
        print('IRC.get_response():<<<<<<{t}>>>>>>'.format(t=resp))
        msg_list = resp.split('\n')
        for line in msg_list:
            msg = line.strip()
            if len(msg) == 0:
                continue
            rmsg = None
            if resp[:4] == 'PING':
                # print('Get a ping: <{r}>'.format(r=resp))
                # rmsg = bytes('PONG ' + resp.split()[1] + '\r\n', "UTF-8")
                rmsg = 'PONG ' + resp.split()[1]
                # rmsg = '/QUOTE PONG ' + resp.split()[1] + '\n'
            elif self.check_Indent_info(msg):  # 发送 nick
                rmsg = "NICK " + bot.nick
            elif self.check_not_registered_info(msg) and bot.login_msg_sent > 0 :  # 发送 pwd
            # elif self.check_not_registered_info(msg):  # 发送 pwd
                rmsg = "NICKSERV IDENTIFY " + bot.pwd + " " + bot.nickpass
                # rmsg = '/msg NickServ identify ' + bot.pwd
                bot.login_msg_sent -= 1
            elif self.check_registered_and_protected_info(msg):  # 发送 pwd
            # elif self.check_not_registered_info(msg):  # 发送 pwd
                rmsg = "NICKSERV IDENTIFY " + bot.pwd + " " + bot.nickpass
                # rmsg = '/msg NickServ identify ' + bot.pwd
                bot.login_msg_sent -= 1
            # elif self.check_registered_info(msg) and bot.identified == False:  # 收到登录成功信息
            #     bot.identified = True
            elif self.check_recognized_info(msg) and bot.identified == False:  # 收到登录成功信息
                bot.identified = True
            else:
                pong = self.check_rizon_pong(msg)
                if pong is not None:
                    # print('Get a PONG: <{r}>'.format(r=resp))
                    rmsg = "/QUOTE PONG " + pong
            print(' | rmsg: ', rmsg)
            if rmsg is not None:
                self.socket_writer.write(bytes(rmsg + '\r\n', "UTF-8"))
        return resp
        # return raw_resp

    def parse_text(self, raw_text):
        """
        消息格式举例： :aweoOO!~Thunderbi@112.8.99.11 PRIVMSG ##Amestris :ConciergeBot
        :param raw_text:
        :return:
        """
        # pattern = re.compile(r"\:(.*?)\!\~(.*?)\@(\d{1:3}\.\d{1:3}\.\d{1:3}\.\d{1:3}) PRIVMSG (.*?) \:(.*)")
        pattern = re.compile(r"\:(.*?)\!\~(.*?)\@(.*?) PRIVMSG (.*?) \:(.*)")
        result = pattern.search(raw_text)
        if result is None:
            return None
        speaker = result.group(1)
        client = result.group(2)
        ip = result.group(3)
        channel = result.group(4)
        text = result.group(5)
        data = {
            'speaker': speaker,
            'client': client,
            'from': ip,
            'channel': channel,
            'text': text #.strip()
        }
        return data

    async def do_react(self, data, bot, channel):
        reactions = bot.react(data)
        for r in reactions:
            await self.chat(channel, r)
            await asyncio.sleep(0.1)


