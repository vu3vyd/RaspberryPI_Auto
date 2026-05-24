import serial
import pynmea2

# Use /dev/ttyS0 for most modern PIs; check /dev/serial0 link
ser = serial.Serial('/dev/serial0', 9600, timeout=0.5)

print("Waiting for GPS Lock...")
try:
    while True:
        line = ser.readline().decode('ascii', errors='replace')
        if line.startswith('$GPRMC') or line.startswith('$GPGGA'):
            try:
                msg = pynmea2.parse(line)
                print(f"Timestamp: {msg.timestamp} | Lat: {msg.latitude} | Lon: {msg.longitude}")
            except pynmea2.ParseError:
                continue
except KeyboardInterrupt:
    ser.close()
