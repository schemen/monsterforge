import numpy as np
import cv2 as cv
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
from urllib.request import Request, urlopen
from fake_useragent import UserAgent
from greedypacker import BinManager
from .items import Item
import os, shutil, re
from collections import Counter

from paperminis.models import Creature
from paperminis.models import Bestiary
from paperminis.models import CreatureQuantity

class MiniBuilder():

    def __init__(self, user):

        # user
        self.user = user
        self.sanitize = re.compile('[^a-zA-Z0-9\(\)\_@]', re.UNICODE)  # sanitize user input
        self.clean_email = self.sanitize.sub('',self.user.email)
        self.user_dir = settings.MEDIA_ROOT + '/generate_minis/users/' + self.clean_email
        self.nginx_url = settings.MEDIA_URL + 'generate_minis/users/' + self.clean_email

        # Make sure media folder path exists
        if not os.path.isdir(self.user_dir):
                os.makedirs(self.user_dir)

        self.file_name_body = self.clean_email
        self.creatures = []
        self.enumerate = False

    def add_bestiary(self, pk):
        creature_quantities = CreatureQuantity.objects.filter(owner=self.user, bestiary=pk)

        bestiary_name = self.sanitize.sub('',creature_quantities.first().bestiary.name)
        if self.file_name_body == self.clean_email:
            self.file_name_body = bestiary_name
        else:
            self.file_name_body += '_'+bestiary_name
        if creature_quantities:
            creatures = []
            for cq in creature_quantities:
                creatures.extend([cq.creature] * cq.quantity)
            self.add_creatures(creatures)
        else:
            return False

    def add_creatures(self, creatures):
        if isinstance(creatures, Creature):
            # add single creature
            self.creatures.append(creatures)
        elif all(isinstance(c, Creature) for c in creatures):
            # add list of creatures
            self.creatures.extend(creatures)
        else:
            return False


    def load_settings(self,
                      paper_format='a4',
                      print_margin=np.array([3.5,4]),
                      grid_size=24,
                      base_shape='square',
                      enumerate=False,
                      force_name='no_force',
                      fixed_height=False,
                      darken=0):

        self.print_margin = print_margin
        self.dpmm = 10 # not fully supported setting yet, leave at 10
        self.grid_size = grid_size
        self.enumerate = enumerate
        self.force_name = force_name
        self.base_shape = base_shape
        self.fixed_height = fixed_height
        self.darken = darken
        self.font = cv.FONT_HERSHEY_SIMPLEX
        self.paper_format = paper_format
        paper = {'a3': np.array([297, 420]),
                 'a4': np.array([210, 297]),
                 'letter': np.array([216, 279]),
                 'legal': np.array([216, 356]),
                 'tabloid': np.array([279, 432])}
        self.canvas = (paper[paper_format] - 2 * print_margin) * self.dpmm
        self.header = {'User-Agent': str(UserAgent().chrome)}


    def build_all_and_zip(self):
        if self.enumerate:
            # if enumerate is true, settings are always loaded
            self.creature_counter = Counter([c.name for c in self.creatures])
            self.creature_counter = {key:val for key, val in self.creature_counter.items() if val > 1}

        self.minis = []
        for creature in self.creatures:
            mini = self.build_mini(creature)
            if not isinstance(mini, str):
                self.minis.append(mini)
            else:
                print('{} skipped with error: {}'.format(creature.name, mini))

        self.sheets = self.build_sheets(self.minis)
        self.zip_path = self.save_and_zip(self.sheets)
        # static fix
        self.zip_static_path = '/' + '/'.join(self.zip_path.split('/')[1:])

    def build_mini(self, creature):
        if not hasattr(self,'grid_size'):
            # check if settings loaded manually, otherwise load default settings
            self.load_settings()

        if not isinstance(creature,Creature):
            return 'Object is not a Creature.'

        if creature.img_url == '':
            return 'No image url found.'

        # Size-based settings in mm
        # after the change to how the font is handled, some settings here are obsolete
        # I will keep them in for now
        min_height_mm = 40
        if creature.size in ['S', 'T']:
            m_width = int(self.grid_size/2)
            max_height_mm = 30
            n_height = 6
            font_size = 1.15 # opencv "height"
            font_height = 40 # PIL drawing max height for n_height = 8
            font_width = 1
            enum_size = 1.2
            enum_width = 3
        elif creature.size == 'M':
            m_width = self.grid_size
            max_height_mm = 40
            n_height = 8
            font_size = 1.15 # opencv "height"
            font_height = 50 # PIL drawing max height for n_height = 8
            font_width = 1
            enum_size = 2.2
            enum_width = 3
        elif creature.size == 'L':
            m_width = self.grid_size * 2
            max_height_mm = 50
            n_height = 10
            font_size = 2
            font_height = 70
            font_width = 2
            enum_size = 5 * self.grid_size/24
            enum_width = 8 * self.grid_size/24
        elif creature.size == 'H':
            m_width = self.grid_size * 3
            max_height_mm = 60 if not self.paper_format == 'letter' else 51
            n_height = 12
            font_size = 2.5
            font_height = 80
            font_width = 2
            enum_size = 8
            enum_width = 16
        elif creature.size == 'G':
            m_width = self.grid_size * 4
            max_height_mm = 80 if not self.paper_format == 'letter' else 73
            n_height = 14
            font_size = 3
            font_height = 100
            font_width = 3
            enum_size = 14
            enum_width = 32
        else:
            return 'Invalid creature size.'
        ## end of settings

        # mm to px
        width = m_width * self.dpmm
        name_height = n_height * self.dpmm
        base_height = m_width * self.dpmm
        max_height = max_height_mm * self.dpmm
        if self.fixed_height:
            min_height = max_height
        else:
            min_height = min_height_mm * self.dpmm

        text = creature.name

        # scale for grid size
        enum_size = int(np.ceil(enum_size * self.grid_size / 24))
        enum_width = int(np.ceil(enum_size * self.grid_size / 24))
        min_height = int(np.ceil(min_height * self.grid_size / 24))

        ## OPENCV versions (with an attempt to use utf-8 but I couldn't get it to work) of the nameplate.
        # It is now done with PIL to have UTF-8 support.
        # name plate
        # if creature.show_name:
        #     n_img = np.zeros((name_height, width, 3), np.uint8) + 255
        #     x_margin = 0
        #     y_margin = 0
        #     # find optimal font size
        #     while x_margin < 2 or y_margin < 10:
        #         font_size = round(font_size - 0.05, 2)
        #         textsize = cv.getTextSize(text, self.font, font_size, font_width)[0]
        #         x_margin = n_img.shape[1] - textsize[0]
        #         y_margin = n_img.shape[0] - textsize[1]
        #     #        print(font_size, x_margin, y_margin)
        #     # write text
        #     textX = np.floor_divide(x_margin, 2)
        #     textY = np.floor_divide(n_img.shape[0] + textsize[1], 2)
        #
        #     cv.putText(n_img, text, (textX, textY), self.font, font_size, (0, 0, 0), font_width, cv.LINE_AA)
        #     cv.rectangle(n_img, (0, 0), (n_img.shape[1] - 1, n_img.shape[0] - 1), (0, 0, 0), thickness=1)
        #     # img = cv.circle(img, (100, 400), 20, (255,0,0), 3)
        # if creature.show_name:
        #     n_img = np.zeros((name_height, width, 3), np.uint8) + 255
        #     ft = cv.freetype.createFreeType2()
        #     ft.loadFontData(fontFileName='DejaVuSans.ttf', id=0)
        #     x_margin = 0
        #     y_margin = 0
        #     # find optimal font size
        #     while x_margin < 2 or y_margin < 10:
        #         font_size = round(font_size - 0.05, 2)
        #         textsize = ft.getTextSize(text, font_size, font_width)[0]
        #         x_margin = n_img.shape[1] - textsize[0]
        #         y_margin = n_img.shape[0] - textsize[1]
        #     #        print(font_size, x_margin, y_margin)
        #     # write text
        #     textX = np.floor_divide(x_margin, 2)
        #     textY = np.floor_divide(n_img.shape[0] + textsize[1], 2)
        #
        #     ft.putText(n_img, text, (textX, textY), font_size, (0, 0, 0), font_width, cv.LINE_AA)
        #     cv.rectangle(n_img, (0, 0), (n_img.shape[1] - 1, n_img.shape[0] - 1), (0, 0, 0), thickness=1)
        #     # img = cv.circle(img, (100, 400), 20, (255,0,0), 3)

        ## nameplate
        show_name = ""

        if self.force_name == "force_name":
            show_name = True
        elif self.force_name == "force_blank":
            show_name = False
        else:
            show_name = creature.show_name
        
        if show_name:
            # PIL fix for utf-8 characters
            n_img_pil = Image.new("RGB", (width, name_height), (255, 255, 255))
            x_margin = 0
            y_margin = 0
            # find optimal font size
            while x_margin < 2 or y_margin < 10:
                #print(font_height)
                unicode_font = ImageFont.truetype("./DejaVuSans.ttf", font_height)
                font_height = round(font_height - 2, 2)
                textsize = unicode_font.getsize(text)
                im_w, im_h = n_img_pil.size
                x_margin = im_w - textsize[0]
                y_margin = im_h - textsize[1]
            # write text
            textX = x_margin//2
            textY = y_margin//2
            draw = ImageDraw.Draw(n_img_pil)
            draw.text((textX, textY), text, font=unicode_font, fill=(0,0,0))
            n_img = np.array(n_img_pil)
            cv.rectangle(n_img, (0, 0), (n_img.shape[1] - 1, n_img.shape[0] - 1), (0, 0, 0), thickness=1)
        else:
            n_img = np.zeros((1, width, 3), np.uint8)



        ## mimiature image
        try:
            req = Request(creature.img_url, headers=self.header)
            with urlopen(req) as resp:
                arr = np.asarray(bytearray(resp.read()), dtype=np.uint8)
                m_img = cv.imdecode(arr, -1)  # Load it "as it is"
        except:
            return 'Image could not be found or loaded.'
        # fix grayscale images

        try:
            if len(m_img.shape) == 2:
                m_img = cv.cvtColor(m_img, cv.COLOR_GRAY2RGB)
        except:
            return 'Image could not be found or loaded.'

        # replace alpha channel with white for pngs (with fix for grayscale images)
        if m_img.shape[2] == 4:
            alpha_channel = m_img[:, :, 3]
            mask = (alpha_channel == 0)
            mask = np.dstack((mask, mask, mask))
            color = m_img[:, :, :3]
            color[mask] = 255
            m_img = color

        # find optimal size of image
        # leave 1 pixel on each side for black border
        if m_img.shape[1] > width - 2:
            f = (width - 2) / m_img.shape[1]
            m_img = cv.resize(m_img, (0, 0), fx=f, fy=f)
            white_vert = np.zeros((m_img.shape[0], 1, 3), np.uint8) + 255
            m_img = np.concatenate((white_vert, m_img, white_vert), axis=1)

        if m_img.shape[0] > max_height- 2:
            f = (max_height - 2) / m_img.shape[0]
            m_img = cv.resize(m_img, (0, 0), fx=f, fy=f)
            white_horiz = np.zeros((1, m_img.shape[1], 3), np.uint8) + 255
            m_img = np.concatenate((white_horiz, m_img, white_horiz), axis=0)

        if m_img.shape[1] < width:
            diff = width - m_img.shape[1]
            left = np.floor_divide(diff, 2)
            right = left
            if diff % 2 == 1: right += 1
            m_img = np.concatenate((np.zeros((m_img.shape[0], left, 3), np.uint8) + 255, m_img,
                                    np.zeros((m_img.shape[0], right, 3), np.uint8) + 255), axis=1)

        if m_img.shape[0] < min_height:
            diff = min_height - m_img.shape[0]
            top = np.floor_divide(diff, 2)
            bottom = top
            if diff % 2 == 1: bottom += 1
            if creature.position == Creature.WALKING:
                m_img = np.concatenate((np.zeros((diff, m_img.shape[1], 3), np.uint8) + 255, m_img), axis=0)
            elif creature.position == Creature.HOVERING:
                m_img = np.concatenate((np.zeros((top, m_img.shape[1], 3), np.uint8) + 255, m_img,
                                    np.zeros((bottom, m_img.shape[1], 3), np.uint8) + 255), axis=0)
            elif creature.position == Creature.FLYING:
                m_img = np.concatenate((m_img,np.zeros((diff, m_img.shape[1], 3), np.uint8) + 255), axis=0)
            else:
                return 'Position setting is invalid. Chose Walking, Hovering or Flying.'

        #draw border
        cv.rectangle(m_img, (0, 0), (m_img.shape[1] - 1, m_img.shape[0] - 1), (0, 0, 0), thickness=1)

        ## flipped miniature image
        m_img_flipped = np.flip(m_img, 0)
        if self.darken:
            # change Intensity (V-Value) in HSV color space
            hsv = cv.cvtColor(m_img_flipped, cv.COLOR_BGR2HSV)
            h, s, v = cv.split(hsv)
            # darkening factor between 0 and 1
            factor = max(min((1-self.darken/100),1),0)
            v[v < 255] = v[v < 255] * (factor)
            final_hsv = cv.merge((h, s, v))
            m_img_flipped = cv.cvtColor(final_hsv, cv.COLOR_HSV2BGR)



        ## base
        bgr_color = tuple(int(creature.color[i:i + 2], 16) for i in (4, 2, 0))
        demi_base = base_height // 2
        if creature.size == 'G': feet_mod = 1
        else: feet_mod = 2
        base_height = int(np.floor(demi_base * feet_mod))
        b_img = np.zeros((base_height, width, 3), np.uint8) + 255
        # fill base
        if self.base_shape == 'square':
            cv.rectangle(b_img, (0, 0), (b_img.shape[1] - 1, demi_base - 1), bgr_color, thickness=-1)
            cv.rectangle(b_img, (0, 0), (b_img.shape[1] - 1, b_img.shape[0] - 1), (0,0,0), thickness=1)
        elif self.base_shape == 'circle':
            cv.ellipse(b_img, (width//2, 0), (width//2, width//2), 0, 0, 180, bgr_color, -1)
            cv.ellipse(b_img, (width // 2, 0), (width // 2, width // 2), 0, 0, 180, (0,0,0), 2)
            if feet_mod >= 2:
                cv.ellipse(b_img, (width // 2, base_height), (width // 2, width // 2), 0, 180, 360, (0, 0, 0), 2)
                cv.line(b_img, (0, base_height), (width, base_height), (0,0,0), 3)
        elif self.base_shape == 'hexagon':
            half = width//2
            hexagon_bottom = np.array([(0,0),(width//4,half),(width//4*3,half),(width,0)], np.int32)
            hexagon_top = np.array([(0,width), (width//4,half), (width//4*3,half), (width,width)],np.int32)
            cv.fillConvexPoly(b_img,hexagon_bottom,bgr_color,1)
            if feet_mod >= 2:
                cv.polylines(b_img,[hexagon_top],True,(0,0,0),2)
        else:
            return 'Invalid base shape. Choose square, hexagon or circle.'

        # enumerate
        if self.enumerate and creature.name in self.creature_counter:
            #print(creature.name, self.creature_counter[creature.name])
            text = str(self.creature_counter[creature.name])
            textsize = cv.getTextSize(text, self.font, enum_size, enum_width)[0]
            x_margin = b_img.shape[1] - textsize[0]
            y_margin = b_img.shape[0] - textsize[1]

            # Number color
            if creature.color ==  'ffffff':
                enum_color = (0, 0, 0)
            else:
                enum_color = (255, 255, 255)

            textX = np.floor_divide(x_margin, 2)
            textY = np.floor_divide(demi_base + textsize[1], 2)
            cv.putText(b_img, text, (textX, textY), self.font, enum_size, enum_color, enum_width, cv.LINE_AA)

            self.creature_counter[creature.name] -= 1

        ## construct full miniature
        img = np.concatenate((m_img, n_img, b_img), axis=0)
        # m_img_flipped = np.flip(m_img, 0)

        nb_flipped = np.rot90(np.concatenate((n_img,b_img), axis=0), 2)
        img = np.concatenate((nb_flipped, m_img_flipped, img), axis=0)

        ## Save image (not needed; only for debug/dev)
        # RGB_img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        # im_pil = Image.fromarray(RGB_img)
        # im_pil.save(self.save_dir + creature.name + ".png", dpi=(25.4 * self.dpmm, 25.4 * self.dpmm))

        return img

    def build_sheets(self,minis):
        M = BinManager(self.canvas[0], self.canvas[1], pack_algo='guillotine', heuristic='best_shortside',
                                    wastemap=True, rotation=True)
        its = {}
        item_id = 0
        for m in minis:
            its[item_id] = m
            item = Item(m.shape[1], m.shape[0], item_id)
            M.add_items(item)
            item_id += 1

        M.execute()

        result = M.bins

        sheets = []
        for r in result:
            img = np.zeros((int(self.canvas[1]), int(self.canvas[0]), 3), np.uint8) + 255
            for it in r.items:
                #print(it)
                x = int(it.x)
                y = int(it.y)
                w = int(it.width)
                h = int(it.height)
                it_id = int(it.item_id)
                m_img = its[it_id]
                test = m_img
                if w > h:  # rotated
                    m_img = np.rot90(m_img, axes=(1, 0))
                shape = m_img.shape
                #print('x',x,'y',y,'shape',m_img.shape)
                img[y:y + shape[0], x:x + shape[1], :] = m_img
            sheets.append(img)

        return sheets

    def show_sheets(self, sheets):
        sheet_nr = 1
        for sheet in sheets:
            RGB_img = cv.cvtColor(sheet, cv.COLOR_BGR2RGB)
            img_small =  cv.resize(sheet, (0,0), fx=.4, fy=.4)
            cv.imshow('Img',img_small)
            cv.waitKey(0)

    def save_and_zip(self, sheets):
        sheet_nr = 1
        sheet_fns = []
        for sheet in sheets:
            RGB_img = cv.cvtColor(sheet, cv.COLOR_BGR2RGB)
            im_pil = Image.fromarray(RGB_img)
            if not os.path.isdir(self.user_dir+ '/sheets'):
                os.makedirs(self.user_dir+ '/sheets')
            sheet_fn = self.user_dir + '/sheets/sheet_' + str(sheet_nr) + '.png'
            im_pil.save(sheet_fn, dpi=(25.4 * self.dpmm, 25.4 * self.dpmm))
            sheet_fns.append(sheet_fn)
            sheet_nr += 1
        self.zip_fn = self.file_name_body+'_minis.zip' # for serving
        zip_fn = self.user_dir+'/'+self.file_name_body+'_minis'
        shutil.make_archive(zip_fn, 'zip', self.user_dir+ '/sheets')
        # delete sheets
        for sheet_fn in sheet_fns:
            try:
                if os.path.isfile(sheet_fn):
                    os.unlink(sheet_fn)
            except Exception as e:
                print(e)

        return zip_fn+'.zip'
