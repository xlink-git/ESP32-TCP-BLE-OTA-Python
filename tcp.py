# author Kwon Taeyoung (xlink69@gmail.com)
# brief TCP OTA
# version 1.0

import socket
import sys

import netifaces
import threading
import os


def get_network_interfaces():
    interfaces = netifaces.interfaces()
    network_info = []

    for interface in interfaces:
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addrs:
            ipv4_info = addrs[netifaces.AF_INET][0]
            ip = ipv4_info['addr']
            if ip != '127.0.0.1':
                network_info.append((interface, ip))

    return network_info


def display_interfaces(interfaces):
    print('(0) Quit')
    for i, (interface, ip) in enumerate(interfaces):
        print(f"({i + 1}) {interface} : {ip}")


def display_targets(targets):
    print('(0) Quit')
    for i, target in targets:
        print(f"({i + 1}) {target}")


def select_interface(interfaces):
    while True:
        try:
            choice = int(input("선택할 인터페이스 번호를 입력하세요: ")) - 1
            if choice == -1:
                print('Quit')
                sys.exit(-1)
            if 0 <= choice < len(interfaces):
                return interfaces[choice]
            else:
                print("유효하지 않은 선택입니다.")
        except ValueError:
            print("숫자를 입력하세요.")


def send_broadcast(udp_socket, ip):
    broadcast_ip = ".".join(ip.split('.')[:-1]) + ".255"
    print(f'Broadcast IP : {broadcast_ip}')
    udp_socket.sendto(b"REQUEST IP", (broadcast_ip, 13333))


# Step 6: 5초 동안 응답 메시지를 받아서 송신한 IP를 리스트로 표시
def receive_responses(udp_socket):
    responses = []
    udp_socket.settimeout(2)

    while True:
        try:
            data, addr = udp_socket.recvfrom(1024)
            responses.append(addr[0])
        except socket.timeout:
            break

    return responses


def connect_tcp(ip):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_socket.connect((ip, 12222))
        print(f'{ip}:12222 에 연결되었습니다')
        return tcp_socket
    except ConnectionRefusedError:
        print("서버에 연결할 수 없습니다.")
    except Exception as e:
        print(f"{ip}:12222 에 연결 중 오류 발생: {e}")
    return None


def send_firmware(tcp_socket, filename):
    print(f'{filename} 파일을 전송합니다')
    with open(filename, "rb") as firmware_file:
        file_len = os.path.getsize(filename)
        data = firmware_file.read(1024)
        tx_len = 0
        while data:
            tcp_socket.send(data)
            tx_len += len(data)
            print('\r %7d / %7d' % (tx_len, file_len), end='')
            data = firmware_file.read(1024)


def check_target(tcp_socket):
    if tcp_socket.send(b'ota') != 3:
        print('\'ota\' 메시지 전송 에러')
        return 'SEND ERROR'
    response = tcp_socket.recv(4)
    if response == b'ACK\0':
        print('\'ACK\' 응답 OK')
        return 'RCV OK'
    print('응답 에러 :', response)
    return 'RCV ERROR : ' + response.decode('utf-8')


def ota_process(firmware_filename):
    interfaces = get_network_interfaces()
    if not interfaces:
        print("사용 가능한 네트워크 인터페이스를 찾을 수 없습니다.")
        return

    print("사용 가능한 네트워크 인터페이스:")
    display_interfaces(interfaces)

    selected_interface = select_interface(interfaces)
    if not selected_interface:
        return

    print(f"선택한 인터페이스: {selected_interface[0]} : {selected_interface[1]}")
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.bind((selected_interface[1], 13333))  # 선택한 인터페이스와 13333 포트로 바인딩
    send_broadcast(udp_socket, selected_interface[1])

    print("브로드캐스트 메시지에 대한 응답을 기다리는 중...")
    responses = receive_responses(udp_socket)

    if not responses:
        print("응답이 없습니다.")
        return

    print("\n응답을 받은 IP 주소 목록:")
    display_targets([ip for ip in enumerate(responses)])

    choice = int(input("연결할 IP 주소를 선택하세요: ")) - 1
    if 0 <= choice < len(responses):
        selected_ip = responses[choice]
        tcp_socket = connect_tcp(selected_ip)
        if tcp_socket:
            ret = check_target(tcp_socket)
            if ret != 'RCV OK':
                print('Target IP check ERROR : ', ret)
                return
            send_firmware(tcp_socket, firmware_filename)
            tcp_socket.close()
            print("\n파일 전송이 완료되었습니다.")
    else:
        print("유효하지 않은 선택입니다.")


