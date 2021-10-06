# ARTCONTRACTS LICENSE:
### This software is a part of, or a derived work based on, the ArtContracts project (https://artcontracts.net) by MathMakesArt (https://mathmakes.art)
### Depending on what software you're using, this code may have been integrated into a larger project with more authors.
### The ArtContracts code is free and open-source. You are free to use it however you want, including for commercial purposes.
### All distributions and derived works MUST include a copy of this text, including author information.
###   If a derived work contains any sort of licensing information, you must include an additional copy of this text within the license file of your software.
### Derived works may implement this code, but you are not permitted to sell this software itself (e.g. you may not charge money for mere access to this software).
## VERSION INFORMATION
### This file comes from version 1.4.5, finalized on 2021/10/05
### The contents of this file (excluding comments) were last edited on 2021/07/21
## AUTHOR INFORMATION:
### GitHub:           @MathMakesArt
### Twitter:          @MathMakesArt
### Website:          https://mathmakes.art
### Email:            mathmakesart@gmail.com
### Tezos address:    tz1gsrd3CfZv4BfPnYKq5pKpHGFVdtGCgd71 (mathmakesart.tez)

# TODO:
# 1. Enable 8-bits-per-channel as a valid specification (and skip any unnecessary actions accordingly)

# Library Imports
import numpy
import PIL

# USER INPUT
# ENABLE_ALPHA_CHANNEL: Boolean describing whether to use transparency
# (Pixels are represented by 3 channels when False, 4 channels when True)
ENABLE_ALPHA_CHANNEL = False
# BITS_PER_CHANNEL: An integer from 1 to 8 describing maximum precision of Palette
BITS_PER_CHANNEL = 4
# ENABLE_CUSTOM_PALETTE
#  - When FALSE, the palette will be determined via standard linear interpolation across the RGB color cube
#  - When TRUE, more complex (asymmetric) color schemes can be supported, but they must be manually defined
# WARNING: Not yet implemented
# TODO: Implement this
ENABLE_CUSTOM_PALETTE = False

# CONSOLE OUTPUT CONTROLS
PRINT_MAX_CHARS = 65536 # This keeps console output size low, and has the effect of ensuring maximum printed hex output size is 32KB
FLAG_PRINT_TEXTURE = True
FLAG_PRINT_PALETTE = False
FLAG_PRINT_STANDARD = True
FLAG_PRINT_8BIT = False

# TODO: Only add these variables when the necessary structural prerequisites have been implemented
# HORIZONTAL_FIRST: Boolean. When True, the image is interpreted row-by-row. When False, column-by-column.
# FROM_LEFT: Boolean. When True, the image is interpreted from left-to-right. When False, right-to-left.
# FROM_TOP: Boolean. When True, the image is interpreted from top-to-bottom. When False, bottom-to-top.

# SCALE_X: Integer multiple for scaling in X direction
SCALE_X = 1
# SCALE_Y: Integer multiple for scaling in Y direction
SCALE_Y = 1
# TILE_X: Integer multiple for tiling in X direction
TILE_X = 1
# TILE_Y: Integer multiple for tiling in Y direction
TILE_Y = 1

# FILE NAMES AND PATHS
INPUT_FOLDER = "input/"
INPUT_FILENAME = "input2-128.png"
INPUT_FILENAME_LOOKUP_BITS = "lookup-bits.csv"
INPUT_FILENAME_LOOKUP_BINARY = "lookup-binary.csv"
OUTPUT_FOLDER = "output/"
DEFAULT_SAVE_NAME_DIGITS = 6
DEFAULT_SAVE_NAME_SUFFIX = ""
DEFAULT_SAVE_FORMAT = ".png"
FRAMES_FOLDER = "frames/"
DEFAULT_FRAME_NAME_DIGITS = 6
DEFAULT_FRAME_NAME_SUFFIX = ""
DEFAULT_FRAME_FORMAT = ".png"
# NUMPY IMAGE METADATA
DEFAULT_INT_DATATYPE = numpy.int32
DEFAULT_FLOAT_DATATYPE = numpy.float32
DEFAULT_IMAGE_SAVE_DATATYPE = numpy.uint8
# PIL METADATA
DEFAULT_PIL_RESIZE_RESAMPLE_MODE = PIL.Image.NEAREST

# CONTROL VALUES
STANDARD_BITS_PER_CHANNEL = 8

# COMPUTED VALUES
# Number of channels
NUM_CHANNELS = 3
if ENABLE_ALPHA_CHANNEL:
    NUM_CHANNELS = 4
# Updating BITS_PER_PIXEL
BITS_PER_PIXEL = NUM_CHANNELS * BITS_PER_CHANNEL
# Coefficients for encoding/decoding each channel
COEFF_R = 0
COEFF_G = 0
COEFF_B = 0
COEFF_A = 0
if ENABLE_ALPHA_CHANNEL:
    COEFF_A = 1
    COEFF_B = 2 ** BITS_PER_CHANNEL
    COEFF_G = 2 ** (2 * BITS_PER_CHANNEL)
    COEFF_R = 2 ** (3 * BITS_PER_CHANNEL)
else:
    COEFF_B = 1
    COEFF_G = 2 ** BITS_PER_CHANNEL
    COEFF_R = 2 ** (2 * BITS_PER_CHANNEL)
