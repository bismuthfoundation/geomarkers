import requests, json, socks
from bisbasic.connections import send, receive

import tornado.ioloop
import tornado.web

with open('key.secret', 'r') as f: #get yours here: https://developers.google.com/maps/documentation/javascript/marker-clustering
    api_key = f.read()

class MainHandler(tornado.web.RequestHandler):
    def get(self):


        s = socks.socksocket()
        s.settimeout(10)
        s.connect(("127.0.0.1", 5658))
        send(s, "statusjson")
        response = receive(s)
        s.close()

        ips = response['connections_list']

        print("IPs:",ips)

        data = []
        for ip in ips:
            if ip != "127.0.0.1":
                print(ip)
                coordinates = json.loads(requests.request("GET", f"http://api.ipstack.com/{ip}?access_key={api_key}").text)
                data.append(coordinates)

        self.render("geo.html", markers=data)

def make_app():

    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/leaflet/(.*)", tornado.web.StaticFileHandler, {"path": "leaflet"}),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(5493)
    tornado.ioloop.IOLoop.current().start()


