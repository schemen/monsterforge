from functools import lru_cache
from urllib.request import Request, urlopen

import cv2 as cv
import numpy as np
from fake_useragent import UserAgent


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
