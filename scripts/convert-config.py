#!/usr/bin/python
import ConfigParser
import agoclient

config = ConfigParser.RawConfigParser()

config.read(agoclient.CONFDIR + '/config.ini')

for section in config.sections():
	# print "Section", section
	newconfig = ConfigParser.RawConfigParser()
	newconfig.add_section(section)
	for option in config.options(section):
		# print "Option: ", option, ":", config.get(section, option)
		newconfig.set(section, option, config.get(section, option))
	with open(agoclient.CONFDIR + '/conf.d/' + section + '.conf', 'wb') as configfile:
		newconfig.write(configfile)

