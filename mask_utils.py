import numpy as np
from PIL import Image
from typing import List, Tuple

@staticmethod
def _string2rle(rle_str: str) -> List[int]:
    p = 0
    cnts = []
    while p < len(rle_str) and rle_str[p]:
        x = 0
        k = 0
        more = 1
        while more:
            c = ord(rle_str[p]) - 48
            x |= (c & 0x1f) << 5 * k
            more = c & 0x20
            p += 1
            k += 1
            if not more and (c & 0x10):
                x |= -1 << 5 * k
        if len(cnts) > 2:
            x += cnts[len(cnts) - 2]
        cnts.append(x)
    return cnts

@staticmethod
def _rle2mask(cnts: List[int], size: Tuple[int, int], label=1):
    img = np.zeros(size, dtype=np.uint8)
    ps = 0
    for i in range(0, len(cnts), 2):
        ps += cnts[i]
        for j in range(cnts[i + 1]):
            x = (ps + j) % size[1]
            y = (ps + j) // size[1]
            if y < size[0] and x < size[1]:
                img[y, x] = label
            else:
                break
        ps += cnts[i + 1]
    return img

def _rle2rgba(self, mask_obj) -> Image.Image:
    """
    Convert the compressed RLE string of mask object to png image object.
    :param mask_obj: The :class:`Mask <dds_cloudapi_sdk.tasks.ivp.IVPObjectMask>` object detected by this task
    """
    # convert rle counts to mask array
    rle = self.string2rle(mask_obj.counts)
    mask_array = self.rle2mask(rle, mask_obj.size)
    # convert the array to a 4-channel RGBA image
    mask_alpha = np.where(mask_array == 1, 255, 0).astype(np.uint8)
    mask_rgba = np.stack((255 * np.ones_like(mask_alpha),
                          255 * np.ones_like(mask_alpha),
                          255 * np.ones_like(mask_alpha),
                          mask_alpha),
                         axis=-1)
    image = Image.fromarray(mask_rgba, "RGBA")
    return image