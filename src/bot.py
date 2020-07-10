"""
bot.py
2020/06/16 18:02
"""
import re
import sys
import random
from pathlib import Path
from info_mulder import action_list as mulder_actions
from info_mulder import help_text as mulder_help

sys.path.append(Path().resolve().parent)


def action_format(text):
    return '\x01ACTION ' + text + '\x01'
    # return ' ACTION ' + text

class Bot:
    def __init__(self, nick, pwd, channels, main_channel=None):
        self.nick = nick
        self.nickpass = "<%= @{nick}_password %>".format(nick=nick)
        self.pwd = pwd
        self.real_name = 'An.Oak.Wood'
        self.channels = channels
        self.main_channel = main_channel
        self.identified = False
        self.login_msg_sent = 3
        self.help = mulder_help
        self.not_identified_counter = 12

    def react(self, data) -> list:
        print('react: Parsing text > {t}'.format(t=data['text']))
        if self.nick in data['text'] or '.mulder' in data['text'] or '.穆德' in data['text']:
            if 'help' in data['text']:
                return [action_format('举起一块牌子："' + line + '"') for line in self.help]
            rindex = random.randint(0, len(mulder_actions) - 1)
            return [action_format(mulder_actions[rindex])]
        else:
            check_dice_result = self.parse_check_dice_str(data['text'])
            print('check_dice_result: ', check_dice_result)
            if check_dice_result is not None:
                dice_result = action_format("举起了一块牌子：“" + str(data['speaker']) + " " + str(check_dice_result) + "”")
                return [dice_result]
            else:
                return []

    def parse_check_dice_str(self, text):
        color_bonus_str = ''
        bonus_sum = 0
        describe = ''
        pattern = re.compile(r'\.(\d+)d(\d+)( ([\+\-]\d+)+)*( .*)*')
        roll_txt = pattern.match(text)
        if roll_txt is None:
            return None
        dice_num = int(roll_txt.group(1))
        dice_side = int(roll_txt.group(2))
        if dice_num > 100000:
            # return action_format('手忙脚乱将一箱骰子全倒在了地上，成功吸引来了雨人。')
            return '：‘骰子滞销，帮帮我们！T.T！’'
        if dice_side not in range(1, 101):
            # return action_format('扔出了一个球，很快就滚得不见影了。')
            return '扔出了一个球，滚得老远。'
        if roll_txt.group(3) is not None:
            bonus_str = roll_txt.group(3).strip()
            bonus_list, bonus_str_list = self.parse_and_cal_bonus(bonus_str)
            bonus_sum = sum(bonus_list)
            print('bonus_str_list: ', bonus_str_list)
            color_bonus_str_list = [self.color_bonus_text(s) for s in bonus_str_list]
            color_bonus_str = ''.join(color_bonus_str_list)
            color_bonus_str += '\x03'
        if roll_txt.group(5) is not None:
            temp_txt = roll_txt.group(5).strip()
            describe = temp_txt
            if len(temp_txt) > 30:
                if len(describe) > 33:
                    describe = temp_txt[:30] + '...' + describe[-3:]
        rvalue = '进行 {desc}\3 检定：'.format(desc=self.color_text(describe, color=6))
        roll_result = self.roll(dice_num, dice_side)
        roll_sum = sum(roll_result)
        if dice_num > 50:
            roll_result_str = [self.color_dice_text(str(n)) for n in roll_result[:2]]
            roll_result_str.append('...')
            roll_result_str.append(self.color_dice_text(str(roll_result[-1])))
        else:
            # roll_result_str = [str(n) for n in roll_result]
            roll_result_str = [self.color_dice_text(str(n)) for n in roll_result]
        roll_sum_text = '\3 +'.join(roll_result_str)
        rvalue += " " + roll_sum_text + "   " + color_bonus_str + ' = \2' + str(roll_sum + bonus_sum)
        # result = action_format(rvalue)
        print('投骰结果：', rvalue)
        return rvalue

    def roll(self, dice_num, dice_side):
        result = []
        for d in range(dice_num):
            result.append(random.randint(1, dice_side))
        return result

    def parse_and_cal_bonus(self, bonus_str):
        pattern = re.compile(r'([\+\-]\d+)')
        bonus = pattern.findall(bonus_str)
        return [int(s) for s in bonus], [str(s) for s in bonus]

    def random_color(self, lower=0, upper=40):
        if lower > upper or lower >39 or upper >= 39 or lower < 0 or upper < 0:
            return '1'
        # colors = ["{0:02d}".format(i) for i in range(1, 40)]
        # return random.choice(colors)
        # return "{0:02d}".format(random.randint(lower, upper))
        return str(random.randint(lower, upper))

    def color_text(self, text, color=None):
        crnt_color = None
        if color is None:
            crnt_color = self.random_color()
        elif isinstance(color, list):
            crnt_color = random.choice(color)
        elif isinstance(color, int):
            crnt_color = color
        else:
            crnt_color = 1
        result = '\3{color} {text}'.format(
            color=crnt_color,
            text=text
        )
        return result

    def color_dice_text(self, text):
        # color = self.random_color(lower=2, upper=15)
        # color_list = [4, 8, 9, 11, 13, 15]
        # color_list = [2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]

        color_list = [2, 3, 4, 5, 6, 7, 10, 12, 13, 14]
        color = random.choice(color_list)
        # result = '\0x03 {color}{text}'.format(
        result = '\3{color} {text}'.format(
            color=color,
            text=text
        )
        return result

    def color_bonus_text(self, text):
        # color = self.random_color(lower=2, upper=15)
        # color_list = [2, 3, 5, 7, 10, 12, 14]
        # color_list = [2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]
        color_list = [2, 3, 4, 5, 6, 7, 10, 12, 13, 14]
        color = random.choice(color_list)
        result = '\3{color} {text}'.format(
            color=color,
            text=text
        )
        return result

