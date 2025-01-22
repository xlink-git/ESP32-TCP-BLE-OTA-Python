# author Kwon Taeyoung (xlink69@gmail.com)
# brief BLE OTA
# version 1.0

import asyncio
import os
import time
import json

from bleak import BleakScanner, BleakClient

ota_ready = False
# NORDIC_UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
# NORDIC_UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
# NORDIC_UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
TARGET_UUIDS = [
    "6e400001-b5a3-f393-e0a9-e50e24dcca9e",     # Nordic UART Service
    "0000ffe0-0000-1000-8000-00805f9b34fb"      # 16비트 UUID FFE0 확장
]

search_keywords = ["esp32", "esp32s3"]
client = BleakClient("")
notify_characteristic = None
write_characteristic = None


def on_disconnect(_client):
    print(f"Client with address {_client.address} got disconnected!")
    # for task in asyncio.all_tasks():
    #     task.cancel()


def notification_handler(sender, data: bytearray):
    global ota_ready
    print("Received data: ", data)
    rcvutf8 = data[:-1].decode('utf-8')
    json_response = json.loads(rcvutf8)
    if json_response['ota'] == 'ready':
        ota_ready = True
        print('OTA ready received')
    else:
        print(f'OTA status : {json_response['ota']}')


async def scan_connect():
    global client, ota_ready, write_characteristic, notify_characteristic
    ota_ready = False
    print('BLE device scanning for 5 seconds...')
    devices = await BleakScanner.discover(timeout=5)
    target_devices = []

    # 타겟 UUID를 가진 디바이스 필터링 (대소문자 무시)
    for device in devices:
        device_uuids = [uuid.lower() for uuid in device.metadata.get("uuids", [])]
        if any(uuid in device_uuids for uuid in TARGET_UUIDS):
            target_devices.append(device)

    if target_devices:
        if len(target_devices) > 1:
            for i, device in enumerate(target_devices):
                print(f"{i + 1}: {device.name} - {device.address}")

            choice = int(input("Select device number: ")) - 1
        else:
            choice = 0

        address = target_devices[choice].address
        name = target_devices[choice].name

        client = BleakClient(address, disconnected_callback=on_disconnect)
        print(f'connecting to {name}...')
        connected = await client.connect(timeout=5)
        if connected:
            print(f'Connected to {name}')

            # 모든 서비스와 캐릭터리스틱 탐색
            services = await client.get_services()
            write_characteristic = None
            notify_characteristic = None

            for service in services:
                print(f"Service: {service.uuid}")
                for characteristic in service.characteristics:
                    print(f"  Characteristic: {characteristic.uuid}, Properties: {characteristic.properties}")
                    if 'write' in characteristic.properties:
                        write_characteristic = characteristic.uuid
                    if 'notify' in characteristic.properties:
                        notify_characteristic = characteristic.uuid

            if not write_characteristic:
                print("No writable characteristic found.")
                return False

            if not notify_characteristic:
                print("No notify characteristic found.")
                return False

            await client.start_notify(notify_characteristic, notification_handler)
            return True
        else:
            print("Failed to connect.")
            return False
    else:
        print("No devices found")
        return False


async def check_ota_response(ota_filename):
    global client
    ota_message = {}
    ota_message.setdefault('ota', 'start')
    ota_message.setdefault('ota size', os.path.getsize(ota_filename))
    asc = json.dumps(ota_message, indent=4, ensure_ascii=False).encode('ascii')
    asc += b'\x04'
    await client.write_gatt_char(write_characteristic, asc)


async def tx_firmware_file(ota_filename):
    with open(ota_filename, "rb") as firmware_file:
        file_len = os.path.getsize(ota_filename)
        data = firmware_file.read(247)
        tx_len = 0
        while data:
            await client.write_gatt_char(write_characteristic, data)
            tx_len += len(data)
            print('\r %7d / %7d' % (tx_len, file_len), end='')
            data = firmware_file.read(247)
        print("\n파일 전송이 완료되었습니다.")


async def disconnect():
    global client
    print('Disconnecting...')
    # await client.stop_notify(NORDIC_UART_TX_CHAR_UUID)
    await client.disconnect()
