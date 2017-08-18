from collections import namedtuple
import os
import textwrap
import time

from PIL import Image, ImageDraw, ImageFont
import requests

ASSET_DIR = 'assets'
DEFAULT_WIDTH = 600
DEFAULT_HEIGHT = 150
DEFAULT_CANVAS_SIZE = (DEFAULT_WIDTH, DEFAULT_HEIGHT)
DEFAULT_OUTPUT_FILE = 'out.png'
RESIZE_PERCENTAGE = 0.8
DEFAULT_TOP_MARGIN = int(((1 - 0.8) * DEFAULT_HEIGHT) / 2)
IMAGES = 'images'
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
WHITE_TRANSPARENT_OVERLAY = (255, 255, 255, 178)
TEXT_FONT_TYPE = os.path.join(ASSET_DIR, 'SourceSansPro-Regular.otf')
TEXT_PADDING_HOR = 10
Y_TEXT_START = 20

# adjust CHARS_PER_LINE if you change TEXT_SIZE
TEXT_SIZE = 24
CHARS_PER_LINE = 30

Font = namedtuple('Font', 'ttf text color size offset')
ImageDetails = namedtuple('Image', 'left top size')


class Banner:
    def __init__(self, size=DEFAULT_CANVAS_SIZE,
                 bgcolor=WHITE, output_file=DEFAULT_OUTPUT_FILE):
        '''Creating a new canvas'''
        self.size = size
        self.width = size[0]
        self.height = size[1]
        self.bgcolor = bgcolor
        self.output_file = self._create_uniq_file_name(output_file)
        self.image = Image.new('RGBA', self.size, self.bgcolor)
        self.image_coords = []

    def _create_uniq_file_name(self, outfile):
        fname, ext = os.path.splitext(outfile)
        tstamp = str(time.time()).replace('.', '_')
        uniq_fname = '{}_{}{}'.format(fname, tstamp, ext)
        return os.path.join(IMAGES, uniq_fname)

    def _image_gt_canvas_size(self, img):
        return img.size[0] > self.image.size[0] or \
               img.size[1] > self.image.size[1]

    def add_image(self, image, resize=False,
                  top=DEFAULT_TOP_MARGIN, left=0, right=False):
        '''Adds (pastes) image on canvas
           If right is given calculate left, else take left
           Returns added img size'''
        img = Image.open(image)

        if resize or self._image_gt_canvas_size(img):
            size = self.height * RESIZE_PERCENTAGE
            img.thumbnail((size, size), Image.ANTIALIAS)

        if right:
            left = self.image.size[0] - img.size[0]

        offset = (left, top)
        self.image.paste(img.convert('RGBA'), offset, mask=img.convert('RGBA'))

        img_details = ImageDetails(left=left, top=top, size=img.size)
        self.image_coords.append(img_details)

    def add_text(self, font):
        '''Adds text on a given image object'''
        draw = ImageDraw.Draw(self.image)
        pillow_font = ImageFont.truetype(font.ttf, font.size)

        # from https://stackoverflow.com/a/7698300
        # if only 1 image use the extra space for text
        single_image = len(self.image_coords) == 1
        text_width = CHARS_PER_LINE * 1.4 if single_image else CHARS_PER_LINE

        lines = textwrap.wrap(font.text, width=text_width)

        if font.offset:
            x_text, y_text = font.offset
        else:
            # if no offset given put text alongside first image
            left_image_px = min(img.left + img.size[0]
                                for img in self.image_coords)

            x_text = left_image_px + TEXT_PADDING_HOR

            # if <= 2 lines center them more vertically
            y_text = Y_TEXT_START * 2 if len(lines) < 3 else Y_TEXT_START

        for line in lines:
            _, height = pillow_font.getsize(line)
            draw.text((x_text, y_text), line, font.color, font=pillow_font)
            y_text += height

    def add_background(self, image, resize=False):
        img = Image.open(image).convert('RGBA')

        overlay = Image.new('RGBA', img.size, WHITE_TRANSPARENT_OVERLAY)
        bg_img = Image.alpha_composite(img, overlay)

        if resize:
            bg_size = (self.width * RESIZE_PERCENTAGE, self.height)
            bg_img.thumbnail(bg_size, Image.ANTIALIAS)
            left = self.width - bg_img.size[0]
            self.image.paste(bg_img, (left, 0))
        else:
            self.image.paste(bg_img.resize(DEFAULT_CANVAS_SIZE,
                                           Image.ANTIALIAS), (0, 0))

    def save_image(self):
        self.image.save(self.output_file)


def _download_image(from_url, to_file, chunk_size=2000):
    r = requests.get(from_url, stream=True)

    with open(to_file, 'wb') as fd:
        for chunk in r.iter_content(chunk_size):
            fd.write(chunk)


def get_image(image_url):
    basename = os.path.basename(image_url)
    local_image = os.path.join(IMAGES, basename)

    if not os.path.isfile(local_image):
        _download_image(image_url, local_image)

    return local_image


def generate_banner(img_banner):
    image1 = img_banner.image1
    image2 = get_image(img_banner.image2)
    text = img_banner.text

    banner = Banner()

    if img_banner.background:
        banner.add_background(image2)
    else:
        banner.add_image(image2, resize=True, right=True)

    banner.add_image(image1)

    font = Font(ttf=TEXT_FONT_TYPE,
                text=text,
                color=BLACK,
                size=TEXT_SIZE,
                offset=None)

    banner.add_text(font)

    banner.save_image()

    return banner.output_file
