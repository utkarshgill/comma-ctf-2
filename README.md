# prius.jpg

Second challenge from the comma.ai/tinycorp CTF (originally for NeurIPS). One image, one flag.

The EXIF has a hint:

```
$ exiftool prius.jpg
ExifTool Version Number         : 13.36
File Name                       : prius.jpg
File Size                       : 1019 kB
File Type                       : JPEG
JFIF Version                    : 1.01
Exif Byte Order                 : Big-endian (Motorola, MM)
X Resolution                    : 1
Y Resolution                    : 1
Resolution Unit                 : None
Y Cb Cr Positioning             : Centered
Exif Version                    : 0232
Components Configuration        : Y, Cb, Cr, -
User Comment                    : Congratulations on finding this secret message.
                                  This CTF is retired. However there is still one
                                  flag to be found in this image. Use this link to
                                  submit it: https://forms.gle/LeytrGCMoicWiyvb8.
                                  Hint: Im a number, I should not exist, yet Im
                                  here. Good luck!
Flashpix Version                : 0100
Color Space                     : Uncalibrated
Image Width                     : 3840
Image Height                    : 2060
Encoding Process                : Baseline DCT, Huffman coding
Bits Per Sample                 : 8
Color Components                : 1
Image Size                      : 3840x2060
Megapixels                      : 7.9
```

> Im a number, I should not exist, yet Im here.

## What didnt work

I spent a few weeks on this before figuring it out. Most of that time I was fixated on the wrong reading of the hint.

"Should not exist" made me think of imaginary numbers. `i = sqrt(-1)`. That was wrong.

I also noticed the SOF marker has Component ID = 0, which is invalid per the JPEG spec. The Color Space field is 65535 (Uncalibrated). There are duplicate JFIF headers. Each of these is a "number that shouldnt exist" in some sense. None of them were the flag.

I ran binwalk, strings, jsteg, outguess, steghide, bit plane analysis, FFT watermarks, pixel LSB, DCT coefficient LSB, F5, Huffman table analysis, EXIF orphan byte mapping. Searched the raw byte stream for flag formats. Tried old flags from the first CTF as decryption keys. Nothing.

I kept reaching for tools instead of thinking about the format.

## How JPEGs actually work

A JPEG doesnt store pixels. It stores frequency coefficients. The image gets split into 8x8 blocks, each block gets a Discrete Cosine Transform, and the resulting values get divided by a quantization table and rounded to integers. Thats what lives in the file.

When you open the image, your viewer does the reverse: multiply by the quantization table, inverse DCT, get pixels back.

The key insight is that these coefficients arent arbitrary. They are derived from pixel values through a fixed transform, and pixel values in an 8-bit image are bounded to 0-255. So every coefficient has a theoretical maximum. You cant just put any number in there and have it correspond to a real image.

Well, you can. The decoder will happily accept it. It just multiplies, runs the inverse DCT, and clips any out-of-range pixels to 0-255. It never validates whether the coefficient was actually achievable. The image displays fine. But mathematically, the number is impossible.

## The bound

For the DC coefficient (position 0,0), the most extreme input is all pixels at 255 or all at 0. After level shifting by -128, the DCT gives a max DC of 1016. This images quantization table divides DC by 2, so the max quantized value is floor(1016/2) = 508.

This isnt statistical or approximate. Its arithmetic. 508 is the ceiling.

## The flag

I computed the theoretical maximum for all 64 coefficient positions and scanned every coefficient in the image. 123,840 blocks, 64 positions each.

One violation. Block (37, 111), position (0,0). Value: **509**. Max possible: 508.

Someone edited the file and set that one coefficient to a value no encoder could produce.

```
509
```

`prius_flagged.jpg` marks the block location with a red square. It's just a normal looking patch of the photo, nothing to see with your eyes.
