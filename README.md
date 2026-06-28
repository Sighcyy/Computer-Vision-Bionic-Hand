# Computer Vision Bionic Hand

A real-time bionic hand that mimics your finger movements using computer vision. The mechanical hand is fully 3D printed with a tendon-driven finger system, actuated by 5 SG90 servos and controlled by an ESP32 that receives live finger angles from a MediaPipe hand tracker running on a PC.

<img width="754" height="544" alt="image" src="https://github.com/user-attachments/assets/3fefaef2-0e09-47c2-b047-8215830e974d" />

---

## How It Works

The hand is built around a **tendon-and-return mechanism** — the same principle used in real prosthetic hands. Fishing line runs from each servo horn, through guides along the finger, and anchors at the fingertip. When a servo rotates, it pulls the tendon and curls the finger. Rubber bands on the dorsal (back) side act as passive return springs, extending the finger when the servo releases tension.

On the sensing side, a Python script on your PC uses MediaPipe to track 21 landmarks on your hand in real time. For each finger it computes a curl angle from the ratio of joint distances, then streams all 5 angles to the ESP32 over USB serial at up to 30 Hz. The ESP32 converts each angle to a PWM duty cycle and drives the corresponding servo instantly.

---

## Repository Structure

```
Computer-Vision-Bionic-Hand/
├── CAD/                  # SolidWorks / STL files for all printed parts
├── Electronics/          # Schematic and wiring diagram
├── Software/
│   ├── hand_tracker.py   # PC-side: camera, MediaPipe, serial output
│   └── esp32_servo.py    # ESP32-side: serial input, servo PWM control
├── BOM.csv               # Full bill of materials with links
├── References.md         # Finger dimension sources and design notes
└── README.md
```

---

## Mechanical Design

### Finger Architecture

Each finger is made of three printed phalanx segments (fingertip, middle, and base) connected by pin joints. The joints use 2.5 mm stainless steel rod sections as axles, pressed through 2.7 mm clearance holes in the hinge ears. This gives smooth, low-friction rotation while keeping the joint tight enough to hold position under load.

<!-- [INSERT CAD RENDER OR EXPLODED VIEW HERE] -->

| Segment | Length x Width x Depth |
|---|---|
| Fingertip phalanx | 21.8 mm x 14.7 mm x 16.0 mm |
| Middle phalanx | 26.7 mm x 14.7 mm x 16.0 mm |
| Base phalanx | 30.0 mm x 14.7 mm x 16.0 mm |
| Palm | 120.0 mm x 80.0 mm x 40.0 mm |

Fillets are 7 mm on the bottom face and 5 mm on the top to reduce stress concentrations at the joint roots and improve print layer adhesion in those areas.

### Tendon Routing

Clear fishing line is used as the tendon for each finger. It runs from a small anchor point on the servo horn, along the palmar (front) face of the finger through printed routing guides, and ties off at the distal phalanx. Keeping the line close to the bone centerline minimizes lateral forces on the joints during actuation.

### Return Mechanism

Rubber bands are stretched across the dorsal (back) side of each finger between the fingertip and the base phalanx. They provide passive extension — when the servo releases tension on the tendon, the rubber band pulls the finger back to its open position. Band tension needs to be matched to servo torque; too tight and the servo struggles to close, too loose and the finger won't fully extend.

### 3D Printing Notes

All parts are printed in PLA. Recommended settings:

| Setting | Value |
|---|---|
| Layer height | 0.2 mm |
| Infill | 40% or higher for phalanges |
| Supports | Required for hinge ears and palm servo mounts |
| Material | PLA 1.75 mm |

Print the phalanges with the hinge ears oriented vertically to maximize layer strength across the joint pin holes.

---

## Electronics

### Bill of Materials

Full cost breakdown is in [`BOM.csv`](BOM.csv). Total build cost: **$62.73**

| Component | Vendor | Cost | Link |
|---|---|---|---|
| ESP32-WROOM-32 | Amazon | $16.79 | [Buy](https://www.amazon.com/ESP-WROOM-32-Development-Microcontroller-Integrated-Compatible/dp/B08D5ZD528) |
| SG90 Micro Servo Motor (x5) | Amazon | $7.99 | [Buy](https://www.amazon.com/Dorhea-Arduino-Helicopter-Airplane-Walking/dp/B07Q6JGWNV) |
| MB102 Breadboard Power Supply Module | Amazon | $8.99 | [Buy](https://www.amazon.com/ALAMSCN-Solderless-Breadboard-Battery-Arduino/dp/B08JYPMCZY) |
| PLA 1.75mm 3D Printer Filament | Amazon | $9.99 | [Buy](https://www.amazon.com/Filament-Dimensional-Accuracy-Clogging-Cardboard/dp/B0DCJR8JTG) |
| 304 Stainless Steel Round Rods (5 pcs) | Amazon | $6.99 | [Buy](https://www.amazon.com/MECCANIXITY-Stainless-Steel-Round-Various/dp/B0CZRWNXJ1) |
| Rubber Bands (assorted) | Amazon | $7.99 | [Buy](https://www.amazon.com/Rubber-Assorted-Elastic-Tactical-supplies/dp/B0DNZ8GTGF) |
| Clear Fishing Line | Amazon | $3.99 | [Buy](https://www.amazon.com/Switches-Mechanical-Keyboards-Mounted-MX1AE1NN/dp/B09ZST8WMF) |

### Power Supply

The MB102 breadboard power supply module is critical to stable servo operation. Five SG90 servos can draw over 500 mA combined when under load — well beyond what the ESP32's onboard regulator or a USB port alone can reliably supply. The MB102 plugs directly into the breadboard's power rails and accepts 7–12V DC input (or USB) and outputs a clean regulated 5V line.

**Before wiring anything:** set the MB102's voltage selection jumper to 5V. Leaving it at 3.3V will underpower the servos and cause erratic movement or no movement at all.

### Pin Mapping

| Servo | Finger | ESP32 GPIO |
|---|---|---|
| M1 | Thumb | 25 |
| M2 | Index | 14 |
| M3 | Middle | 19 |
| M4 | Ring | 33 |
| M5 | Pinky | 23 |

### Wiring

Each servo has three wires: the signal wire (orange) connects to the assigned ESP32 GPIO pin, the power wire (red) connects to the MB102's 5V rail, and the ground wire (brown/black) connects to the shared GND rail on the breadboard. The ESP32 ground must also connect to this same GND rail so the logic and power grounds are referenced together — without a common ground, the PWM signals will be unreliable.

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

### Servo endpoints

If a servo pulls the tendon too far and jams the joint, or doesn't pull far enough to fully curl the finger, adjust the PWM duty cycle limits in `esp32_servo.py`:

```python
DUTY_MIN = 40    # raise this to shift the 0° endpoint up
DUTY_MAX = 115   # lower this to shift the 180° endpoint down
```

### Tendon tension

Anchor the fishing line with the finger in its natural open position and the servo at 90°. This ensures the servo has equal range in both directions and the tendon doesn't go slack or over-tension at the extremes.

### Rubber band stiffness

If the finger lags behind the servo on the return stroke, the rubber band is too loose — add a second band or use a stiffer one. If the servo struggles to close against the band, switch to a lighter band or shorten the anchor point.

---

## References

See [`References.md`](References.md) for finger dimension sources and design notes.

---

## Future Ideas

- Wireless control over WiFi using UDP to remove the USB tether
- Flex sensors on the arm for force feedback
- Stronger MG90S metal-gear servos for higher grip force
- Wrist rotation as a 6th axis
- Gesture macros to lock preset hand positions


