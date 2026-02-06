"""
comma.ai/tinycorp NeurIPS CTF — prius.jpg
Flag: 509

The EXIF User Comment contains a riddle:
  "I'm a number, I should not exist, yet I'm here"

The flag is a single DCT coefficient that violates a hard mathematical
invariant of the JPEG format.  No valid encoder can produce it — it was
injected directly into the file.

This script proves it in three steps:
  1. Compute the theoretical maximum for every quantized DCT coefficient
     position in an 8-bit grayscale JPEG with this image's quantization table.
  2. Scan every coefficient in the image.
  3. Report any that exceed their theoretical bound.

Only one does: block (37, 111), position (0, 0), value 509.
The proven maximum for that position is 508.  509 cannot exist — yet it's here.
"""

import numpy as np
from scipy.fft import dct as dct_func
import jpegio

# ---------- load image ----------
jpg = jpegio.read("prius.jpg")
coeffs = jpg.coef_arrays[0]
qt = jpg.quant_tables[0]

print(f"Image DCT shape: {coeffs.shape}")
print(f"Blocks: {coeffs.shape[0]//8} rows x {coeffs.shape[1]//8} cols\n")

# ---------- step 1: theoretical bounds ----------
# For each of the 64 positions in an 8x8 block, find the maximum
# absolute quantized value any valid 8-bit input can produce.
#
# Method: build the 2-D DCT basis function for position (r, c),
# then set each pixel to 0 or 255 depending on the sign of the
# basis at that pixel (this maximises the dot product).
# Level-shift by 128, forward-DCT, divide by the quantization
# step, and floor.

basis_1d = dct_func(np.eye(8), type=2, norm="ortho", axis=0)  # 8x8
theo_max = np.zeros((8, 8), dtype=int)

for r in range(8):
    for c in range(8):
        # 2-D basis: outer product of 1-D bases
        basis_2d = np.outer(basis_1d[r], basis_1d[c])
        # optimal pixels: 255 where basis > 0, 0 where basis < 0
        block = np.where(basis_2d > 0, 255.0, 0.0) - 128.0
        dct_block = dct_func(dct_func(block, type=2, norm="ortho", axis=0),
                             type=2, norm="ortho", axis=1)
        theo_max[r, c] = int(np.floor(abs(dct_block[r, c]) / qt[r, c]))

print("Theoretical max quantized magnitude per position:")
print(theo_max, "\n")

# ---------- step 2: scan for violations ----------
h_blocks, w_blocks = coeffs.shape[0] // 8, coeffs.shape[1] // 8
violations = []

for br in range(h_blocks):
    for bc in range(w_blocks):
        block = coeffs[br * 8:(br + 1) * 8, bc * 8:(bc + 1) * 8]
        for r in range(8):
            for c in range(8):
                if abs(block[r, c]) > theo_max[r, c]:
                    violations.append((br, bc, r, c,
                                       int(block[r, c]),
                                       int(theo_max[r, c])))

# ---------- step 3: report ----------
print(f"Violations found: {len(violations)}\n")
for br, bc, r, c, val, bound in violations:
    print(f"  block ({br},{bc})  pos ({r},{c})  value = {val}  "
          f"(max possible = {bound})")

if violations:
    flag = abs(violations[0][4])
    print(f"\nFlag: {flag}")
