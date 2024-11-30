import paho.mqtt.client as mqtt  # type: ignore
import csv
from datetime import datetime

# Broker MQTT
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/drowsiness/#"

subscribed_vehicles = set()
alert_counts = {}  # Menyimpan jumlah peringatan per kendaraan

# Threshold peringatan
ALERT_THRESHOLD = 3

# Callback ketika berhasil terhubung ke broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Berhasil terhubung ke broker MQTT.")
        client.subscribe(MQTT_TOPIC)
        print(f"Berlangganan ke topik: {MQTT_TOPIC}")
    else:
        print(f"Gagal terhubung ke broker. Kode: {rc}")

# Callback ketika pesan diterima
def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")
    topic = msg.topic
    vehicle_id = topic.split("/")[-1]

    # Cetak kendaraan yang subscribe pertama kali
    if vehicle_id not in subscribed_vehicles:
        subscribed_vehicles.add(vehicle_id)
        print(f"Kendaraan dengan plat {vehicle_id} berhasil subscribe.")

    if "Drowsiness detected!" in payload:
        print(f"[ALERT] Kendaraan dengan Nopol {vehicle_id} mengalami kantuk. Pesan: {payload}")
        
        # Menyimpan data ke CSV
        save_to_csv(vehicle_id, payload)
        
        if vehicle_id in alert_counts:
            alert_counts[vehicle_id] += 1
        else:
            alert_counts[vehicle_id] = 1
        
        if alert_counts[vehicle_id] >= ALERT_THRESHOLD:
            print(f"Pengemudi dengan Nopol {vehicle_id} Ngantuk Berat, Tidak Diizinkan Mengemudi!")
            alert_counts[vehicle_id] = 0

def save_to_csv(vehicle_id, payload):
    # Dapatkan tanggal dan waktu saat ini
    current_time = datetime.now()
    date = current_time.strftime("%Y-%m-%d")
    time = current_time.strftime("%H:%M:%S")
    
    # Nama file CSV
    file_name = "drowsiness_alerts.csv"
    
    # Cek apakah file sudah ada atau belum
    try:
        # Jika file belum ada, kita buat header
        with open(file_name, mode='a', newline='') as file:
            writer = csv.writer(file)
            
            # Menulis header jika file kosong
            if file.tell() == 0:
                writer.writerow(["Date", "Time", "Vehicle ID", "Alert Message"])
            
            # Menulis data baru
            writer.writerow([date, time, vehicle_id, payload])
            
        print(f"Data peringatan disimpan untuk kendaraan {vehicle_id}.")

    except Exception as e:
        print(f"Gagal menyimpan data ke CSV: {e}")

client = mqtt.Client(client_id="AdminMonitor")
client.on_connect = on_connect
client.on_message = on_message

print("Menghubungkan ke broker MQTT...")
client.connect(MQTT_BROKER, MQTT_PORT)

print("Admin sedang mendengarkan pesan...")
client.loop_forever()
