import qmf.console
import optparse
qmf = qmf.console.Session()
qmf_broker = qmf.addBroker("agocontrol/letmein@localhost")
acl = qmf.getObjects(_class="acl")[0]
result = acl.reloadACLFile()
print result   

