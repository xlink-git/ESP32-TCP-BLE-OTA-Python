# ESP32-TCP-BLE-OTA-Python
Python 으로 만든 PC 용 ESP32 OTA Application (BLE + TCP)

- Author : Kwon Taeyoung (xlink69@gmail.com)
- PyCharm
- Python 3.12
- module : bleak, netifaces
- BLE OTA 는 설정한 UUID 로 스캔하여 접속 후 OTA 진행
- TCP OTA 는 서브넷으로 브로드캐스팅 매시지 전송 후 응답한 IP 리스트 중 선택하여 OTA 진행
- 전송할 파일은 현재 폴더에 있는 경우 이름만, 다른 폴더에 있는 경우는 전체 path 입력
