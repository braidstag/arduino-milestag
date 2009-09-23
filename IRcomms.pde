//A remote with an accelerometer for Sony IR protocol
//The sleep code is adapted from www.arduino.cc/playground/Learning/ArduinoSleepCode, (C) D. Cuartielles
//Other parts of this code are copyrighted by me. You can use this code freely, just  mention me in the
//copyright section.
//
//Copyright (C) Timo Herva aka 'mettapera', 2009

//commands for some functions
byte volume_up = 0x24;//B0100100
byte volume_down = 0x64;//B1100100
byte power_toggle = 0x54;//B1010100
byte av_scroll = 0x52;//B1010010
//create an array for the 12-bit signal: 7-bit command + 5-bit address
byte array_signal[] = {0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0};
//some pretty obvious pins
byte pin_infrared = 12;
byte pin_visible = 13;
//variables for the carrier wave(40kHz) of the signal, desirable duty-cycle is 1/4 - 1/3
byte time_up = 9;
byte time_down = 9;

byte iter_start = 90;
byte iter_one = 45;
byte iter_zero = 22;

float factor = 2;

//12+5 = 17 is the duration of a 40KHz wave, what is 56? also need to multiply up all the iterations of this to get the same duration.



//command decoding variables
byte value_decode1 = 0;
byte value_decode2 = 0;
int delay_value = 600;

//function to decode the command needed to the array (one array and five binarynumbers consume less space than five arrays)
//TODO use >> inside the sending loop, 6 bytes are even cheaper still!.
void command_decode(int binary_command) {
  value_decode1 = binary_command;
  for (int i = 6; i > -1; i--) {
    value_decode2 = value_decode1 & B1;
    if (value_decode2 == 1) {
      array_signal[i] = 1;
    }
    else {
      array_signal[i] = 0;
    }
    value_decode1 = value_decode1 >> 1;
  }
}

void carrier_make() {
  digitalWrite(pin_infrared, HIGH);
  digitalWrite(pin_visible, HIGH);
  delayMicroseconds(time_up);
  digitalWrite(pin_infrared, LOW);
  digitalWrite(pin_visible, LOW);
  delayMicroseconds(time_down);
}

//function which send the command over an IR-led
void signal_send() {
  for (int i = 0; i < iter_start; i++) {//start the message with a 2.4 ms time up
    carrier_make();
  }
  for (int a = 0; a < 12; a++) {
    delayMicroseconds(delay_value);//time down is always 0.6 ms
    if (array_signal[a] == 1) {
      for (int i = 0; i < iter_one; i++) {//"1" is always 1.2 ms high
        carrier_make();
      }
    }
    else {
      for (int i = 0; i < iter_zero; i++) {//"0" is always 0.6 ms high
        carrier_make();
      }
    }
  }
  delay(random(250, 1000));
}

void adjust_times() {
  factor = factor*= 0.9;
  
  if (factor < 0.2) {
    factor = 2;
  }
  
  
  time_up = factor * 9;
  time_down = factor * 9;

  iter_start = 90 / factor;
  iter_one = 45 / factor;
  iter_zero = 22 / factor;
}

//setting things ready  
void setup() {
  pinMode(pin_infrared, OUTPUT);
}

void loop() {
  command_decode(volume_up);
  adjust_times();
  signal_send();
}
 


