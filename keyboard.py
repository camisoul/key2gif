#!/usr/bin/env python

import re
import configparser
from PIL import Image, ImageDraw, ImageFont


IMAGE_WIDTH = 640
IMAGE_HEIGHT = 360

# 設定読み込み
config = configparser.ConfigParser()
config.read('./settings.txt', 'UTF-8')


# キーテーブル読み込み
class KeyData:
    def __init__(self, name, text):
        self.name = name
        self.text = text
        self.points = []

    def append(self, pos):
        self.points.append(pos)


def ReadNormalLines(f):
    result = []
    pattern = r'^\s*(#.*|)$'
    line = f.readline()
    while line:
        match = re.match(pattern, line)
        if not match:
            result.append(line)
        line = f.readline()
    return result


def LoadInput(filename):
    result = []
    with open(filename, 'r') as f:
        lines = ReadNormalLines(f)
        for line in lines:
            i, o = line.split('|')
            result.append((i, o.rstrip()))
    return result


def LoadTable(filename):
    # キーと座標のテーブルを作成
    keytable = []
    with open(filename, 'r') as f:
        lines = ReadNormalLines(f)
        # 最初の1行はテキストエリアの高さ
        text_height = int(lines[0])
        # 最初の6行はEnter
        k, n = lines[1].split()
        enter = KeyData(k, n)
        for i in range(6):
            x1, y1, x2, y2 = lines[2 + i].split(',')
            enter.append((int(x1), int(y1), int(x2), int(y2)))
        keytable.append(enter)
        # 8行目からは1行おき
        count = 0
        temp = None
        for line in lines[8:]:
            while line:
                count += 1
                if count % 2 == 1:
                    k, n = line.split()
                    temp = KeyData(k, n)
                else:
                    x1, y1, x2, y2 = line.split(',')
                    temp.append((int(x1), int(y1), int(x2), int(y2)))
                    keytable.append(temp)
                line = f.readline()
    return (text_height, keytable)


text_height, keytable = LoadTable(config['main']['file'])
table = LoadInput(config['main']['input'])


# アニメーションするキー画像
class KeyImage:
    INVISIBLE = (255, 255, 255, 0)

    def __init__(self, keytable, size, duration=4, color=(255, 64, 64)):
        self.im = Image.new('RGBA', size, self.INVISIBLE)
        self._keytable = keytable
        self._pos = []
        self._alpha = 255
        self._duration = duration
        self._r, self._g, self._b = color

    def _draw(self):
        pic = ImageDraw.Draw(self.im)
        for pos in self._pos:
            pic.rectangle(
                pos,
                fill=(self._r, self._g, self._b, self._alpha))

    def Update(self):
        if self._alpha > 0:
            self._alpha = max(self._alpha - 255 // self._duration, 0)
            self._draw()
        else:
            self._alpha = 0

    def SetKey(self, key):
        for k in self._keytable:
            if (key == k.name):
                for p in k.points:
                    self._pos.append(p)


class Runner:
    def __init__(self, keytable, keys,
                 wait=2, pre_wait=10, post_wait=20,
                 fg_color=(0, 0, 0),
                 bg_color=(255, 255, 255),
                 key_color=(64, 64, 64),
                 text_color=(255, 224, 224),
                 width=640,
                 padding=(2, 2),
                 text_height=120,
                 animation_color=(255, 64, 64),
                 animation_duration=4
                 ):
        self.images = []
        self._keytable = keytable
        self._keys = keys
        self._key_images = []

        r, g, b = bg_color
        self._keyboard = Image.new('RGBA',
                                   (IMAGE_WIDTH, IMAGE_HEIGHT),
                                   (r, g, b, 255))
        self._fg_color = fg_color
        self._key_color = key_color
        self._text_color = text_color
        self._text_height = text_height
        self._width = width
        self._padding = padding

        self._animation_duration = animation_duration
        self._animation_color = animation_color

        self._display = ''
        self._frame = 0
        self._index = 0
        self._wait = wait
        self._pre_wait = pre_wait
        self._post_wait = post_wait
        self._maxframe = pre_wait + (wait + 1) * len(keys) + post_wait

        self._draw_keyboard()

    def run(self):
        for i in range(self._maxframe):
            self._update()

    def _draw_text(self, im):
        pic = ImageDraw.Draw(im)
        w, h = pic.textsize(self._display, font=txtfnt)
        pic.text(((IMAGE_WIDTH - w) / 2, (self._text_height - h) / 2),
                 self._display,
                 fill=self._text_color, align='center', font=txtfnt)

    def _draw_only_display(self, im):
        self._draw_text(im)

    def _draw_key(self, im):
        key, char = self._keys[self._index]
        cin, cout = key
        if char == cin.split()[-1]:
            self._display += cout
        self._draw_text(im)
        key_image = KeyImage(self._keytable, im.size,
                             duration=self._animation_duration,
                             color=self._animation_color)
        for c in char:
            key_image.SetKey(c)
        self._key_images.append(key_image)
        self._index += 1

    def _update(self):
        im = self._keyboard.copy()
        span = self._wait + 1
        if self._frame < self._pre_wait:
            self._draw_only_display(im)
        elif (self._frame - self._pre_wait) % span == 0 and \
                self._frame < self._pre_wait + span * len(self._keys):
            self._draw_key(im)
        else:
            self._draw_only_display(im)
        for key_image in self._key_images:
            key_image.Update()
            im = Image.alpha_composite(im, key_image.im)
        self.images.append(im.resize(
            (self._width, self._width * 9 // 16),
            resample=Image.LANCZOS
            ))
        self._frame += 1

    def _draw_normal_key(self, draw, pos, label):
        x, y, _, _ = pos
        px, py = self._padding
        draw.text((x + px, y + py), label,
                  fill=self._key_color, align='center', font=keyfnt)
        draw.rectangle(pos, outline=self._fg_color)

    def _draw_keyboard(self):
        draw = ImageDraw.Draw(self._keyboard)
        for k in self._keytable:
            if len(k.points) == 1:
                self._draw_normal_key(draw, k.points[0], k.text)
            else:
                x, y, _, _ = k.points[0]
                px, py = self._padding
                draw.text((x + px, y + py), k.text,
                          fill=self._key_color, align='center', font=keyfnt)
                for p in k.points:
                    draw.line(p, fill=self._fg_color)


def HTML2Color(code):
    return (int(code[1:3], 16), int(code[3:5], 16), int(code[5:7], 16))


# 設定読み込み
duration = int(config['main']['duration'])
txtfnt = ImageFont.truetype(
        config['display']['textfont'],
        int(config['display']['textfontsize']))
keyfnt = ImageFont.truetype(
        config['display']['keyfont'],
        int(config['display']['keyfontsize']))

data = []
for t in table:
    for char in t[0].split():
        data.append((t, char))

runner = Runner(
        keytable, data,
        wait=int(config['main']['wait']),
        pre_wait=int(config['main']['prewait']),
        post_wait=int(config['main']['postwait']),
        width=int(config['main']['outputwidth']),
        fg_color=HTML2Color(config['display']['foregroundcolor']),
        bg_color=HTML2Color(config['display']['backgroundcolor']),
        key_color=HTML2Color(config['display']['keycolor']),
        text_color=HTML2Color(config['display']['textcolor']),
        text_height=text_height,
        animation_duration=int(config['animation']['duration']),
        animation_color=HTML2Color(config['animation']['color'])
        )
runner.run()
images = runner.images

images[0].save(config['main']['output'],
               save_all=True, append_images=images[1:],
               duration=duration, loop=0)
