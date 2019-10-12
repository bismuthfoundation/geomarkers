import requests, json, socks
from bismuthclient.bismuthclient import rpcconnections

import tornado.ioloop
import tornado.web

with open('key.secret', 'r') as f: #get yours here: https://developers.google.com/maps/documentation/javascript/marker-clustering
    api_key = f.read()

class MainHandler(tornado.web.RequestHandler):
    def get(self):

        connection._send("statusjson")
        response = connection._receive()

        ips = response['connections_list']

        print("IPs:",ips)

        data = []
        for ip in ips:
            if ip != "127.0.0.1":
                print(ip)
                coordinates = json.loads(requests.request("GET", f"http://api.ipstack.com/{ip}?access_key={api_key}").text)
                if coordinates['latitude'] and coordinates['longitude']:
                    data.append(coordinates)

        self.render("geo.html", markers=data)

def make_app():

    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/leaflet/(.*)", tornado.web.StaticFileHandler, {"path": "leaflet"}),
    ])

if __name__ == "__main__":
    connection = rpcconnections.Connection(("127.0.0.1", 5658))
    app = make_app()
    app.listen(5493)
    tornado.ioloop.IOLoop.current().start()


