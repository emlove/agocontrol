import squeezeboxserver
import time

squeezebox = squeezeboxserver.SqueezeboxServer("192.168.1.65:9000")

players = squeezebox.players()

for p in players:
    print ("MAC: %s" % p['playerid'])

time.sleep(10)
squeezebox.power("00:04:20:06:8c:55", "on")
squeezebox.playlist("00:04:20:06:8c:55", "play")
time.sleep(10)
squeezebox.playlist("00:04:20:06:8c:55", "stop")
time.sleep(3)
squeezebox.power("00:04:20:06:8c:55", "off")
