import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from http.client import HTTPConnection
from urllib.parse import urlparse

port = int(sys.argv[1])

class myPrx(BaseHTTPRequestHandler):
    request_count = 0
    # def send_response(self, code, message=None):
    #     pass

    def do_GET(self):
        self.__class__.request_count += 1
        print("-----------------------------------------------")
        
        korFlag = False
        imgFlag = False

        if ("korea" in self.path):
            korFlag = True
            parsed_url = urlparse("http://mnet.yonsei.ac.kr/")
        else:
            parsed_url = urlparse(self.path)

        if (parsed_url.query == "image_off"):
            imgFlag = True

        print("%d [%c] Redirected [%c] Image filter" % (self.__class__.request_count, ("O" if korFlag else "X"), ("O" if imgFlag else "X")))

        client_ip, client_port = self.client_address
        print(f"[CLI connected to {client_ip}:{client_port}]")
        print("[CLI ==> PRX --- SRV]")
        print("  > %s" % (self.requestline))
        print("  > %s" % (self.headers['User-Agent'].splitlines()[0]))
        SRV_conn = HTTPConnection(parsed_url.hostname)
        print("[SRV connected to %s:%d]" % (parsed_url.hostname, SRV_conn.port))

        print("[CLI --- PRX ==> SRV]")
        SRV_conn.putrequest('GET', parsed_url.path)
        SRV_conn.putheader('Accept', 'text/html')
        # SRV_conn.putheader('Content-Length', str(0))
        # SRV_conn.putheader("Host", SRV_domain)
        SRV_conn.putheader("Connection", "close")
        SRV_conn.putheader("User-Agent", self.headers['User-Agent'])
        print("  > %s" % (parsed_url.hostname + parsed_url.path))
        print("  > %s" % (self.headers['User-Agent'].splitlines()[0]))
        SRV_conn.endheaders()

        print("[CLI --- PRX <== SRV]")
        try:
            SRV_res = SRV_conn.getresponse()
        except Exception as e:
            print(f"An error occurred: {e}")
        print("  > %s %s" % (SRV_res.status, SRV_res.reason))
        print("  > %s %sbytes" % (SRV_res.headers['Content-Type'], (SRV_res.headers['Content-Length'] if SRV_res.headers['Content-Length'] else "0")))


        notFoundFlag = False
        print("[CLI <== PRX --- SRV]")
        self.path = parsed_url.hostname + parsed_url.path
        if (imgFlag and SRV_res.info().get_content_type() == "image/jpeg"):
            self.send_response_only(404)
            notFoundFlag = True
        else:
            self.send_response_only(SRV_res.status)
        self.send_header('Connection', 'close')
        if (imgFlag):
            self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'none';")
        self.end_headers()
        if (not notFoundFlag):
            self.wfile.write(SRV_res.read())
        else:
            self.wfile.write(b"Not Found")
        print("  > %s %s" % (SRV_res.status, SRV_res.reason))
        print("  > %s %sbytes" % (SRV_res.headers['Content-Type'], (SRV_res.headers['Content-Length'] if SRV_res.headers['Content-Length'] else "0")))

        # self.close_connection = True
        print("[CLI disconnected]")
        SRV_conn.close()
        print("[SRV disconnected]")

try:
    print("Starting proxy server on port %d" % port)
    httpd = HTTPServer(('', port), myPrx)
    httpd.allow_reuse_address = True
    httpd.serve_forever()  
except KeyboardInterrupt:
    httpd.shutdown()