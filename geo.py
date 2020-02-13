import requests, json, time, threading
from bismuthclient.bismuthclient import rpcconnections

import tornado.ioloop
import tornado.web
import requests

with open('key.secret', 'r') as f: #get yours here: https://developers.google.com/maps/documentation/javascript/marker-clustering
    api_key = f.read()

def present(list_of_dicts, ip):
    for d in list_of_dicts:
        if d["ip"] == ip:
            return True
    else:
        return False

def get_hns():
    try:
        raw = requests.get("https://hypernodes.bismuth.live/mn_status.json")
        hns = json.loads(raw.text)
        print(hns)

        filtered = []
        for hn in hns:
            if hn["status"] == "ENABLED":
                filtered.append(hn)
        return filtered
    except:
        print("Unable to list Hypernodes")
        raise

def randomize(value, list_of_values):
    while value in list_of_values:
        print(f"Randomizing position of {value}")
        value = str(float(value) + 0.001)
        print(value)

    list_of_values.append(value)

    return value

class ThreadedClient(threading.Thread):
    def __init__(self, updater):
        threading.Thread.__init__(self)

    def run(self):
       while True:
           updater.update()
           updater.clean()
           print("Waiting one hour")
           time.sleep(3600)

class Updater():
    def __init__(self):
        self.data_nodes = []
        self.data_hns = []
        self.long_list = []
        self.lat_list = []

    def clean(self):
        for key in self.data_nodes:
            if time.time() - int(key['added']) > 86400:
                self.data_nodes.remove(key)
                self.long_list.remove(key["longitude"])
                self.lat_list.remove(key["latitude"])
                print(f"Removed {key}")

        for key in self.data_hns:
            if time.time() - int(key['added']) > 86400:
                self.data_hns.remove(key)
                self.long_list.remove(key["longitude"])
                self.lat_list.remove(key["latitude"])
                print(f"Removed {key}")

    def update(self):
        self.connection = rpcconnections.Connection(("127.0.0.1", 5658))
        print("Update started")
        self.connection._send("statusjson")
        response = self.connection._receive()

        ips = response['connections_list']
        hns = get_hns()

        print("IPs:", ips)

        for ip in ips:
            if ip != "127.0.0.1" and not present(self.data_nodes, ip):
                print(ip)
                coordinates = json.loads(requests.request("GET", f"http://api.ipstack.com/{ip}?access_key={api_key}").text)
                coordinates['ip'] = ip
                coordinates['added'] = time.time()

                if coordinates['latitude'] and coordinates['longitude']:
                    coordinates['latitude'] = randomize(coordinates['latitude'], self.lat_list)
                    coordinates['longitude'] = randomize(coordinates['longitude'], self.long_list)
                    self.data_nodes.append(coordinates)

        for hypernode in hns:
            hn_ip = hypernode["ip"]
            if hn_ip != "127.0.0.1" and not present(self.data_hns, hn_ip):
                print(hn_ip)
                coordinates = json.loads(requests.request("GET", f"http://api.ipstack.com/{hn_ip}?access_key={api_key}").text)
                coordinates['ip'] = hn_ip
                coordinates['added'] = time.time()

                if coordinates['latitude'] and coordinates['longitude']:
                    coordinates['latitude'] = randomize(coordinates['latitude'], self.lat_list)
                    coordinates['longitude'] = randomize(coordinates['longitude'], self.long_list)
                    self.data_hns.append(coordinates)


        print("Update finished")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("geo.html", nodes=updater.data_nodes, hypernodes=updater.data_hns)

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


