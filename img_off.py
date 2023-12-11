import socket
import threading
import re

def handle_client(client_socket):
    # 클라이언트로부터 HTTP 요청 받기
    request_data = client_socket.recv(4096)

    # 요청에서 호스트 추출
    host = re.search(rb'Host: (.+?)\r\n', request_data)
    if host:
        remote_host = host.group(1).decode('utf-8')
    else:
        # 호스트가 없으면 기본 값으로 설정
        remote_host = 'www.example.com'

    # 원격 서버에 연결
    remote_server = (remote_host, 80)
    server_socket = socket.create_connection(remote_server)
    server_socket.sendall(request_data)

    # 원격 서버로부터 응답 받기
    response_data = b''
    while True:
        chunk = server_socket.recv(4096)
        if not chunk:
            break
        response_data += chunk

    # 이미지 데이터를 원하는 형식으로 변경
    # 여기에서는 아무 변경 없이 전송
    # 만약 이미지를 조작하려면 해당 부분을 수정
    modified_image_data = response_data

    # 클라이언트에게 HTTP 응답 전송
    client_socket.sendall(modified_image_data)

    # 소켓 닫기
    server_socket.close()
    client_socket.close()

def start_proxy_server():
    proxy_host = '127.0.0.1'
    proxy_port = 8080

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((proxy_host, proxy_port))
    server.listen(5)

    print(f"Proxy server is running on {proxy_host}:{proxy_port}")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")

        # 새로운 스레드에서 클라이언트 요청을 처리
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == '__main__':
    start_proxy_server()
