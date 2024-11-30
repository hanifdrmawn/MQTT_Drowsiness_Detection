import paho.mqtt.client as mqtt  # type: ignore

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
        
        if vehicle_id in alert_counts:
            alert_counts[vehicle_id] += 1
        else:
            alert_counts[vehicle_id] = 1
        
        if alert_counts[vehicle_id] >= ALERT_THRESHOLD:
            print(f"Pengemudi dengan Nopol {vehicle_id} Ngantuk Berat, Tidak Diizinkan Mengemudi!")
            alert_counts[vehicle_id] = 0

client = mqtt.Client(client_id="AdminMonitor")
client.on_connect = on_connect
client.on_message = on_message

print("Menghubungkan ke broker MQTT...")
client.connect(MQTT_BROKER, MQTT_PORT)

print("Admin sedang mendengarkan pesan...")
client.loop_forever()
