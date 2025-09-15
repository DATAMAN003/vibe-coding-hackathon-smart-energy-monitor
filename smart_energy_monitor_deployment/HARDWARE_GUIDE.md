# DIY Current Sensor Hardware Guide

## Shopping List (Total cost: ~$30-50)

### Essential Components:
1. **Current Transformers (CTs)** - $8-12 each
   - SCT-013-030 (30A max) or SCT-013-100 (100A max)
   - Non-invasive clamp-on type
   - 3.5mm jack output
   - Buy 2-4 depending on circuits you want to monitor

2. **MCP3008 ADC Chip** - $3-5
   - 8-channel 10-bit ADC
   - SPI interface for Raspberry Pi
   - Handles 0-3.3V input range

3. **Burden Resistors** - $2
   - 33Ω resistors (for SCT-013-030)
   - Or 22Ω resistors (for SCT-013-100)
   - 1/4W rating is fine

4. **Voltage Divider Resistors** - $2
   - 10kΩ resistors (2 per CT sensor)
   - Creates 1.65V bias point

5. **Capacitors** - $2
   - 10μF electrolytic capacitors
   - Filters noise from CT sensors

6. **Breadboard/Perfboard** - $3-5
   - For prototyping the circuit

7. **3.5mm Jack Sockets** - $5
   - To connect CT sensors
   - Panel mount type preferred

8. **Jumper Wires** - $3
   - Male-to-female for Pi connections

## Circuit Diagram

```
CT Sensor → 3.5mm Jack → Burden Resistor → Voltage Divider → ADC → Raspberry Pi

For each CT sensor:

CT Sensor (3.5mm plug)
    |
    ├─ Tip: Signal
    └─ Sleeve: Ground
    
Signal ──[33Ω Burden]── ADC Input
    |                      |
    ├─[10kΩ]─── 3.3V      |
    |                      |
    └─[10kΩ]─── GND ──[10μF]── GND
         |
      1.65V bias
```

## Wiring to Raspberry Pi

### MCP3008 to Pi (SPI):
```
MCP3008 Pin  →  Pi Pin
VDD (16)     →  3.3V (Pin 1)
VREF (15)    →  3.3V (Pin 1)  
AGND (14)    →  GND (Pin 6)
CLK (13)     →  SCLK (Pin 23)
DOUT (12)    →  MISO (Pin 21)
DIN (11)     →  MOSI (Pin 19)
CS (10)      →  CE0 (Pin 24)
DGND (9)     →  GND (Pin 6)
```

### CT Sensors to MCP3008:
```
CT Sensor 1  →  CH0 (Pin 1)
CT Sensor 2  →  CH1 (Pin 2)
CT Sensor 3  →  CH2 (Pin 3)
CT Sensor 4  →  CH3 (Pin 4)
```

## Installation Steps

### 1. Enable SPI on Raspberry Pi
```bash
sudo raspi-config
# Navigate to: Interface Options → SPI → Enable
sudo reboot
```

### 2. Install SPI Library
```bash
pip install spidev
```

### 3. Build the Circuit
1. Connect MCP3008 to breadboard
2. Wire MCP3008 to Pi using SPI connections above
3. For each CT sensor:
   - Connect 3.5mm jack
   - Add burden resistor between signal and ADC input
   - Add voltage divider (two 10kΩ resistors)
   - Add filter capacitor
   - Connect to MCP3008 channel

### 4. Install CT Sensors
1. **SAFETY FIRST**: Turn off circuit breaker before installation
2. Clamp CT around ONE wire only (not both hot and neutral)
3. For 240V circuits, clamp around the hot wire
4. For 120V circuits, clamp around the hot wire
5. Arrow on CT should point toward the load (away from breaker)

## Calibration Process

1. **Test without load**:
```bash
python hardware_interface.py
```
Should read near 0W for all sensors

2. **Calibrate with known load**:
```bash
python hardware_interface.py
# Follow prompts to calibrate each sensor
```

3. **Update config.py** with calibration factors

## Safety Notes

⚠️ **ELECTRICAL SAFETY**:
- Turn off breakers when installing CTs
- CTs are non-invasive but still work with live wires
- Never open electrical panels if you're not qualified
- Consider hiring an electrician for panel installations
- Test with extension cords first for safety

⚠️ **CT Sensor Safety**:
- Never disconnect CT secondary while primary has current
- This can create dangerous high voltages
- Always short CT secondary when not connected to burden resistor

## Troubleshooting

**No readings**: Check SPI connections and enable SPI interface
**Negative readings**: Flip CT sensor direction (arrow toward load)
**Noisy readings**: Add more filtering capacitors
**Inaccurate readings**: Recalibrate with known loads

## Advanced Features

Once basic monitoring works, you can add:
- Voltage sensing for real power calculation
- Multiple phases for 240V appliances  
- Wireless sensor nodes using ESP32
- Current transformers on individual outlets
- Integration with home automation systems