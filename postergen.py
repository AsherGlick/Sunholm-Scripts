# This script generates a balanced poster image from a given source.
# In order to create a good poster take an image, crop out a square, add a
# new layer on top of solid white, take a feathered eraser tool ~33% the size
# of the  screen and begin erasing parts of the white making sure the tool's
# border never touches the edge of the screen. Then export the image to a png
# and run this script on the png to generate a properly sized and color
# balanced png image that can be used for a poster.
# postergen.py input_image.png output_image.png

import math
import sys
from PIL import Image  # type: ignore
from typing import List, Tuple

total_shares: float = 0
for i in range(0, 237):
    total_shares += 1

for i in range(237, 254):
    total_shares += math.pow(1.14, i - 237)

shares = []

for i in range(0, 237):
    shares.append(1 / total_shares)
for i in range(237, 254):
    shares.append(math.pow(1.14, i - 237) / total_shares)

share_threshold: List[float] = [0]

for i in range(0, 254):
    share_threshold.append(share_threshold[-1] + shares[i])

im = Image.open(sys.argv[1])


def get_luma(red: int, green: int, blue: int) -> float:
    return (red * 0.3 + green * 0.59 + blue * 0.11)


pixel_values: List[Tuple[float, int, int]] = []

white_pixels: List[Tuple[int, int]] = []

im.putalpha(255)

pixels = im.load()
width, height = im.size

for x in range(width):
    for y in range(height):
        color = pixels[x, y]
        luma = get_luma(color[0], color[1], color[2])
        if luma < 255.0:
            pixel_values.append((luma, x, y))
        else:
            white_pixels.append((x, y))

pixel_values.sort(key=lambda x: x[0])

pixel_share_threshold = []
for i in range(254):
    pixel_share_threshold.append(math.floor(share_threshold[i] * len(pixel_values)))

pixel_share_threshold.append(len(pixel_values))

alpha_index = 0

for i, pixel in enumerate(pixel_values):
    luma = pixel[0]
    x = pixel[1]
    y = pixel[2]

    if i > pixel_share_threshold[alpha_index]:
        alpha_index += 1

    alpha = 255 - alpha_index

    pixels[x, y] = (0, 0, 0, alpha)

for white_pixel in white_pixels:
    x = white_pixel[0]
    y = white_pixel[1]
    pixels[x, y] = (0, 0, 0, 0)

# Save the modified image
im.resize((256, 256)).save(sys.argv[2])
