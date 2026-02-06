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

I also noticed the [SOF marker](https://en.wikipedia.org/wiki/JPEG#Syntax_and_structure) has Component ID = 0, which is invalid per the JPEG spec. The Color Space field is 65535 (Uncalibrated). There are duplicate [JFIF](https://en.wikipedia.org/wiki/JPEG_File_Interchange_Format) headers. Each of these is a "number that shouldnt exist" in some sense. None of them were the flag.

I ran binwalk, strings, [jsteg](https://github.com/lukechampine/jsteg), outguess, steghide, bit plane analysis, [FFT](https://en.wikipedia.org/wiki/Fast_Fourier_transform) watermarks, pixel [LSB](https://en.wikipedia.org/wiki/Bit_numbering#Least_significant_bit), DCT coefficient LSB, [F5](https://en.wikipedia.org/wiki/F5_algorithm), [Huffman table](https://en.wikipedia.org/wiki/Huffman_coding) analysis, [EXIF](https://en.wikipedia.org/wiki/Exif) orphan byte mapping. Searched the raw byte stream for flag formats. Tried old flags from the first CTF as decryption keys. Nothing.

I kept reaching for tools instead of thinking about the format.

## How JPEGs actually work

A JPEG doesnt store pixels. It stores frequency coefficients. The image gets split into 8x8 blocks, and each block gets a 2D [Discrete Cosine Transform](https://en.wikipedia.org/wiki/Discrete_cosine_transform):

$$F(u,v) = \frac{1}{4} C(u) C(v) \sum_{x=0}^{7} \sum_{y=0}^{7} f(x,y) \cos\frac{(2x+1)u\pi}{16} \cos\frac{(2y+1)v\pi}{16}$$

where $C(0) = \frac{1}{\sqrt{2}}$ and $C(k) = 1$ for $k > 0$. In practice `scipy.fft.dct` with `norm='ortho'` handles all of this.

This gives you 64 coefficients per block. The one at position $(0,0)$ is the DC coefficient. For DC all the cosine terms are 1, so it simplifies to $F(0,0) = \frac{1}{8}\sum f(x,y)$ — just the average brightness of the block scaled by 8. The other 63 are AC coefficients (the names come from electrical engineering — Direct Current for the constant component, Alternating Current for the oscillating ones), representing progressively higher frequency detail. Low frequency stuff like gradients lives near the top-left, fine texture and edges live near the bottom-right.

These coefficients then get divided by a [quantization table](https://en.wikipedia.org/wiki/Quantization_(image_processing)) $Q$ and rounded:

$$F_q(u,v) = \text{round}\left(\frac{F(u,v)}{Q(u,v)}\right)$$

Thats what the file stores. When you open the image, the decoder multiplies back by $Q$, runs the inverse DCT, and gets pixels. The quantization step is where information is lost — thats the "lossy" in lossy compression.

The key insight is that these quantized coefficients arent arbitrary. They are derived from pixel values $f(x,y) \in [0, 255]$ through a fixed transform. So every coefficient has a theoretical maximum determined by the math. You cant just put any number in there and have it correspond to a real image.

Well, you can. The decoder will happily accept it — it just multiplies, runs the inverse DCT, and clips any out-of-range pixels to 0-255. It never checks whether the coefficient was actually achievable. The image displays fine. But mathematically, the number is impossible.

## The bound

For the DC coefficient, plugging into the formula above with $u = v = 0$:

$$F(0,0) = \frac{1}{4} \cdot \frac{1}{\sqrt{2}} \cdot \frac{1}{\sqrt{2}} \sum_{x=0}^{7} \sum_{y=0}^{7} f(x,y) = \frac{1}{8} \sum_{x=0}^{7} \sum_{y=0}^{7} f(x,y)$$

Before the DCT, pixel values get [level-shifted](https://en.wikipedia.org/wiki/JPEG#Encoding) by 128, so $f(x,y) \in [-128, 127]$. The most extreme case is all pixels at 255 (shifted to 127):

$$F(0,0)_{\max} = \frac{1}{8} \cdot 64 \cdot 127 = 1016$$

This images quantization table has $Q(0,0) = 2$, so:

$$F_q(0,0)_{\max} = \left\lfloor \frac{1016}{2} \right\rfloor = 508$$

This isnt statistical or approximate. Its arithmetic. 508 is the ceiling.

## The flag

I computed the theoretical maximum for all 64 coefficient positions and scanned every coefficient in the image. 123,840 blocks, 64 positions each.

One violation. Block (37, 111), position (0,0). Value: **509**. Max possible: 508.

Someone edited the file and set that one coefficient to a value no encoder could produce.

```
509
```

`prius_flagged.jpg` marks the block location with a red square. It's just a normal looking patch of the photo, nothing to see with your eyes.
