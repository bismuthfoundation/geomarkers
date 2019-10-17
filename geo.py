import requests, json, time, threading
from bismuthclient.bismuthclient import rpcconnections

import tornado.ioloop
import tornado.web

with open('key.secret', 'r') as f: #get yours here: https://developers.google.com/maps/documentation/javascript/marker-clustering
    api_key = f.read()

def present(list_of_dicts, ip):
    for d in list_of_dicts:
        if d["ip"] == ip:
            return True
    else:
        return False

class ThreadedClient(threading.Thread):
    def __init__(self, updater):
        threading.Thread.__init__(self)

    def run(self):
       while True:
           updater.update()
           updater.clean()
           print("Waiting 5 minutes")
           time.sleep(360)

class Updater():
    def __init__(self):
        self.data = []

    def clean(self):
        for key in self.data:
            if time.time() - int(key['added']) > 86400:
                self.data.remove(key)
                print(f"Removed {key}")

    def update(self):
        self.connection = rpcconnections.Connection(("127.0.0.1", 5658))
        print("Update started")
        self.connection._send("statusjson")
        response = self.connection._receive()

        ips = response['connections_list']

        print("IPs:",ips)

        for ip in ips:
            if ip != "127.0.0.1" and not present(self.data, ip):
                print(ip)
                coordinates = json.loads(requests.request("GET", f"http://api.ipstack.com/{ip}?access_key={api_key}").text)
                coordinates['ip'] = ip
                coordinates['added'] = time.time()

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


