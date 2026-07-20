#!/usr/bin/env python3
"""
prep_photo.py <source-photo.jpg>

Turns a normal photo into a clean, high-contrast grayscale PNG that
converts nicely to ASCII art:
  1. Remove the background (rembg) so only the subject remains.
  2. CLAHE contrast boost so a flatly-lit face gets real highlights/shadows.
  3. Composite onto pure white so the background maps to "blank" in the
     ASCII ramp.

Output: source-prepped.png (next to the input file)
"""
import sys
import os
import numpy as np
import cv2
from PIL import Image


def prep(path: str) -> str:
    from rembg import remove  # imported lazily; heavy dependency

    with open(path, "rb") as f:
        input_bytes = f.read()

    # 1. Remove background -> RGBA with transparent bg
    result_bytes = remove(input_bytes)
    rgba = Image.open(__import__("io").BytesIO(result_bytes)).convert("RGBA")

    # 2. Composite onto white
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, rgba).convert("RGB")

    # 3. Grayscale + CLAHE contrast boost
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    boosted = clahe.apply(gray)

    out_path = os.path.splitext(path)[0] + "-prepped.png"
    Image.fromarray(boosted).save(out_path)
    print(f"wrote {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python prep_photo.py <source-photo.jpg>")
        sys.exit(1)
    prep(sys.argv[1])
