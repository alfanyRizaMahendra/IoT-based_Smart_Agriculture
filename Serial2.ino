// Relay logic is inverted
#include <SoftwareSerial.h>
#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <DHT.h>

#define pump 7 
#define peltier 8 // aktuator 1
#define mist 9 // aktuator 2
#define lamp 10 // aktuator 3

// Setup a oneWire instance to communicate with any OneWire devices (not just Maxim/Dallas temperature ICs)
OneWire oneWire(2); // one wire at GPIO digital 2

// Pass our oneWire reference to Dallas Temperature. 
DallasTemperature sensors(&oneWire);

DeviceAddress tempDeviceAddress; // We'll use this variable to store a found device address
SoftwareSerial serialSaya(12, 11); // RX, TX
DHT dht(3, DHT11);

// edit peltier and humidifier duration here (millisecond) !!
unsigned long peltDuration = 3000, humDuration = 3000;

unsigned long lastPelt = 0, lastHum = 0; 
String inputString = "", commandString ="", nyala = "", nyala_pompa = "", nyala_pelt = "", nyala_mist="", nyala_lamp="", ask = "";
boolean stringComplete = false, pumpCondition = false, peltIsReceived = false, mistIsReceived = false;
boolean isDifferent = false, pumpReceived = false, lampReceived = false, peltReceived = false, mistReceived = false;
boolean onPump = false, onLamp = false, onMist = false, onPelt = false, peltCondition = false, humCondition = false;
unsigned long lastPump = 0, pumpDurationOn = 100000000000, pumpDurationOff = 100000000000;
int countSame = 0, sensor_value = 0;
uint8_t i = 0;

void getCommand(void);
void ask_data(void);
void kondisi(void);
void kondisi_pompa(void);
void kondisi_lampu(void);
void kondisi_peltier(void);
void kondisi_mist(void);
uint8_t split(String command);
void split_coma(String kalimat);
void check_ds18b20(void);
void printAddress(DeviceAddress deviceAddress);
void printTemperature(DeviceAddress deviceAddress);

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Wire.begin();

  // ds18b20
  sensors.begin();
  check_ds18b20();

  // dht
  dht.begin();
  
  pinMode(pump, OUTPUT);
  pinMode(peltier, OUTPUT);
  pinMode(mist, OUTPUT);
  pinMode(lamp, OUTPUT);

  digitalWrite(pump, HIGH);
  digitalWrite(peltier, HIGH);
  digitalWrite(mist, HIGH);
  digitalWrite(lamp, HIGH);

  serialSaya.begin(38400);
}

void loop() {
  // put your main code here, to run repeatedly:
  if(serialSaya.available()) {
    // get the new byte:
    char inChar = (char)serialSaya.read();
    // add it to the inputString:
    //Serial.println(inChar);
    inputString += inChar;
    if (inChar == '\n') stringComplete = true;
    if(stringComplete)
    {
      stringComplete = false;
      getCommand();
      Serial.print("\n\n-------------------Command Diterima---------------------\n");
      Serial.print(commandString);
      Serial.println("\n--------------------------------------------------\n");
      Serial.println(commandString.charAt(0));
      switch (commandString.charAt(0)){
        case '?': //  ambil data sensor
          ask_data();
          Serial.print("\n ask data = ");
          Serial.println(ask);
          if(ask == "lux")
          {
            //sensor_value = analogRead(A0);
            //int ldrSend = sensor_value/4;
            int ldrSend = random(0,256);
            if(ldrSend > 255) ldrSend = 255;
            Serial.print("Cahaya = ");
            Serial.println(ldrSend);
            serialSaya.write(ldrSend);
            serialSaya.write("\n"); 
          }
          if(ask == "hum")
          {
            //sensor_value = dht.readHumidity();
            sensor_value = random(0,100);
            Serial.print("humidity = ");
            Serial.println(sensor_value);
            serialSaya.write(sensor_value);
            serialSaya.write("\n"); 
          }
          if(ask == "tem")
          {
            Serial.print("Requesting temperatures ds18b20...");
            sensors.requestTemperatures(); // Send the command to get temperatures
            Serial.println("DONE");
            //sensor_value = sensors.getTempC(tempDeviceAddress);
            sensor_value = random(26,35);
            Serial.print("temperature = ");
            Serial.println(sensor_value);
            serialSaya.write(sensor_value);
            serialSaya.write("\n");
          }
          ask = "";
          inputString = "";   
          commandString ="";
          break;
        case 'q': // aktuator 1 
          kondisi();
          if(nyala == "ON") 
          {
            peltCondition = true;
            humCondition = false;
            digitalWrite(lamp, HIGH);
            peltIsReceived = true;
          }
          inputString = "";   
          commandString ="";
          break;
        case 'w': // aktuator 2
          kondisi();
          if(nyala == "ON") 
          {
            peltCondition = false;
            humCondition = true;
            digitalWrite(lamp, HIGH);
            mistIsReceived = true;
          }
          inputString = "";   
          commandString ="";
          break;
        case 'e': // aktuator 3
          kondisi();
          if(nyala == "ON") 
          {
            peltCondition = false;
            humCondition = false;
            digitalWrite(lamp, LOW);
            Serial.println("Lampu Menyala");
          }
          inputString = "";   
          commandString ="";
          break;
        case 'r': // aktuator 1 & 2
          kondisi();
          if(nyala == "ON") 
          {
            peltCondition = true;
            humCondition = true;
            digitalWrite(lamp, HIGH);
            peltIsReceived = true;
            mistIsReceived = true;
          }
          inputString = "";   
          commandString ="";
          break;
        case 't': // aktuator 2 & 3 
          kondisi();
          if(nyala == "ON") 
          {
            peltCondition = false;
            humCondition = true;
            digitalWrite(lamp, LOW);
            Serial.println("Lampu Menyala !");
            mistIsReceived = true;   
          }
          inputString = "";   
          commandString ="";
          break;
        case 'y': // aktuator 1 & 3
          kondisi();
          if(nyala == "ON") 
          {
            peltCondition = true;
            humCondition = false;
            digitalWrite(lamp, LOW);
            Serial.println("Lampu Menyala !!");
            peltIsReceived = true;
          }
          inputString = "";   
          commandString ="";   
          break;
        case 'u': // aktuator 1 & 2 & 3
          kondisi();
          if(nyala == "ON") 
          {
            peltCondition = true;
            humCondition = true;
            digitalWrite(lamp, LOW);
            Serial.println("Lampu Menyala !!!");
            peltIsReceived = true;
            mistIsReceived = true;            
          }
          inputString = "";   
          commandString ="";
          break;
        case 'a': // menyalakan peltier
          kondisi_peltier();
          if(nyala_pelt == "ON") onPelt = true;
          else onPelt = false;  
          inputString = "";   
          commandString ="";
          break;
        case 's': // menyalakan humidifier 
          kondisi_mist();
          if(nyala_mist == "ON") onMist = true;
          else onMist = false;  
          inputString = "";   
          commandString ="";
          break;
        case 'd': // menyalakan lampu 
          kondisi_lampu();
          if(nyala_lamp == "ON") onLamp = true;
          else onLamp = false;  
          inputString = "";   
          commandString ="";
          break;
        case 'o': // menyalakan pompa air 
          kondisi_pompa();
          if(nyala_pompa == "ON") onPump = true;
          else onPump = false;  
          inputString = "";   
          commandString ="";
          break;
        case 'p': // menangkap durasi pompa mati dan menyala
          split_coma(commandString);
          inputString = "";   
          commandString ="";
          break;
        default:
          Serial.println("Ideal Bro, Mantap !!!!");
          peltCondition = false;
          humCondition = false;
          digitalWrite(lamp, HIGH);
          inputString = "";   
          commandString ="";
          break;
      }
    }
  }

  unsigned long now = millis();
  if((now - lastPump >= pumpDurationOff) && (pumpCondition == false) && ((isDifferent == true) || (countSame >= 1))){
    lastPump = now;
    pumpCondition = true;
    Serial.println("\n------------------------------");
    Serial.println("Pompa air menyala !");
    digitalWrite(pump, LOW); 
  }

  if((now - lastPump >= pumpDurationOn) && (pumpCondition == true) && ((isDifferent == true) || (countSame >= 1))){
    lastPump = now;
    pumpCondition = false;
    Serial.println("\n------------------------------");
    Serial.println("Pompa air mati !");
    digitalWrite(pump, HIGH); 
    isDifferent = true;
  }

  // peltier
  if((now - lastPelt >= peltDuration) && (peltCondition == true) && peltIsReceived){
    lastPelt = now;
    peltCondition = false;
    Serial.println("\n------------------------------");
    Serial.println("Peltier menyala !");
    digitalWrite(peltier, LOW); 
  }

  if((now - lastPelt >= peltDuration) && (peltCondition == false) && peltIsReceived){
    lastPelt = now;
    peltIsReceived = false;
    Serial.println("\n------------------------------");
    Serial.println("Peltier mati !");
    digitalWrite(peltier, HIGH); 
  }

  // Humidifier
  if((now - lastHum >= humDuration) && (humCondition == true) && mistIsReceived){
    lastHum = now;
    humCondition = false;
    Serial.println("\n------------------------------");
    Serial.println("Humidifier menyala !");
    digitalWrite(mist, LOW); 
  }

  if((now - lastHum >= humDuration) && (humCondition == false) && mistIsReceived){
    lastHum = now;
    mistIsReceived = false;
    Serial.println("\n------------------------------");
    Serial.println("Humidifier mati !");
    digitalWrite(mist, HIGH); 
  }
  
  // pompa manual
  if(pumpReceived && onPump)
  {
    pumpReceived = false;
    digitalWrite(pump, LOW);
  }

  if(pumpReceived && (onPump == false))
  {
    pumpReceived = false;
    digitalWrite(pump, HIGH);
  }

  // peltier manual
  if(peltReceived && onPelt)
  {
    peltReceived = false;
    digitalWrite(peltier, LOW);
  }

  if(peltReceived && (onPelt == false))
  {
    peltReceived = false;
    digitalWrite(peltier, HIGH);
  }

  // humidifier manual
  if(mistReceived && onMist)
  {
    mistReceived = false;
    digitalWrite(mist, LOW);
  }

  if(mistReceived && (onMist == false))
  {
    mistReceived = false;
    digitalWrite(mist, HIGH);
  }

  // Lampu UV manual
  if(lampReceived && onLamp)
  {
    lampReceived = false;
    digitalWrite(lamp, LOW);
  }

  if(lampReceived && (onLamp == false))
  {
    lampReceived = false;
    digitalWrite(lamp, HIGH);
  }
}

// Additional Function
unsigned long foo (String sentence) // convert string to unsigned long 
{
  return strtoul(sentence.c_str(), NULL, 10);
}

void getCommand(void){
  if(inputString.length()>0) commandString = inputString.substring(0,inputString.length()-2);
}

void ask_data(void){
  if(commandString.length()>0) ask = commandString.substring(1,commandString.length()-4);
}

void kondisi(void){
  if(commandString.length()>0) 
  {
    nyala = commandString.substring(1,commandString.length());
    Serial.println(nyala);
  }
}

void kondisi_pompa(void){
  if(commandString.length()>0) 
  {
    pumpReceived = true;
    nyala_pompa = commandString.substring(1,commandString.length());
    Serial.println(nyala_pompa);
  }
}

void kondisi_lampu(void){
  if(commandString.length()>0) 
  {
    lampReceived = true;
    nyala_lamp = commandString.substring(1,commandString.length());
    Serial.println(nyala_lamp);
  }
}

void kondisi_peltier(void){
  if(commandString.length()>0) 
  {
    peltReceived = true;
    nyala_pelt = commandString.substring(1,commandString.length());
    Serial.println(nyala_pelt);
  }
}

void kondisi_mist(void){
  if(commandString.length()>0) 
  {
    mistReceived = true;
    nyala_mist = commandString.substring(1,commandString.length());
    Serial.println(nyala_mist);
  }
}

uint8_t split(String command){
  uint8_t index, colorNum;
  index = command.indexOf('$');
  colorNum = command.substring(1, index).toInt();
  return colorNum;
}

void split_coma(String kalimat){ // ~,pumpOn,pumpOff$
  unsigned long new_pumpDurationOn, new_pumpDurationOff;
  int i1 = kalimat.indexOf(',');
  int i2 = kalimat.indexOf(',', i1+1);
  int i3 = kalimat.indexOf(',', i2+1); 

  new_pumpDurationOn = foo(kalimat.substring(i1 + 1, i2)) * 1000;
  new_pumpDurationOff = foo(kalimat.substring(i2 + 1, i3)) * 1000 * 60;
  if((new_pumpDurationOn != pumpDurationOn) || (new_pumpDurationOff != pumpDurationOff)) 
  {
    pumpDurationOn = new_pumpDurationOn;
    pumpDurationOff = new_pumpDurationOff;
    countSame = 0;
    isDifferent = true;
  }
  else{ 
    countSame += 1;
  }
  Serial.println("\n------------------------------------------------------------");
  Serial.print("Pompa air Menyala selama ");
  Serial.print(pumpDurationOn);
  Serial.print(" milliseconds; Mati selama ");
  Serial.print(pumpDurationOff);
  Serial.println(" milliseconds");
  Serial.println("----------------------------------------------------------\n");
}

// function to print a device address
void printAddress(DeviceAddress deviceAddress)
{
  for (i = 0; i < 8; i++)
  {
    if (deviceAddress[i] < 16) Serial.print("0");
    Serial.print(deviceAddress[i], HEX);
  }
}

void check_ds18b20(void)
{
  int numberOfDevices = sensors.getDeviceCount();

  // Loop through each device, print out address
  for(i=0;i<numberOfDevices; i++)
  {
    // Search the wire for address
    if(sensors.getAddress(tempDeviceAddress, i))
    {
      Serial.print("Found device ");
      Serial.print(i, DEC);
      Serial.print(" with address: ");
      printAddress(tempDeviceAddress);
      Serial.println();
      
      Serial.print("Setting resolution to ");
      Serial.println(9, DEC);
      
      // set the resolution to TEMPERATURE_PRECISION bit (Each Dallas/Maxim device is capable of several different resolutions)
      sensors.setResolution(tempDeviceAddress, 9);
    }
    else
    {
      Serial.print("Found ghost device at ");
      Serial.print(i, DEC);
      Serial.print(" but could not detect address. Check power and cabling");
    }
  }
}
