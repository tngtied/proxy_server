import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from http.client import HTTPConnection
from urllib.parse import urlparse

port = int(sys.argv[1])

class myPrx(BaseHTTPRequestHandler):
    request_count = 0

    def do_GET(self):
        self.__class__.request_count += 1
        print("-----------------------------------------------")
        
        korFlag = False
        imgFlag = False

        if ("korea" in self.path):
            korFlag = True
            SRV_path = "http://mnet.yonsei.ac.kr/"
        else:
            SRV_path = self.path
        splitted_path = self.path.split("?")
        if (splitted_path[-1] == "image_off"):
            imgFlag = True
            SRV_path = ""
            for i in range(len(splitted_path) - 1):
                 SRV_path += splitted_path[i]

        print("%d [%c] Redirected [%c] Image filter" % (self.__class__.request_count, ("O" if korFlag else "X"), ("O" if imgFlag else "X")))

        client_ip, client_port = self.client_address
        print(f"[CLI connected to {client_ip}:{client_port}]")
        print("[CLI ==> PRX --- SRV]")
        requestLines = self.requestline.split()
        print("  > %s %s" % (requestLines[0], requestLines[1]))
        print("  > %s" % (self.headers['User-Agent']))

        SRV_domain = SRV_path.split("/")[2]
        SRV_conn = HTTPConnection(SRV_domain, 80)
        print("[SRV connected to %s:%d]" % (SRV_domain, SRV_conn.port))

        print("[CLI --- PRX ==> SRV]")
        SRV_conn.putrequest('GET', SRV_path)
        SRV_conn.putheader('Accept', 'text/html')
        # SRV_conn.putheader('Content-Length', str(0))
        # SRV_conn.putheader("Host", SRV_domain)
        SRV_conn.putheader("Connection", "close")
        SRV_conn.putheader("User-Agent", self.headers['User-Agent'])
        if (imgFlag):
             SRV_conn.putheader('Content-Security-Policy', "default-src 'self'; img-src 'none';")
        print("  > GET %s" % (SRV_path))
        print("  > %s" % (self.headers['User-Agent']))
        SRV_conn.endheaders()

        print("[CLI --- PRX <== SRV]")
        try:
            SRV_res = SRV_conn.getresponse()
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print("getresponse() itself ran")
        print("  > %s %s" % (SRV_res.status, SRV_res.reason))
        print("  > %s %sbytes" % (SRV_res.headers['Content-Type'], SRV_res.headers['Content-Length']))


        print("[CLI <== PRX --- SRV]")
        self.send_response(SRV_res.status)
        self.send_header('Connection', 'close')
        if (imgFlag):
             self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'none';")
        for header, value in SRV_res.getheaders():
            print("header %s, value %s" % (header, value))
            self.send_header(header, value)
        self.end_headers()
        print("  > %s %s" % (SRV_res.status, SRV_res.reason))
        print("  > %s %sbytes" % (SRV_res.headers['Content-Type'], SRV_res.headers['Content-Length']))
        self.wfile.write(SRV_res.read())


        # CLI_conn = HTTPConnection(self.path.split("/")[2], client_port)
        # print("[CLI <== PRX --- SRV]")
        # CLI_conn.
        # CLI_res = CLI_conn.getresponse()
        print("[CLI disconnected]")
        SRV_conn.close()
        print("[SRV disconnected]")

try:

    # server.TCPServer.allow_reuse_address = True   # solution for `OSError: [Errno 98] Address already in use`
    print("Starting proxy server on port %d" % port)
    httpd = HTTPServer(('', port), myPrx)
    httpd.allow_reuse_address = True
    httpd.serve_forever()  
except KeyboardInterrupt:
    httpd.shutdown()