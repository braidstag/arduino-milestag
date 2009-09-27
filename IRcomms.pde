//A remote with an accelerometer for Sony IR protocol
//The sleep code is adapted from www.arduino.cc/playground/Learning/ArduinoSleepCode, (C) D. Cuartielles
//Other parts of this code are copyrighted by me. You can use this code freely, just  mention me in the
//copyright section.
//
//Original Copyright (C) Timo Herva aka 'mettapera', 2009
// hacked up by Andrew Shirley


//some pretty obvious pins
byte pin_infrared = 9; //don't chnage this one without changeing the pwm freq setup!
byte pin_visible = 13;
byte pin_ir_reciever = 12;

////////////////////////
// IR Writing variables
byte volume_up = 0x24;//B0100100
//create an array for the 12-bit signal: 7-bit command + 5-bit address
byte array_signal[] = {0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0};

//command decoding variables
byte value_decode1 = 0;
byte value_decode2 = 0;

byte writeBuffer = 0;
byte writeBits = 0;
unsigned long writeUpTime = 0;
unsigned long writeDownTime = 0;
unsigned long  writeLastChangeTime = 0;

////////////////////////
// IR reading variables
byte readBuffer = 0;
byte bitsRead = 0;
byte oldBitsRead = 0;

byte oldPinValue = 1;
unsigned long readRiseTime;

byte timingTolerance = 200;

////////////////////////
// IR reading functions
void signal_recieve() {
  byte pinValue = digitalRead(pin_ir_reciever);
  if (oldPinValue && !pinValue) {
    Serial.print("/ @");
    Serial.println(micros());
    //IR rising edge (falling edge on this pin)
    readRiseTime = micros();
    oldPinValue = pinValue;
  }
  else if (!oldPinValue && pinValue) {
    //IR falling edge (rising edge on this pin)
    unsigned long duration = micros() - readRiseTime;
    Serial.print("\\ @ ");
    Serial.print(micros());
    Serial.print("  ");
    Serial.println(duration);
    
    if (within_tolerance(duration, 2400, timingTolerance)) {
      //we are within tollerance of 2400 us - a restart
      readBuffer = 0;
      bitsRead = 0;
    }
    else if (within_tolerance(duration, 1200, timingTolerance)) {
      //we are within tollerance of 1200 us - a one
      readBuffer = (readBuffer << 1) + 1;
      bitsRead++;
    }
    if (within_tolerance(duration, 600, timingTolerance)) {
      //we are within tollerance of 600 us - a zero
      readBuffer = readBuffer << 1;
      bitsRead++;
    }
    
    
    oldPinValue = pinValue;
  }
}

boolean within_tolerance(unsigned long value, unsigned long target, byte tolerance) {
  long remainder = value - target;
  return remainder < tolerance && remainder > -tolerance;
}

void debug_signal() {
  if (bitsRead != oldBitsRead) {
    if (bitsRead == 0) {
      Serial.println("====");
    }
    
    oldBitsRead = bitsRead;
    Serial.println(readBuffer, BIN);
  }
}

////////////////////////
// IR writing functions

/*
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
*/

void start_command(byte command) {
  if (writeUpTime || writeDownTime) {
    //already writing - this is an error
    return;
  }
  
  writeBuffer = command;
  writeBits = 8;
  
  //write header
  ir_up();
  Serial.println("  /");
  writeDownTime = 2400;
}

void signal_send() {
  unsigned long elapsed = micros() - writeLastChangeTime;
  
  if (writeDownTime && writeDownTime < elapsed) {
    Serial.print("  \\");
    Serial.print(elapsed);
    Serial.print(" \\ ");
    Serial.println(writeDownTime, DEC);
    ir_down();
    writeDownTime = 0;
    
    if (writeBits) {
      //not done yet
      writeUpTime = 600;
    }
  }
  else if (writeUpTime && writeUpTime < elapsed) {
    Serial.print("  /");
    Serial.print(elapsed);
    Serial.print(" / ");
    Serial.println(writeUpTime, DEC);
    ir_up();
    writeUpTime = 0;
    
    if (writeBuffer & B1) {
      //write a one
      writeDownTime = 1200;
    }
    else {
      //write a zero
      writeDownTime = 600;
    }
    
    writeBuffer = writeBuffer >> 1;
    writeBits --;
  }
}

void ir_up() {
  analogWrite(pin_infrared, 255);
  digitalWrite(pin_visible, HIGH);
  writeLastChangeTime = micros();
}

void ir_down() {
  analogWrite(pin_infrared, 0);
  digitalWrite(pin_visible, LOW);
  writeLastChangeTime = micros();
}

////////////////////////
// general functions

//setting things ready  
void setup() {
  //set the pins
  pinMode(pin_infrared, OUTPUT);
  pinMode(pin_visible, OUTPUT);
  pinMode(pin_ir_reciever, INPUT);
  
  //set the carrier wave frequency. This only sets up pin 9 so don't change the pin_infrared config!
  TCCR1A = _BV(WGM01) | _BV(COM0A0); // | _BV(COM0B0); for another pin (10)
  TCCR1B = _BV(CS00);
  
  TIMSK1 = 0;
  TIFR1 = _BV(OCF1A);
  
  OCR1A = 13 - 1;
  //OCR1B = 13 - 1; for another pin (10)

  //debug  
  Serial.begin(9600); 
  Serial.println("jobbie - debug");
}

unsigned long time = micros();

void loop() {
  //command_decode(volume_up);
  //signal_send();
  
  
  if (micros() > time + 1000000) {
    time = micros();
    //Serial.print("starting ");
    //Serial.println(volume_up, BIN);
    start_command(volume_up);
  }
  signal_send();
  
  signal_recieve();
  debug_signal();
}
