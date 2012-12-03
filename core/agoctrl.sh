#!/bin/bash


case "$1" in
	start)
		for service in /lib/systemd/system/ago*.service
		do
			servicename=$(basename $service)
			systemctl start ${servicename}
		done
		;;
	stop)
		for service in /lib/systemd/system/ago*.service
		do
			servicename=$(basename $service)
			systemctl stop ${servicename}
		done
		;;
	restart)
		for service in /lib/systemd/system/ago*.service
		do
			servicename=$(basename $service)
			systemctl restart ${servicename}
		done
		;;
	enable)
		for service in /lib/systemd/system/ago*.service
		do
			servicename=$(basename $service)
			systemctl enable ${servicename}
		done
		;;
	disable)
		for service in /lib/systemd/system/ago*.service
		do
			servicename=$(basename $service)
			systemctl disable ${servicename}
		done
		;;
	*)
esac


