//#define DEBUG_DECODE 1

void decode_signal() {
#ifdef DEBUG_DECODE
  Serial.print("==");
  Serial.println(readBuffer, BIN);
  Serial.println(readBuffer, HEX);
#endif
}

//setting things ready
void setup() {
  //set the pins
  pinMode(9, OUTPUT);
  pinMode(pin_ir_feedback, OUTPUT);
  pinMode(pin_ir_reciever, INPUT);
  pinMode(power_relay_pin, OUTPUT);
  pinMode(laser_pin, OUTPUT);
  pinMode(trigger_pin, INPUT);
  pinMode(power_monitor_pin, INPUT);
  pinMode(muzzlered_pin, OUTPUT);
  pinMode(muzzlegreen_pin, OUTPUT);
  pinMode(muzzleblue_pin, OUTPUT);
  
  // see http://www.atmel.com/dyn/resources/prod_documents/doc8161.pdf for more details (page 136 onwards)
  //set the carrier wave frequency. This only sets up pin 9.
  TCCR1A = _BV(COM1A0); // | _BV(COM1B0); for another pin (10)
  TCCR1B = _BV(WGM12) | _BV(CS10);
  
  TIMSK1 = 0; //no interupts
  TIFR1 = _BV(OCF1A) | _BV(OCF1A); //clear Output Compare Match Flags (by setting them :-P )
  unsigned long desired_freq = 40000;
  OCR1A = 10000000/desired_freq - 1; // see page 126 of datasheet for this equation
  //OCR1B = 10000000/desired_freq - 1; for another pin (10)

  ir_down();

  //debug  
  Serial.begin(115200);
  
  digitalWrite(power_relay_pin, HIGH);
}

boolean clientConnected = false;
unsigned long time = micros();

void loop() {
  timeDebug();
  checkTrigger();
  signal_send();
  if (signal_recieve()) {
    decode_signal();
    mt_parseIRMessage(readBuffer);
  }

  checkSerial();
  timeDebug();
}

boolean oldTrigger = false;
long lastTriggerCheck = 0;

void checkTrigger() {
  //only check the trigger every millisecond as a crude de-bounce.
  if (micros() > lastTriggerCheck + 1000) {
    boolean trigger = digitalRead(trigger_pin);
    if (trigger && trigger != oldTrigger) {
      //if we are still debugging and the pi hasn't connected, just send a shot with fixed team/player/damage
      if (clientConnected) {
        Serial.println("Trigger()");
      }
      else {
        mt_fireShot();
      }

      oldTrigger = trigger;    
    }
    if (!trigger && trigger != oldTrigger) {
      if (clientConnected) {
        Serial.println("TriggerRelease()");
      }

      oldTrigger = trigger;    
    }
    lastTriggerCheck = micros();
  }
}

void checkBattery() {
  Serial.println(analogRead(power_monitor_pin) * 5 / 1023.0);
}

void shutdown() {
  delay(50000);
  digitalWrite(power_relay_pin, LOW);
}
