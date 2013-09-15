#!/usr/bin/python
import ConfigParser

config = ConfigParser.RawConfigParser()

config.read('/etc/opt/agocontrol/config.ini')

for section in config.sections():
	# print "Section", section
	newconfig = ConfigParser.RawConfigParser()
	newconfig.add_section(section)
	for option in config.options(section):
		# print "Option: ", option, ":", config.get(section, option)
		newconfig.set(section, option, config.get(section, option))
	with open('/etc/opt/agocontrol/conf.d/' + section + '.conf', 'wb') as configfile:
		newconfig.write(configfile)

