import numpy as np

def mask_to_rle(img, encode=False):
    """
    img: numpy array, 1 - mask, 0 - background
    Returns run length as string formatted
    """
    pixels = img.flatten()
    pixels = np.concatenate([[0], pixels, [0]])
    # runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
    runs = np.where(pixels[1:] != pixels[:-1])[0]
    runs[1:] -= runs[:-1]
    counts = [int(x) for x in runs]
    if encode:
        return rle_to_string(counts)
    return counts


def rle_to_array(cnts, size, label=1):
    if isinstance(cnts, str):
        cnts = rle_fr_string(cnts)
    img = np.zeros(size, dtype=np.uint8)
    ps = 0
    for i in range(0, len(cnts)):
        if i & 1 == 0:
            ps += cnts[i]
            continue
        img[ps:ps + cnts[i]] = label
        ps += cnts[i]
    return img


def rle_to_string(cnts):
    # Similar to LEB128 but using 6 bits/char and ascii chars 48-111.
    m = len(cnts)
    p = 0
    s = [''] * (m * 6)

    for i in range(m):
        x = cnts[i]
        if i > 2:
            x -= cnts[i - 2]
        more = True

        while more:
            c = x & 0x1f
            x >>= 5
            more = x != -1 if (c & 0x10) else (x != 0)
            if more:
                c |= 0x20
            c += 48
            s[p] = chr(c)
            p += 1
    return ''.join(s)


def rle_fr_string(s):
    p = 0
    cnts = []

    while p < len(s) and s[p]:
        x = 0
        k = 0
        more = 1

        while more:
            c = ord(s[p]) - 48
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
