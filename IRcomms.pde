//A remote with an accelerometer for Sony IR protocol
//The sleep code is adapted from www.arduino.cc/playground/Learning/ArduinoSleepCode, (C) D. Cuartielles
//Other parts of this code are copyrighted by me. You can use this code freely, just  mention me in the
//copyright section.
//
//Original Copyright (C) Timo Herva aka 'mettapera', 2009
// hacked up by Andrew Shirley

byte volume_up = 0x24;//B0100100
//create an array for the 12-bit signal: 7-bit command + 5-bit address
byte array_signal[] = {0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0};
//some pretty obvious pins
byte pin_infrared = 9; //don't chnage this one without changeing the pwm freq setup!
byte pin_visible = 13;

//command decoding variables
byte value_decode1 = 0;
byte value_decode2 = 0;

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

//function which send the command over an IR-led
void signal_send() {
  //start the message with a 2.4 ms time up
  ir_up();
  delayMicroseconds(2400);
  
  for (int a = 0; a < 12; a++) {
    //time down is always 0.6 ms
    ir_down();
    delayMicroseconds(600);
    if (array_signal[a] == 1) {
      //"1" is always 1.2 ms high
      ir_up();
      delayMicroseconds(1200);
    }
    else {
      //"0" is always 0.6 ms high
      ir_up();
      delayMicroseconds(600);
    }
  }
  ir_down();
  delay(random(250, 1000));
}

void ir_up() {
  analogWrite(pin_infrared, 255);
  digitalWrite(pin_visible, HIGH);
}

void ir_down() {
  analogWrite(pin_infrared, 0);
  digitalWrite(pin_visible, LOW);
}

//setting things ready  
void setup() {
  //set the pins
  pinMode(pin_infrared, OUTPUT);
  pinMode(pin_visible, OUTPUT);
  
  //set the carrier wave frequency. This only sets up pin 9 so don't change the pin_infrared config!
  TCCR1A = _BV(WGM01) | _BV(COM0A0); // | _BV(COM0B0); for another pin (10)
  TCCR1B = _BV(CS00);
  
  TIMSK1 = 0;
  TIFR1 = _BV(OCF1A);
  
  OCR1A = 13 - 1;
  //OCR1B = 13 - 1; for another pin (10)
}

void loop() {
  command_decode(volume_up);
  signal_send();
}
 


