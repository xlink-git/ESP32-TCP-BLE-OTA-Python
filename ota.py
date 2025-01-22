# author Kwon Taeyoung (xlink69@gmail.com)
# brief ESP32 BLE/TCP OTA
# version 1.0

import asyncio
import time

import ble
import tcp


async def main():
    firmware_filename = 'firmware.bin'
    while True:
        print('(0) Quit')
        print('(1) Firmware file :', firmware_filename)
        print('(2) BLE')
        print('(3) WiFi')
        try:
            selection = int(input("사용할 인터페이스 번호를 입력하세요: "))
            if selection == 0:
                break
            elif selection == 1:
                firmware_filename = input('Firmware 파일 이름을 입력하세요: ')
                if firmware_filename == '':
                    firmware_filename = 'firmware.bin'
                    continue
            elif selection == 2:
                if not await ble.scan_connect():
                    break
                await ble.check_ota_response(firmware_filename)
                await asyncio.sleep(2)  # 응답 대기
                if ble.ota_ready:
                    await ble.tx_firmware_file(firmware_filename)
                    await asyncio.sleep(3)
                break

            elif selection == 3:
                tcp.ota_process(firmware_filename)
                break
            else:
                print('알맞은 숫자를 입력하세요\n')
        except ValueError:
            print('숫자를 입력하세요\n')


if __name__ == '__main__':
    asyncio.run(main())

