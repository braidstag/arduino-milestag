/*
 * SSD1306 interface.
 * 
 * A lot of this code was taken from AdaFruit's library (although we try to use less memory)
 * https://github.com/adafruit/Adafruit_SSD1306/blob/master/Adafruit_SSD1306.cpp
 */
 
#include <Wire.h>
#include "glcdfont.c"
#include "IRComms.h"

#define SSD1306_LCDWIDTH                  128
#define SSD1306_LCDHEIGHT                 64

#define SSD1306_SETCONTRAST 0x81
#define SSD1306_DISPLAYALLON_RESUME 0xA4
#define SSD1306_DISPLAYALLON 0xA5
#define SSD1306_NORMALDISPLAY 0xA6
#define SSD1306_INVERTDISPLAY 0xA7
#define SSD1306_DISPLAYOFF 0xAE
#define SSD1306_DISPLAYON 0xAF

#define SSD1306_SETDISPLAYOFFSET 0xD3
#define SSD1306_SETCOMPINS 0xDA

#define SSD1306_SETVCOMDETECT 0xDB

#define SSD1306_SETDISPLAYCLOCKDIV 0xD5
#define SSD1306_SETPRECHARGE 0xD9

#define SSD1306_SETMULTIPLEX 0xA8

#define SSD1306_SETLOWCOLUMN 0x00
#define SSD1306_SETHIGHCOLUMN 0x10

#define SSD1306_SETSTARTLINE 0x40

#define SSD1306_MEMORYMODE 0x20
#define SSD1306_COLUMNADDR 0x21
#define SSD1306_PAGEADDR   0x22

#define SSD1306_COMSCANINC 0xC0
#define SSD1306_COMSCANDEC 0xC8

#define SSD1306_SEGREMAP 0xA0

#define SSD1306_CHARGEPUMP 0x8D

#define SSD1306_EXTERNALVCC 0x1
#define SSD1306_SWITCHCAPVCC 0x2

// Scrolling #defines
#define SSD1306_ACTIVATE_SCROLL 0x2F
#define SSD1306_DEACTIVATE_SCROLL 0x2E
#define SSD1306_SET_VERTICAL_SCROLL_AREA 0xA3
#define SSD1306_RIGHT_HORIZONTAL_SCROLL 0x26
#define SSD1306_LEFT_HORIZONTAL_SCROLL 0x27
#define SSD1306_VERTICAL_AND_RIGHT_HORIZONTAL_SCROLL 0x29
#define SSD1306_VERTICAL_AND_LEFT_HORIZONTAL_SCROLL 0x2A


#define I2C_ADDR 0x3C

#define SCREEN_WIDTH 21
#define SCREEN_HEIGHT 8

char screen_scrollingData[SCREEN_HEIGHT][SCREEN_WIDTH] = {
// 1234567890123456789012
  "          /\\        ",
  "         /  \\       ",
  "        /    \\      ",
  "       /      \\     ",
  "      /        \\    ",
  "     /          \\   ",
  "    / FireStorm  \\  ",
  "   /______________\\ "
};
byte screen_scrollingDataBottomLineIndex = 7;


void ssd1306_command(uint8_t c) {
    uint8_t control = 0x00;   // Co = 0, D/C = 0
    Wire.beginTransmission(I2C_ADDR);
    Wire.write(control);
    Wire.write(c);
    Wire.endTransmission();
}

void display() {
  ssd1306_command(SSD1306_COLUMNADDR);
  ssd1306_command(0);   // Column start address (0 = reset)
  ssd1306_command(SSD1306_LCDWIDTH-1); // Column end address (127 = reset)

  ssd1306_command(SSD1306_PAGEADDR);
  ssd1306_command(0); // Page start address (0 = reset)
  ssd1306_command(7); // Page end address



  for(int8_t charRow=0; charRow<8; charRow++) { // 8 rows of character
    byte lineBuffer[24] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    byte lineBufferCount = 0;
    
    for(int8_t charCol=0; charCol<21; charCol++) { // 21 characters per row
      char c = screen_scrollingData[(screen_scrollingDataBottomLineIndex + 1 + charRow) % 8][charCol];
      for(int8_t i=0; i<5; i++) { // 5 cols within each character
        //right shift to find the correct row and check least significant bit 
        uint8_t vline = (c == 0 || c == 0x20) ? 0 : pgm_read_byte(&font[c * 5 + i]);
        lineBuffer[lineBufferCount++] = vline;
      }
      //blank col after the character
      lineBuffer[lineBufferCount++] = 0;

      //the number of bytes we write at once must be a multiple of 6
      if (lineBufferCount == 12) {
        //write out 12 bytes at once
        Wire.beginTransmission(I2C_ADDR);
        Wire.write(0x40);
        for (uint8_t x=0; x<12; x++) {
          Wire.write(lineBuffer[x]);
        }
        Wire.endTransmission();
        lineBufferCount = 0;
      }
    }

    Wire.beginTransmission(I2C_ADDR);
    Wire.write(0x40);
    //write remaining columns
    for (uint8_t x=0; x<lineBufferCount; x++) {
      Wire.write(lineBuffer[x]);
    }
    //write two blank columns to finish the line
    Wire.write(0);
    Wire.write(0);
    Wire.endTransmission();
  }
}

void screen_setup() {

  Wire.begin();

//  // Setup reset pin direction (used by both SPI and I2C)
//  pinMode(screenRst_pin, OUTPUT);
//  digitalWrite(screenRst_pin, HIGH);
//  // VDD (3.3V) goes high at start, lets just chill for a ms
//  delay(1);
//  // bring reset low
//  digitalWrite(screenRst_pin, LOW);
//  // wait 10ms
//  delay(10);
//  // bring out of reset
//  digitalWrite(screenRst_pin, HIGH);


  // Init sequence
  ssd1306_command(SSD1306_DISPLAYOFF);                    // 0xAE
  ssd1306_command(SSD1306_SETDISPLAYCLOCKDIV);            // 0xD5
  ssd1306_command(0x80);                                  // the suggested ratio 0x80

  ssd1306_command(SSD1306_SETMULTIPLEX);                  // 0xA8
  ssd1306_command(SSD1306_LCDHEIGHT - 1);

  ssd1306_command(SSD1306_SETDISPLAYOFFSET);              // 0xD3
  ssd1306_command(0x0);                                   // no offset
  ssd1306_command(SSD1306_SETSTARTLINE | 0x0);            // line #0
  ssd1306_command(SSD1306_CHARGEPUMP);                    // 0x8D

  ssd1306_command(0x14);

  ssd1306_command(SSD1306_MEMORYMODE);                    // 0x20
  ssd1306_command(0x00);                                  // 0x0 act like ks0108
  ssd1306_command(SSD1306_SEGREMAP | 0x1);
  ssd1306_command(SSD1306_COMSCANDEC);

  ssd1306_command(SSD1306_SETCOMPINS);                    // 0xDA
  ssd1306_command(0x12);
  ssd1306_command(SSD1306_SETCONTRAST);                   // 0x81

  ssd1306_command(0xCF);

  ssd1306_command(SSD1306_SETPRECHARGE);                  // 0xd9
  
  ssd1306_command(0xF1);
  
  ssd1306_command(SSD1306_SETVCOMDETECT);                 // 0xDB
  ssd1306_command(0x40);
  ssd1306_command(SSD1306_DISPLAYALLON_RESUME);           // 0xA4
  ssd1306_command(SSD1306_NORMALDISPLAY);                 // 0xA6

  ssd1306_command(SSD1306_DEACTIVATE_SCROLL);

  ssd1306_command(SSD1306_DISPLAYON);//--turn on oled panel
  display();
}

void screen_addScrollingData(const char newLine[]) {
  screen_scrollingDataBottomLineIndex = (screen_scrollingDataBottomLineIndex + 1) % SCREEN_HEIGHT;
  strncpy(screen_scrollingData[screen_scrollingDataBottomLineIndex], newLine, SCREEN_WIDTH);
  display();
}
