import requests, json, time, threading
from bismuthclient.bismuthclient import rpcconnections

import tornado.ioloop
import tornado.web

with open('key.secret', 'r') as f: #get yours here: https://developers.google.com/maps/documentation/javascript/marker-clustering
    api_key = f.read()

class ThreadedClient(threading.Thread):
    def __init__(self, updater):
        threading.Thread.__init__(self)

    def run(self):
       while True:
           updater.update()
           print("Waiting 5 minutes")
           time.sleep(360)

class Updater():
    def __init__(self):
        self.data = []
        self.connection = rpcconnections.Connection(("127.0.0.1", 5658))

    def update(self):
        print("Update started")
        self.connection._send("statusjson")
        response = self.connection._receive()

        ips = response['connections_list']

        print("IPs:",ips)

        for ip in ips:
            if ip != "127.0.0.1":
                print(ip)
                coordinates = json.loads(requests.request("GET", f"http://api.ipstack.com/{ip}?access_key={api_key}").text)
                coordinates['ip'] = ip
                if coordinates['latitude'] and coordinates['longitude']:
                    self.data.append(coordinates)

        print("Update finished")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("geo.html", markers=updater.data)

def make_app():

    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/leaflet/(.*)", tornado.web.StaticFileHandler, {"path": "leaflet"}),
    ])

if __name__ == "__main__":
    updater = Updater()
    background = ThreadedClient(updater)
    background.start()

    app = make_app()
    app.listen(5493)
    tornado.ioloop.IOLoop.current().start()


