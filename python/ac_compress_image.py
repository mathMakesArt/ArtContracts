# ARTCONTRACTS LICENSE:
### This software is a part of, or a derived work based on, the ArtContracts project (https://artcontracts.net) by MathMakesArt (https://mathmakes.art)
### Depending on what software you're using, this code may have been integrated into a larger project with more authors.
### The ArtContracts code is free and open-source. You are free to use it however you want, including for commercial purposes.
### All distributions and derived works MUST include a copy of this text, including author information.
###   If a derived work contains any sort of licensing information, you must include an additional copy of this text within the license file of your software.
### Derived works may implement this code, but you are not permitted to sell this software itself (e.g. you may not charge money for mere access to this software).
## VERSION INFORMATION
### This file comes from version 1.4, finalized on 2021/07/21
## AUTHOR INFORMATION:
### GitHub:           @MathMakesArt
### Twitter:          @MathMakesArt
### Website:          https://mathmakes.art
### Email:            mathmakesart@gmail.com
### Tezos address:    tz1gsrd3CfZv4BfPnYKq5pKpHGFVdtGCgd71 (mathmakesart.tez)

# TODO:
# 1. Enable 8-bits-per-channel as a valid specification (and skip any unnecessary actions accordingly)
# 2. Consider splitting scaling into its own separate function

# Library Imports
import random
import timeit
from timeit import default_timer
import PIL
from PIL import Image
import numpy
from pathlib import Path
import matplotlib.pyplot as plt
import glob
from numba import jit
from numpy.lib.function_base import place

# Local Imports
import ac_settings as acs

def getSavePath(fileIndex, digits=acs.DEFAULT_SAVE_NAME_DIGITS, suffix=acs.DEFAULT_SAVE_NAME_SUFFIX,
                format=acs.DEFAULT_SAVE_FORMAT):
    return Path.cwd() / acs.OUTPUT_FOLDER / (str(fileIndex).zfill(digits) + suffix + format)

def getFramePath(fileIndex, digits=acs.DEFAULT_FRAME_NAME_DIGITS, suffix=acs.DEFAULT_FRAME_NAME_SUFFIX,
                format=acs.DEFAULT_FRAME_FORMAT):
    return Path.cwd() / acs.OUTPUT_FOLDER / acs.FRAMES_FOLDER / (str(fileIndex).zfill(digits) + suffix + format)


# Saves an image to the specified path
def saveImage(imageData, path):
    Image.fromarray(imageData.astype(acs.DEFAULT_IMAGE_SAVE_DATATYPE)).save(path)

# Saves an image to the specified path, with (integer) scaling
def saveImageResized(imageData, path, scaleX, scaleY):
    if (scaleX == 1) and (scaleY == 1):
        saveImage(imageData, path)
    else:
        newWidth = int(imageData.shape[1] * scaleX)
        newHeight = int(imageData.shape[0] * scaleY)
        Image.fromarray(imageData.astype(acs.DEFAULT_IMAGE_SAVE_DATATYPE)).resize(
            (newWidth, newHeight),
            resample=acs.DEFAULT_PIL_RESIZE_RESAMPLE_MODE
        ).save(path)

# Creates the folder(s) in which outputs will be saved
def makeDirectories():
    cwDir = Path.cwd()
    dirs = [cwDir / acs.OUTPUT_FOLDER,  # MAIN OUTPUT DIRECTORY
            cwDir / acs.OUTPUT_FOLDER / acs.FRAMES_FOLDER]  # FRAMES DIRECTORY
    for newDir in dirs:
        if not newDir.is_dir():
            newDir.mkdir()

@jit(nopython=True)
def makeBlankCanvas(imageData, val=255):
    imageData[:, :, :] = val
    return imageData

@jit(nopython=True)
def generateGridRatiosNumba(dim):
    startVal = 1 / (2 * dim)
    return numpy.arange(start=startVal, stop=1.0, step=(startVal * 2))

@jit(nopython=True)
def makeGradientNumba(imageData):
    imageShape = imageData.shape
    xVals = generateGridRatiosNumba(imageShape[1])
    yVals = generateGridRatiosNumba(imageShape[0])
    for y in range(imageShape[0]):
        for x in range(imageShape[1]):
            imageData[y, x, 0] = (xVals[x]) * 255
            imageData[y, x, 1] = (yVals[y]) * 255
            imageData[y, x, 2] = ((xVals[x] + yVals[y]) / 2) * 255
    return imageData

@jit(nopython=True)
def floydSteinberg(imageData, bitLookup, bitsPerChannel):
    imageFloat = imageData.copy().astype(acs.DEFAULT_FLOAT_DATATYPE)
    if bitsPerChannel >= acs.STANDARD_BITS_PER_CHANNEL:
        return imageFloat.astype(acs.DEFAULT_INT_DATATYPE)
    imageShape = imageFloat.shape
    for y in range(imageShape[0]):
        for x in range(imageShape[1]):
            for c in range(imageShape[2]):
                currentVal = acs.DEFAULT_INT_DATATYPE(imageFloat[y, x, c])
                # Ensure currentVal remains within [0, 255] boundary
                if currentVal > 255:
                    currentVal = 255
                elif currentVal < 0:
                    currentVal = 0
                # Compute current pixel error
                newVal = bitLookup[currentVal, bitsPerChannel]
                currentError = currentVal - newVal
                # Update current pixel value
                imageFloat[y, x, c] = newVal
                # Distribute current pixel error onto up to 4 neighboring (future) pixels
                if (x + 1) < imageShape[1]:
                    imageFloat[y, (x + 1), c] += (7 / 16) * currentError
                    if (y + 1) < imageShape[0]:
                        imageFloat[(y + 1), (x + 1), c] += (1 / 16) * currentError
                if (y + 1) < imageShape[0]:
                    imageFloat[(y + 1), x, c] += (5 / 16) * currentError
                    if x > 0:
                        imageFloat[(y + 1), (x - 1), c] += (3 / 16) * currentError
    return imageFloat.astype(acs.DEFAULT_INT_DATATYPE)


def wrapper():

    # VARIABLE INITIALIZATION
    saveCount = 0  # Used in filenames, always increment directly after calling saveImage

    # PREREQUISITE ACTIONS
    # Directory Creation
    makeDirectories()
    # Construct the path from which to load the bit lookup table
    inputPath = Path.cwd() / acs.INPUT_FOLDER / acs.INPUT_FILENAME_LOOKUP_BITS
    # Loads the lookup table for bit precision conversions
    lookupBits = numpy.genfromtxt(inputPath, delimiter=',', dtype=acs.DEFAULT_INT_DATATYPE)
    

    # Construct the path from which to load the binary conversion lookup table
    inputPath = Path.cwd() / acs.INPUT_FOLDER / acs.INPUT_FILENAME_LOOKUP_BINARY
    # Loads the lookup table for binary conversions
    lookupBinary = numpy.genfromtxt(inputPath, delimiter=',', dtype=acs.DEFAULT_INT_DATATYPE)
    # Gets the shape of the binary lookup table
    lookupBinaryShape = lookupBinary.shape
    # Construct the empty list which will hold the string form of the Binary lookup table
    lookupBinaryList = []
    # Fill the empty list (lookupBinaryList) with string versions of values from the Numpy array (lookupBinary)
    for n in list(range(lookupBinaryShape[0])):
        lookupBinaryList.append([])
        for b in list(range(lookupBinaryShape[1])):
            lookupBinaryList[-1].append(str(lookupBinary[n, b]).zfill(b))


    # Construct the path from which to load the input image
    inputPath = Path.cwd() / acs.INPUT_FOLDER / acs.INPUT_FILENAME
    # Load the input image, restricting the number of channels to NUM_CHANNELS from the settings
    numpyImage = numpy.asarray(Image.open(inputPath)).astype(acs.DEFAULT_INT_DATATYPE)[:, :, 0:acs.NUM_CHANNELS]

    #TODO: IF IMAGE HAS NO ALPHA CHANNEL BUT acs.ENABLE_ALPHA_CHANNEL is True, then ADD a 4th channel so as to not screw up future math
    numChannelsLoaded = numpyImage.shape[2]
    if numChannelsLoaded < acs.NUM_CHANNELS:
        alphaChannel = 255 * numpy.ones((numpyImage.shape[0], numpyImage.shape[1]), dtype=acs.DEFAULT_INT_DATATYPE)
        numpyImage = numpy.transpose(numpy.array((numpyImage[:,:,0], numpyImage[:,:,1], numpyImage[:,:,2], alphaChannel), dtype=acs.DEFAULT_INT_DATATYPE), (1, 2, 0))

    # Applies Floyd-Steinberg dithering to the new image
    numpyImage = floydSteinberg(numpyImage, lookupBits, acs.BITS_PER_CHANNEL)


    # BINARY AND HEXADECIMAL CONVERSIONS
    # Coefficients for conversion between 8-bit and N-bit color representations, where N = acs.BITS_PER_CHANNEL
    coefficientsTo8 = []
    for c in range(acs.NUM_CHANNELS):
        coefficientsTo8.append(((2 ** acs.STANDARD_BITS_PER_CHANNEL) ** (acs.NUM_CHANNELS - c - 1)) * (((2 ** acs.STANDARD_BITS_PER_CHANNEL) - 1) / ((2 ** acs.BITS_PER_CHANNEL) - 1)))
    print(coefficientsTo8)
    
    # Variables for Texture Contract Construction
    textureBin = ""
    textureBin8 = ""
    textureDec = ""
    textureDec8 = ""
    textureHex = ""
    textureHex8 = ""
    imageShape = numpyImage.shape

    # Assembles textureBin and textureBin8
    for y in range(imageShape[0]):
        for x in range(imageShape[1]):
            currentDecSum = 0 # Begins each pixel loop with currentDecSum reset to 0
            # Iterate through all channels (3 or 4 depending on alpha)
            for c in range(imageShape[2]):
                # Grabs the binary value associated with the current color channel of the current pixel
                currentBin = lookupBinaryList[numpyImage[y, x, c]][acs.BITS_PER_CHANNEL]
                textureBin += currentBin # Adds this binary value to the textureBin string
                # Computes the decimal version of this binary number and multiplies it by the corresponding channel coefficient for 8-bit-per-channel conversion
                currentDec = int(currentBin, 2) * coefficientsTo8[c]
                currentDecSum += currentDec # Adds this decimal value to the pixel's decimal sum
            currentBin8 = bin(round(currentDecSum))[2:].zfill(acs.STANDARD_BITS_PER_CHANNEL * acs.NUM_CHANNELS) # Converts the decimal sum to an 8-bit-per-channel binary representation
            textureBin8 += currentBin8 # Adds the 8-bit-per-channel binary value to the 8-bit binary texture string

    # Variables for Palette Contract Construction
    paletteBin = ""
    paletteBin8 = ""
    paletteDec = ""
    paletteDec8 = ""
    paletteHex = ""
    paletteHex8 = ""

    # If the custom palette is enabled, compute a full palette and output the palette string
    # NOTE: The existing code within this IF block is incorrect.
    # It was developed for NON-CUSTOM palettes, before it became apparent that non-custom palettes do not need a palette string.
    if acs.ENABLE_CUSTOM_PALETTE:
        # Maximum number of colors in a palette with acs.BITS_PER_PIXEL of storage per color
        maxNumColors = 2 ** (acs.BITS_PER_PIXEL)
        # Assembles paletteBin and paletteBin8
        for i in range(maxNumColors):
            currentDecSum = 0 # Begins each color loop with currentDecSum reset to 0
            # Grabs the binary value associated with the current color
            currentBin = str(bin(i))[2:].zfill(acs.BITS_PER_PIXEL)
            currentChannels = [currentBin[i:(i + acs.BITS_PER_CHANNEL)] for i in range(0, acs.BITS_PER_PIXEL, acs.BITS_PER_CHANNEL)]
            # Iterate through all channels (3 or 4 depending on alpha)
            for c in range(acs.NUM_CHANNELS):
                # Computes the decimal version of this binary number and multiplies it by the corresponding channel coefficient for 8-bit-per-channel conversion
                currentDec = int(currentChannels[c], 2) * coefficientsTo8[c]
                currentDecSum += currentDec # Adds this decimal value to the pixel's decimal sum
            currentBin8 = bin(round(currentDecSum))[2:].zfill(acs.STANDARD_BITS_PER_CHANNEL * acs.NUM_CHANNELS)  # Converts the decimal sum to an 8-bit-per-channel binary representation
            paletteBin += currentBin  # Adds the base binary value to the paletteBin string
            paletteBin8 += currentBin8 # Adds the 8-bit-per-channel binary value to the paletteBin8 string
    else:
        paletteBin = "0"
        paletteBin8 = "0"

    # Prepends a single "1" character into the palette and texture binary strings
    paletteBin = "1" + paletteBin
    textureBin = "1" + textureBin


    textureDec = int(textureBin, 2)
    textureDec8 = int(textureBin8, 2)
    paletteDec = int(paletteBin, 2)
    paletteDec8 = int(paletteBin8, 2)
    textureHex = hex(textureDec)[2:] # [2:] removes leading "0x"
    textureHex8 = hex(textureDec8)[2:] # [2:] removes leading "0x"
    paletteHex = hex(paletteDec)[2:] # [2:] removes leading "0x"
    paletteHex8 = hex(paletteDec8)[2:] # [2:] removes leading "0x"


    # Adds leading "0x" to the hexadecimal strings
    textureHex = "0x" + textureHex
    textureHex8 = "0x" + textureHex8
    paletteHex = "0x" + paletteHex
    paletteHex8 = "0x" + paletteHex8
    # Adds a trailing zero to any hex string with an odd number of characters
    if len(textureHex) % 2 == 1:
        textureHex += "0"
    if len(textureHex8) % 2 == 1:
        textureHex8 += "0"
    if len(paletteHex) % 2 == 1:
        paletteHex += "0"
    if len(paletteHex8) % 2 == 1:
        paletteHex8 += "0"


    # STRING PRINTING (For Development)
    if acs.FLAG_PRINT_STANDARD:
        print("VALUES AT USER-SPECIFIED BIT-PER-CHANNEL PRECISION")
        if acs.FLAG_PRINT_TEXTURE:
            print("TEXTURE (BINARY)")
            print(textureBin[0:acs.PRINT_MAX_CHARS])
            print("TEXTURE (DECIMAL)")
            print(str(textureDec)[0:acs.PRINT_MAX_CHARS])
            print("TEXTURE (HEXADECIMAL)")
            print(textureHex[0:acs.PRINT_MAX_CHARS])
            print()
            print()
        if acs.FLAG_PRINT_PALETTE and acs.ENABLE_CUSTOM_PALETTE:
            print("PALETTE (BINARY)")
            print(paletteBin[0:acs.PRINT_MAX_CHARS])
            print("PALETTE (DECIMAL)")
            print(str(paletteDec)[0:acs.PRINT_MAX_CHARS])
            print("PALETTE (HEXADECIMAL)")
            print(paletteHex[0:acs.PRINT_MAX_CHARS])
            print()
            print()
    if acs.FLAG_PRINT_8BIT:
        print("VALUES SCALED UP TO 8-BITS-PER-CHANNEL:")
        if acs.FLAG_PRINT_TEXTURE:
            print("TEXTURE (8-BIT BINARY)")
            print(textureBin8[0:acs.PRINT_MAX_CHARS])
            print("TEXTURE (8-BIT DECIMAL)")
            print(str(textureDec8)[0:acs.PRINT_MAX_CHARS])
            print("TEXTURE (8-BIT HEXADECIMAL)")
            print(textureHex8[0:acs.PRINT_MAX_CHARS])
            print()
            print()
        if acs.FLAG_PRINT_PALETTE and acs.ENABLE_CUSTOM_PALETTE:
            print("PALETTE (8-BIT BINARY)")
            print(paletteBin8[0:acs.PRINT_MAX_CHARS])
            print("PALETTE (8-BIT DECIMAL)")
            print(str(paletteDec8)[0:acs.PRINT_MAX_CHARS])
            print("PALETTE (8-BIT HEXADECIMAL)")
            print(paletteHex8[0:acs.PRINT_MAX_CHARS])
            print()
            print()

    
    # TODO: STRING EXPORT
    # (SAVING TO FILES)

    # IMAGE EXPORT
    print("SHAPE OF IMAGE (before any TILING or SCALING operations)")
    print(numpyImage.shape)
    newRed = numpyImage[:,:,0]
    newGreen = numpyImage[:,:,1]
    newBlue = numpyImage[:,:,2]
    # Tiles the image, if necessary
    if (acs.TILE_X != 1) or (acs.TILE_Y != 1):
        newRed = numpy.tile(newRed, (acs.TILE_X, acs.TILE_Y))
        newGreen = numpy.tile(newGreen, (acs.TILE_X, acs.TILE_Y))
        newBlue = numpy.tile(newBlue, (acs.TILE_X, acs.TILE_Y))
        numpyImage = numpy.transpose(numpy.array((newRed, newGreen, newBlue), dtype=acs.DEFAULT_INT_DATATYPE), (1, 2, 0))
    print("SHAPE OF IMAGE (after TILING but before SCALING)")
    print(numpyImage.shape)
    # Saves a copy of the current image, and increments saveCount
    saveImageResized(numpyImage, getSavePath(saveCount), acs.SCALE_X, acs.SCALE_Y)
    saveCount += 1


def main():
    # RANDOM SEEDING
    random.seed("030303")
    # WRAPPER
    wrapper()


main()
