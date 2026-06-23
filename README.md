# Computer Vision Bionic Hand

A real-time prosthetic hand that mirrors your finger movements using computer vision. A webcam tracks your hand with MediaPipe, maps each finger's curl angle to a servo, and streams those angles to an ESP32 over USB — all at up to 30 Hz.
<img width="754" height="544" alt="image" src="https://github.com/user-attachments/assets/1109187b-d5fc-4e3d-9f74-d5dac1d99240" />


## How It Works

1. A Python script on your PC captures webcam frames and runs MediaPipe hand detection
2. For each of the 5 fingers, it computes a curl angle (0° = open, 180° = fully curled) using the ratio of landmark distances
3. It packages all 5 angles into a compact serial packet and sends it to the ESP32
4. The ESP32 reads the packet, clamps the angles for safety, and drives each servo via PWM

---

## Repository Structure

```
Computer-Vision-Bionic-Hand/
├── CAD/                  # SolidWorks / STL files for the hand structure
├── Electronics/          # Schematic and wiring diagram files
├── Software/
│   ├── hand_tracker.py   # PC-side: camera, MediaPipe, serial output
│   └── esp32_servo.py    # ESP32-side: serial input, servo PWM control
├── BOM.csv               # Full bill of materials
├── References.md         # Finger dimensions and CAD reference specs
└── README.md
```

---

## Hardware

### Bill of Materials

See [`BOM.csv`](BOM.csv) for the full list. Key components:

| Component | Qty |
|---|---|
| ESP32-WROOM-32 | 1 |
| Servo motor (SG90 or MG90S) | 5 |
| Breadboard (half-size or full) | 1 |
| USB cable (data-capable) | 1 |
| Jumper wires | as needed |

### Pin Mapping

| Servo | Finger | ESP32 GPIO |
|---|---|---|
| M1 | Thumb | 25 |
| M2 | Index | 14 |
| M3 | Middle | 19 |
| M4 | Ring | 33 |
| M5 | Pinky | 23 |

### Wiring

Each servo connects with three wires: signal (orange) to the GPIO pin, power (red) to 5V, and ground (black) to GND. All grounds share a common rail on the breadboard.

<!-- [INSERT WIRING DIAGRAM PHOTO OR SCHEMATIC SCREENSHOT HERE — from the Electronics/ folder] -->

---

## CAD

The hand structure was custom-designed with dimensions taken from average human finger measurements. All parts are 3D printable.

| Section | Dimensions (L x W x D) |
|---|---|
| Fingertip | 21.8 mm x 14.7 mm x 16.0 mm |
| Middle phalanx | 26.7 mm x 14.7 mm x 16.0 mm |
| Base phalanx | 30.0 mm x 14.7 mm x 16.0 mm |
| Palm | 120.0 mm x 80.0 mm x 40.0 mm |

Joint holes are 2.7 mm diameter — use a 2.5 mm axle for a clean fit. Fillets are 7 mm on the bottom face and 5 mm on the top.

<!-- [INSERT CAD RENDER OR PRINTED PART PHOTO HERE] -->

---

## Software Setup

### 1. Flash MicroPython onto the ESP32

Download the latest firmware from [micropython.org](https://micropython.org/download/esp32/), then flash it:

```bash
pip install esptool
esptool.py --port COM3 erase_flash
esptool.py --port COM3 --baud 460800 write_flash -z 0x1000 esp32-firmware.bin
```

### 2. Upload the ESP32 script

```bash
pip install mpremote
mpremote connect COM3 cp Software/esp32_servo.py :main.py
```

Or use [Thonny](https://thonny.org/) — open `esp32_servo.py` and save it to the device as `main.py`.

### 3. Install PC dependencies

```bash
pip install opencv-python mediapipe pyserial
```

### 4. Run the hand tracker

```bash
python Software/hand_tracker.py --port COM3
```

Replace `COM3` with your actual port (`/dev/ttyUSB0` on Linux/Mac). Press `Q` to quit.

---

## Calibration

If a servo hits its physical stop before reaching 0° or 180°, tune these constants in `esp32_servo.py`:

```python
DUTY_MIN = 40    # raise this to shift the 0° endpoint up
DUTY_MAX = 115   # lower this to shift the 180° endpoint down
```

The send rate can also be adjusted in `hand_tracker.py`:

```python
SEND_HZ = 30    # reduce if you see serial overrun errors
```

---

## Dependencies

| Library | Where | Purpose |
|---|---|---|
| `opencv-python` | PC | Webcam capture and display |
| `mediapipe` | PC | 21-point hand landmark detection |
| `pyserial` | PC | Serial communication to ESP32 |
| `machine` (built-in) | ESP32 MicroPython | PWM servo control |

---

## References

See [`References.md`](References.md) for finger dimension sources and design notes.

---

## Future Ideas

- Wireless control over WiFi using UDP instead of serial
- Flex sensor feedback for force awareness
- Gesture macros to trigger preset hand positions
- Dual-hand tracking support

---

## License

MIT License. Build on it, improve it, share it.
