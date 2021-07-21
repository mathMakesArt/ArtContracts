//# ARTCONTRACTS LICENSE:
//### This software is a part of, or a derived work based on, the ArtContracts project (https://artcontracts.net) by MathMakesArt (https://mathmakes.art)
//### Depending on what software you're using, this code may have been integrated into a larger project with more authors.
//### The ArtContracts code is free and open-source. You are free to use it however you want, including for commercial purposes.
//### All distributions and derived works MUST include a copy of this text, including author information.
//###   If a derived work contains any sort of licensing information, you must include an additional copy of this text within the license file of your software.
//### Derived works may implement this code, but you are not permitted to sell this software itself (e.g. you may not charge money for mere access to this software).
//## VERSION INFORMATION
//### This file comes from version 1.4, finalized on 2021/07/21
//## AUTHOR INFORMATION:
//### GitHub:           @MathMakesArt
//### Twitter:          @MathMakesArt
//### Website:          https://mathmakes.art
//### Email:            mathmakesart@gmail.com
//### Tezos address:    tz1gsrd3CfZv4BfPnYKq5pKpHGFVdtGCgd71 (mathmakesart.tez)

// G L O B A L     V A R I A B L E S
// INPUT VARIABLES - To be manually provided by user of this template:
var defaultNetworkString = "mainnet";
var defaultBigmapPointer = 4330;
// (To be removed or reimplemented)

// GLOBAL VARIABLES - Placeholder Values
var bitsPerChannel = 0;
var numChannels = 0;
var numRows = 0;
var numCols = 0;
var queryString = ""; // Placeholder for string of JSON pulled from RPC node
var inputString = ""; // Placeholder for PARSED version of queryString
// Total Width
var totalWidth = window.innerWidth;
var totalHeight = window.innerHeight;
var cellWidth = 0;
var cellHeight = 0;
// Bits Per Pixel - The number of binary digits required to fully encode for a single pixel
var bitsPerPixel = 0;
// coefficientTo8 - Floating-point coefficient for converting each channel to and from the "standard" bit representation (8 bits per channel)
var coefficientTo8 = 0.0;
// started - Boolean which prevents draw() calls until manually flipped from false to true
var started = false; // Drawing of canvas contents will not begin until this boolean is set to true

// GLOBAL VARIABLES - Hard Coded
var backgroundColor = 255;
var grid = [];
var fr = 30; // Framerate in FPS
var frameCount = 0; // Number of frames elapsed since first draw() call
// GLOBAL VARIABLES - Standardization (DO NOT MODIFY UNLESS YOU KNOW WHAT YOU'RE DOING)
var standardBitsPerChannel = 8;


// chunkString function written by StackOverflow user Vivin Paliath
// USER PAGE: https://stackoverflow.com/users/263004/vivin-paliath
// ANSWER PAGE: https://stackoverflow.com/a/7033662
function chunkString(str, length) {
  return str.match(new RegExp('.{1,' + length + '}', 'g'));
}

// URL BUILDING FUNCTIONS
function getBigmapKeyURL(net = defaultNetworkString, ptr = defaultBigmapPointer) {
  return "https://api.better-call.dev/v1/bigmap/" + net + "/" + ptr.toString() + "/keys";
}

// JSON PARSERS
function getOnchainValue(index, urlString) {
  return jQuery.getJSON(urlString, function(data) {
    queryString = data[index]["data"]["value"]["value"];
  })
}

function getOnchainKey(index, urlString) {
  return jQuery.getJSON(urlString, function(data) {
    queryString = data[index]["data"]["key"]["value"];
  })
}

// TODO: Find a way to use this with .always()
//       (Currently, attempting to use it returns an error)
function getDimensions() {
  getOnchainValue(1, getBigmapKeyURL());
}

function parseDimensions(dimString) {
  return dimString.toString().split(",").map(Number);
}

// HEX-ASCII CONVERSION
function hexToAscii(str) {
  var hex = str.toString();
  var numChars = hex.length;
  var strOut = "";
  for (var n = 0; n < numChars; n += 2) {
    strOut += String.fromCharCode(parseInt(hex.substr(n, 2), 16));
  }
  return strOut;
}


function setup() {
  // SETUP ACTIONS
  colorMode(RGB, 255); // Sets the color interpretation mode
  rectMode(CORNER); // Sets the rectangle interpretation mode
  createCanvas(window.innerWidth, window.innerHeight);
  textAlign(CENTER, CENTER);
  frameRate(fr);

  // Gets the "dimensions" value into queryString
  getOnchainValue(1, getBigmapKeyURL()).always(function() {
    // Anything inside of this function block will wait to execute until AFTER the getOnchainValue() return

    // Parses queryString into an array of integers
    var dimensions = parseDimensions(queryString);
    // Assigns each integer in the array to its appropriate placeholder global
    bitsPerChannel = dimensions[0];
    numChannels = dimensions[1];
    numRows = dimensions[2];
    numCols = dimensions[3];

    // COMPUTING VALUES FOR PLACEHOLDER GLOBAL VARIABLES
    // totalWidth and totalHeight
    totalWidth = Math.floor(960 / numCols) * numCols;
    totalHeight = Math.floor(960 / numRows) * numRows;
    // Modifications if the image is taller than it is wide (PORTRAIT)
    if (numRows > numCols) {
      totalWidth = Math.floor(960 / numRows) * numCols;
    }
    // Modifications if the image is wider than it is tall (LANDSCAPE)
    if (numCols > numRows) {
      totalHeight = Math.floor(960 / numCols) * numRows;
    }
    // Cell Width and Height
    cellWidth = Math.floor(totalWidth / numCols);
    cellHeight = Math.floor(totalHeight / numRows);
    // Bits per Pixel
    var bitsPerPixel = numChannels * bitsPerChannel;
    // CoefficientTo8
    coefficientTo8 = (((2 ** standardBitsPerChannel) - 1) / ((2 ** bitsPerChannel) - 1));

    getOnchainValue(2, getBigmapKeyURL()).always(function() {
      // Anything inside of this function block will wait to execute until AFTER the getOnchainValue() return

      // Set input string to have "0x" prefix
      // WARNING: DO NOT ACCESS queryString BEYOND HERE. Use inputString instead.
      inputString = "0x" + queryString;
      // Computes bit-correct versions of the input string(s),
      //   and splits the binary into a series of smaller strings on a per-chunk basis
      // The .slice(1) function REMOVES THE LEADING 1 bit of the binary string
      var inputStringBinString = BigInt(inputString).toString(2).slice(1);
      // Splits the texture 
      var inputPixelsBinary = chunkString(inputStringBinString, bitsPerPixel);

      // Initializes the pixel count as 0
      var pixelCount = 0;
      // Construct the grid and fill with colors pertaining to each integer in stringArr
      for (var y = 0; y < numRows; y++) {
        // Push a new empty (row) array into the grid
        grid.push([]);
        // loop through all cells of the current row
        for (var x = 0; x < numCols; x++) {
          // Push a new empty (cell) array into the current row of the grid
          grid[y].push([]);
          // Creates an empty "color array"
          var colorArr = [];
          // Get the binary string associated with the current pixelCount value and breaks it into "channel strings"
          var channelsBinaryIn = chunkString(inputPixelsBinary[pixelCount], bitsPerChannel);
          // Iterate through each channel of the current binary string
          for (channelBinaryIn of channelsBinaryIn) {
            // Convert the binary value to decimal, multiply it by the LAST CHANNEL's multiplier, and append it to the color array
            colorArr.push(Math.round(coefficientTo8 * parseInt(channelBinaryIn, 2)));
          }
          // Set the current grid cell equal to the color array
          grid[y][x] = colorArr;
          // Increment pixelCount
          pixelCount++;
        }
      }
      // Update the started global to true so that draw() is allowed to execute
      started = true;
      // Call windowResized once before drawing begins
      windowResized();
    })
  })
}

function draw() {
  if (started) {
    // Fills the background with backgroundColor
    background(backgroundColor);
    // Initializes the pixel count as 0
    var pixelCount = 0;

    // loop through all rows in the grid
    for (var y = 0; y < numRows; y++) {
      // loop through all cells of the current row
      for (var x = 0; x < numCols; x++) {
        // Get the color associated with the current grid position
        var currentColor = color(grid[y][x][0], grid[y][x][1], grid[y][x][2], grid[y][x][3]);
        // Determine proper drawing position
        var currentScreenX = x * cellWidth;
        var currentScreenY = y * cellHeight;
        // Set drawing attributes and draw a rectangle
        fill(currentColor);
        noStroke();
        rect(currentScreenX, currentScreenY, cellWidth, cellHeight);
        // Increment pixelCount
        pixelCount++;
      }
    }
  }
}

function windowResized() {
  //resizeCanvas(window.innerWidth, window.innerHeight)
  resizeCanvas(totalWidth, totalHeight);
}