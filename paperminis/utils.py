import json
from fractions import Fraction
from functools import lru_cache
from urllib.request import Request, urlopen

import cv2 as cv
import numpy as np
from fake_useragent import UserAgent

from paperminis.models import Creature


# Observe this, in case this breaks things. This cache gets cleared when Minibuilder() gets evoked.
# This is here to stop spamming image sources
# Maybe replace with proper Redis cache at some point
@lru_cache(maxsize=64)
def download_image(url):
    """Download an image from an URL. Returns a bytearray. Also caches"""
    header = {'User-Agent': str(UserAgent().chrome)}
    try:
        req = Request(url, headers=header)
        with urlopen(req) as resp:
            arr = np.asarray(bytearray(resp.read()), dtype=np.uint8)
            m_img = cv.imdecode(arr, -1)  # Load it "as it is"
            return m_img
    except:
        return 'Image could not be found or loaded.'


def handle_json(f, user):
    """Load and process .json file.
    This version will update creatures if the json has more/different information.
    A creature is uniquely identified by the tuple (name, img_url).
    The update is still kind of slow for large files, but I can't see a better way to do it currently."""

    try:
        data = json.loads(f['file'].read().decode('utf-8'))
    except:
        return -1

    current = Creature.objects.filter(owner=user)
    current_name_url = [(x.name, x.img_url) for x in current]
    current_full = [(x.name, x.img_url, x.size) for x in current]
    size_map = {v: k for k, v in dict(Creature.CREATURE_SIZE_CHOICES).items()}
    skip = 0
    obj_list = []
    for k, i in data.items():
        # mandatory fields
        try:
            name = i['name']
            img_url = i['img_url']
            name_url = (name, img_url)
        except:
            skip += 1
            continue

        # fix illegal size (default to medium)
        try:
            short_size = size_map[i['creature_size']]
        except:
            short_size = Creature.MEDIUM

        # check if unique
        if name_url in current_name_url:
            full_tup = (name, img_url, short_size, cr, short_type)
            if full_tup in current_full:
                # excact duplicate
                skip += 1
                continue
            else:
                # updated attributes
                # this is kinda slow :(
                Creature.objects.filter(owner=user, name=name, img_url=img_url).update(size=short_size)
                current_full.append(full_tup)
                continue

        current_name_url.append(name_url)

        # if everything is ok, generate the object and store it
        obj = Creature(owner=user, name=i['name'], size=short_size, img_url=i['img_url'])
        obj_list.append(obj)

    if len(obj_list) > 0:
        # MUCH faster than one query per entry!
        Creature.objects.bulk_create(obj_list)
    return skip
