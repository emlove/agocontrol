from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

from uuid import *

class Connector:
    connection = None
    dev_queue = None

    def __init__(self, broker, username, password, queue):
        self.connection = Connection(broker, username=username, password=password, reconnect=True)
	self.connection.open()
        self.dev_queue = queue

    def send_raw_message(self, content):
        try:
            session = self.connection.session()

            replyuuid = str(uuid4())
            sender = session.sender('%s; {create: always, node: {type: topic}}' % self.dev_queue)
            receiver = session.receiver("reply-%s; {create: always, delete: always}" % replyuuid)

            message = Message(content=content)
            message.reply_to = "reply-%s" % replyuuid

            sender.send(message)
        except SendError, e:
		session.close()
		raise e

        try:
            message = receiver.fetch(timeout=3)
	except Empty, e:
		session.close()
		return None
        except ReceiverError, e:
            raise e

	session.close()
        return message

    def get_videoframe(self, uuid):
        content = {}
        content["command"] = "getvideoframe"
        content["uuid"] = uuid

        return self.send_raw_message(content)

    def get_epg(self, uuid):
        content = {}
        content["command"] = "getepg"
        content["uuid"] = uuid

        return self.send_raw_message(content)

    def get_inventory(self):
        content = {}
        content["command"] = "inventory"

        return self.send_raw_message(content)

    def send_command(self, uuid, command, args = None):
        content = {}
        content["uuid"] = uuid
        content["command"] = command
        if args:
            for key in args.iterkeys():
                content[key] = args[key]

        return self.send_raw_message(content)

    def create_room(self, name):
        content = {}
        content["command"] = "setroomname"
        content["name"] = name

        return self.send_raw_message(content)

    def set_room_name(self, uuid, name):
        content = {}
        content["uuid"] = uuid
        content["command"] = "setroomname"
        content["name"] = name

        return self.send_raw_message(content)

    def delete_room(self, uuid):
        content = {}
        content["command"] = "deleteroom"
        content["uuid"] = uuid

        return self.send_raw_message(content)

    def create_scenario(self, map):
        content = {}
        content["command"] = "setscenario" 
        content["scenariomap"] = map

        return self.send_raw_message(content)

    def edit_scenario(self, uuid, map):
        content = {}
        content["command"] = "setscenario" 
        content["scenariomap"] = map
        content["uuid"] = uuid

        return self.send_raw_message(content)               

    def get_scenario(self, uuid):
        content = {}
        content["command"] = "getscenario"
        content["uuid"] = uuid

        return self.send_raw_message(content)

    def delete_scenario(self, uuid):
        content = {}
        content["command"] = "delscenario"
        content["uuid"] = uuid

        return self.send_raw_message(content)

    def set_device_name(self, uuid, devicename):
        content = {}
        content["command"] = "setdevicename"
        content["uuid"] = uuid
        content["name"] = devicename

        return self.send_raw_message(content)

    def set_device_room(self, uuid, deviceroom):
        content = {}
        content["command"] = "setdeviceroom"
        content["uuid"] = uuid
        content["room"] = deviceroom

        return self.send_raw_message(content)

    def create_event(self, eventmap):
        content = {}
        content["command"] = "setevent"
        content["eventmap"] = eventmap

        return self.send_raw_message(content)

    def edit_event(self, uuid, eventmap):
        content = {}
        content["command"] = "setevent"
        content["uuid"] = uuid
        content["eventmap"] = eventmap

        return self.send_raw_message(content)

    def get_event(self, uuid):
        content = {}
        content["command"] = "getevent"
        content["uuid"] = uuid

        return self.send_raw_message(content)

    def delete_event(self, uuid):
        content = {}
        content["command"] = "delevent"
        content["uuid"] = uuid

        return self.send_raw_message(content)
    
    def get_device_environments(self):
        content = {}
        content["command"] = "getdeviceenvironments"
        return self.send_raw_message(content)
    
    def get_graph_data(self, deviceid, env, start, end, freq):
        content = {}
        content["command"] = "getloggergraph"
        content["deviceid"] = deviceid
        content["env"] = env
        content["start"] = start
        content["end"] = end
        content["freq"] = freq
        return self.send_raw_message(content)
