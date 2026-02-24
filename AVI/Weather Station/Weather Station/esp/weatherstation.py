import network
import urequests as requests
import time
import ntptime
from machine import Pin, I2C, framebuf
import ssd1306

# --- CONFIGURATION ---
SSID = "Your_WiFi_Name"
PASSWORD = "Your_WiFi_Password"
# Ensure this matches your Laptop's Local IP and Flask Port
BASE_URL = "http://10.201.5.214:5000/api/" 
ROUTES = ["current", "wind", "rain", "forecast"]

# --- HARDWARE SETUP ---
# I2C for OLED
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# External Digital Touch Sensors
# SIG wired to 14 (Home) and 12 (Next)
home_sensor = Pin(14, Pin.IN)
next_sensor = Pin(12, Pin.IN)

# --- ICON BITMAPS (16x16) ---
sun_fb = framebuf.FrameBuffer(bytearray([0x01, 0x80, 0x21, 0x84, 0x41, 0x82, 0x0f, 0xf0, 0x1f, 0xf8, 0x3f, 0xfc, 0x3f, 0xfc, 0x3f, 0xfc, 0x3f, 0xfc, 0x1f, 0xf8, 0x0f, 0xf0, 0x41, 0x82, 0x21, 0x84, 0x01, 0x80, 0x00, 0x00, 0x00, 0x00]), 16, 16, framebuf.MONO_HLSB)
cloud_fb = framebuf.FrameBuffer(bytearray([0x00, 0x00, 0x00, 0x00, 0x06, 0x00, 0x0f, 0x80, 0x1f, 0xc0, 0x1f, 0xe0, 0x7f, 0xf0, 0xff, 0xf8, 0xff, 0xfc, 0xff, 0xfe, 0xff, 0xfe, 0xff, 0xfe, 0x7f, 0xfc, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]), 16, 16, framebuf.MONO_HLSB)
rain_fb = framebuf.FrameBuffer(bytearray([0x06, 0x00, 0x0f, 0x80, 0x1f, 0xc0, 0x7f, 0xf0, 0xff, 0xf8, 0xff, 0xfc, 0x7f, 0xfc, 0x00, 0x00, 0x22, 0x22, 0x44, 0x44, 0x22, 0x22, 0x44, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]), 16, 16, framebuf.MONO_HLSB)

# --- GLOBAL STATE ---
route_index = -1  # -1 is Home, 0-3 are API routes
last_api_fetch = 0
cached_data = None

def connect_wifi():
    oled.fill(0)
    oled.text("WiFi Connecting", 0, 20)
    oled.show()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    timeout = 0
    while not wlan.isconnected() and timeout < 15:
        time.sleep(1)
        timeout += 1
    
    if wlan.isconnected():
        try:
            ntptime.settime() # Syncs ESP32 clock to global time
        except:
            pass
    else:
        oled.text("Failed!", 0, 35)
        oled.show()

def get_api_data(route):
    try:
        res = requests.get(BASE_URL + route)
        data = res.json()
        res.close()
        return data
    except:
        return None

def update_display():
    global cached_data, last_api_fetch
    oled.fill(0)
    
    # Calculate IST Time (UTC + 5:30 = 19800 seconds)
    t = time.localtime(time.time() + 19800)
    
    # 1. HOME SCREEN LOGIC
    if route_index == -1:
        # Update data every 2 minutes (120s)
        if time.time() - last_api_fetch > 120 or cached_data is None:
            cached_data = get_api_data("current")
            last_api_fetch = time.time()
        
        # Draw Time Header
        oled.text(f"{t[3]:02d}:{t[4]:02d}", 5, 5)
        oled.text(f"{t[2]}/{t[1]}", 60, 5)
        oled.hline(0, 18, 128, 1)
        
        if cached_data:
            # Weather Icon Logic
            code = cached_data.get('weather:', '').lower()
            if "clear" in code: oled.blit(sun_fb, 105, 1)
            elif "rain" in code or "drizzle" in code: oled.blit(rain_fb, 105, 1)
            else: oled.blit(cloud_fb, 105, 1)
            
            # Weather Content
            oled.text(f"Temp: {cached_data['temp']}", 5, 30)
            oled.text(f"Humi: {cached_data['humidity']}", 5, 45)
            oled.text(code[:15], 5, 56)
        else:
            oled.text("Offline Data", 5, 35)

    # 2. API PAGES LOGIC
    else:
        curr_route = ROUTES[route_index]
        data = get_api_data(curr_route)
        
        oled.text(f"PAGE: {curr_route.upper()}", 0, 0)
        oled.hline(0, 12, 128, 1)
        
        if data:
            # Extracts values from your Flask JSON dynamically
            vals = list(data.values())
            keys = list(data.keys())
            oled.text(f"{keys[0]}:", 0, 25)
            oled.text(str(vals[0]), 0, 35)
            if len(vals) > 1:
                oled.text(f"{keys[1]}:", 0, 48)
                oled.text(str(vals[1]), 0, 56)
        else:
            oled.text("Error Fetching", 0, 35)

    oled.show()

# --- EXECUTION ---
connect_wifi()
update_display()

while True:
    # Sensor Handling
    if home_sensor.value() == 1:
        route_index = -1
        update_display()
        time.sleep(0.4) # Debounce
        
    if next_sensor.value() == 1:
        route_index = (route_index + 1) % len(ROUTES)
        update_display()
        time.sleep(0.4) # Debounce

    # Passive Update Logic
    # If on Home, refresh every 10s to keep clock ticking
    # If on data page, stay until button press
    if route_index == -1:
        update_display()
        time.sleep(10)
    else:
        time.sleep(0.1)