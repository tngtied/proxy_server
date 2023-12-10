import sys
import socket
from urllib.parse import urlparse
import threading

port = int(sys.argv[1])
imgFlag = False
request_count = 0

def parse_header(req_lines):
    header = {}
    for line in req_lines:
        header_parts = line.split(": ")
        if (len(header_parts) > 1):
            header[header_parts[0]] = header_parts[1]
    return header


def handle_client(CLI_socket, CLI_addr):
    global imgFlag, request_count
    # if CLI_socket._closed == -1:
    #     print("socket closed")

    CLI_req_headerlines, CLI_req_, CLI_req_body = CLI_socket.recv(4096).partition(b'\r\n\r\n')

    CLI_req_headerlines = CLI_req_headerlines.decode("utf-8").split("\r\n")

    request_count += 1
    print("-----------------------------------------------")

    korFlag = False
    CLI_req_path = CLI_req_headerlines[0].split(' ')[1]

    if ("korea" in CLI_req_path):
        korFlag = True
        parsed_url = urlparse("http://mnet.yonsei.ac.kr/")
    else:
        parsed_url = urlparse(CLI_req_path)

    if (parsed_url.query == "image_off"):
        imgFlag = True
    elif (parsed_url.query == "image_on"):
        imgFlag = False

    print("%d [%c] Redirected [%c] Image filter" % (request_count, ("O" if korFlag else "X"), ("O" if imgFlag else "X")))
    client_ip, client_port = CLI_addr
    print(f"[CLI connected to {client_ip}:{client_port}]")

    CLI_req_header = parse_header(CLI_req_headerlines)
    print("[CLI ==> PRX --- SRV]")
    print("  > %s" % (CLI_req_headerlines[0]))
    print("  > %s" % (CLI_req_header['User-Agent'].splitlines()[0]))


    SRV_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # _, _, SRV_port = socket.getservbyname('http', 'tcp')
    SRV_socket.connect((parsed_url.hostname, 80))
    SRV_addr = SRV_socket.getpeername()
    print(f"[SRV connected to {SRV_addr[0]}:{SRV_addr[1]}]")

    print("[CLI --- PRX ==> SRV]")
    # SRV_req_headers = CLI_req_header
    # SRV_req_headers.pop('Accept-Encoding')
    # SRV_req_headers["Connection"] = "close"
    
    # print("SRV req headers:\n" + str(SRV_req_headers))
    
    SRV_req_headers = {
        "Host" : CLI_req_header["Host"],
        'Accept-Language': CLI_req_header['Accept-Language'],
        'GET' : parsed_url.path,
        "Connection" : "close",
        "User-Agent" : CLI_req_header['User-Agent'],
        'Accept': CLI_req_header['Accept']
    }
    SRV_req_str = f"GET {parsed_url.path} HTTP/1.1\r\n"
    for key, value in SRV_req_headers.items():
        SRV_req_str += f"{key}: {value}\r\n"
    SRV_req_str += "\r\n"

    SRV_socket.sendall(SRV_req_str.encode('utf-8') + CLI_req_ + CLI_req_body)
    print("  > %s" % (parsed_url.hostname + parsed_url.path))
    print("  > %s" % (CLI_req_header['User-Agent'].splitlines()[0]))

    print("[CLI --- PRX <== SRV]")
    SRV_recv = SRV_socket.recv(4096)
    SRV_res_headerlines, _, SRV_recv_body =  SRV_recv.partition(b'\r\n\r\n')

    SRV_res_headerlines = SRV_res_headerlines.decode('utf-8').split("\r\n")
    SRV_res_headers = parse_header(SRV_res_headerlines)

    print("headers received: " + str(SRV_res_headers))

    SRV_res_status = (SRV_res_headerlines[0].split(" ")[1], SRV_res_headerlines[0].split(" ")[2])
    print("  > %s %s" % (SRV_res_status[0], SRV_res_status[1]))
    print("  > %s %sbytes" % (SRV_res_headers['Content-Type'], (len(SRV_recv_body) if SRV_recv_body else "0")))

    notFoundFlag = False
    print("[CLI <== PRX --- SRV]")
    # self.path = parsed_url.geturl()
    if (imgFlag and SRV_res_headers["Content-Type"] == "image/jpeg"):
        CLI_res_status = ('404', 'Not Found')
        CLI_res_str = "HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n".encode("utf-8")
        notFoundFlag = True
    else:
        CLI_res_status = SRV_res_status
        CLI_res_str = SRV_res_headerlines[0]
        CLI_res_header = SRV_res_headers
        CLI_res_header['Connection'] = 'close'
        # CLI_res_header['Content-Length'] = (len(SRV_recv_body) if SRV_recv_body else 0)
        CLI_res_header['Content-Length'] = SRV_res_headers['Content-Length']

        # CLI_re{
        #     'Connection' : 'close',
        #     'Content-Type' : SRV_res_headers['Content-Type'],
        #     'Content-Length' : (len(SRV_recv_body) if SRV_recv_body else "0")
        # }
        if (imgFlag):
            CLI_res_header['Content-Security-Policy'] =  "default-src 'self'; img-src ;"
        for key, value in CLI_res_header.items():
            CLI_res_str += f"{key}: {value}\r\n"
        CLI_res_str += "\r\n"
        CLI_res_str = CLI_res_str.encode("utf-8")
        CLI_res_str += SRV_recv_body
    CLI_socket.send(CLI_res_str)

    # self.send_header('Connection', 'close')
    # if (imgFlag and parsed_url.path.endswith(('.html', '.htm'))):
    #     # self.send_header('Content-Security-Policy', "default-src 'self'; img-src ;")
    #     self.send_header('Content-Type', 'text/html')
    # self.end_headers()
    # if (not notFoundFlag):
    #     self.wfile.write(SRV_res.read())
    print("  > %s %s" % (CLI_res_status[0], CLI_res_status[1]))
    if (not notFoundFlag): 
        print("  > %s %sbytes" % (SRV_res_headers['Content-Type'], (len(SRV_recv_body) if SRV_recv_body else "0")))

    CLI_socket.close()
    print("[CLI disconnected]")
    SRV_socket.close()
    print("[SRV disconnected]")

def run_proxy_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', port)) 
    server.listen(5)
    print("Starting proxy server on port %d" % port)
    while True:
        try: 
            client_socket, addr = server.accept()
            client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_handler.start()
        except KeyboardInterrupt:
            client_socket.close()
            break
    server.close()

if __name__ == '__main__':
    run_proxy_server()