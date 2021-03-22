from http.server import BaseHTTPRequestHandler, HTTPServer   # BaseHTTPRequestHandler used for servicing incoming HTTP requests
import csv
import os
from lightbulb import lightbulb
import datetime
import socket

hostname = socket.gethostname()
host_name = socket.gethostbyname(hostname)   # Change this to your Raspberry Pi IP address. type 'ip -4 address|grep inet' in terminal 192.168.0.25
#host_name = '130.108.226.76'    # Anthony's Testing IP
host_port = 8080

#  Connect to bulb ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
device_address = 'C9:F0:78:8D:F2:F9'  # MAC Address of the Hue Bulb

bulb = lightbulb(device_address)   # store bulb as class lightbulb and pass in the device_address defined above. This argument is passed into the function __init__
bulb.connect()                   # use connect() function inside the class lightbulb

brightness = 0


#Handle History and Ststus File IO ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def writeHistory(status, method, brightness):
    with open('history.csv', 'a', newline='') as f:
        time = datetime.datetime.now() 
        writer = csv.writer(f)
        writer.writerow([time, status, method, brightness])
        
def setBrightness(brightness):
    with open('history.csv', 'a', newline='') as f:
        time = datetime.datetime.now() 
        writer = csv.writer(f)
        writer.writerow([time, status, method, brightness])
        
def getBrightness():
    with open('history.csv', 'r', newline='') as f:
        time = datetime.datetime.now() 
        writer = csv.writer(f)
        writer.writerow([time, status, method, brightness])
        



class server(BaseHTTPRequestHandler):
    """ A special implementation of BaseHTTPRequestHander for reading data from
        and control GPIO of a Raspberry Pi
    """
    #dev = lightbulb(device_address)   # store dev as class Central and pass in the device_address defined above. This argument is passed into the function __init__
    #dev.connect()                   # use connect() function inside the class Central
    
    def defineLocals(self):
        self.brightness = 0
    
    def do_HEAD(self):
        """ do_HEAD() can be tested use curl command 
            'curl -I http://server-ip-address:port' 
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
    def _redirect(self, path):
        self.send_response(303)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()
        
    def do_GET(self):
        """ do_GET() can be tested using curl command 
            'curl http://server-ip-address:port' 
        """
        html = open('html/index.html', 'r').read()
        
        self.do_HEAD()
        
        #  Insert all necessary variable into the HTML
        html = html%(brightness)
        
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])    # Get the size of data
        post_data = self.rfile.read(content_length).decode("utf-8")   # Get the data
        post_data = post_data.split("=")[1]    # Only keep the value
        
        if post_data == 'On':
            current_brightness = bulb.turnOn()
            writeHistory('on', 'application', current_brightness)   
        elif post_data == 'Off': 
            current_brightness = bulb.turnOff()
            writeHistory('off', 'application', current_brightness)  
        else:
            brightness = int(format(post_data))
            bulb.setBrightness(brightness)
            writeHistory('brightness change', 'application', brightness)  # TODO: UnboundLocalError: local variable 'brightness' referenced before assignment
        
        self._redirect('/')
        


if __name__ == '__main__':
    http_server = HTTPServer((host_name, host_port), server)
    print("Server Starts - %s:%s" % (host_name, host_port))

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()
    
     
    
    
    

















