#!/bin/bash
echo ==== CONFG ====
cat /etc/opt/agocontrol/config.ini | grep -v ^uuid | grep -v ^#
echo ==== PSINF ====
ps auxw | grep ago | grep -v grep
echo ==== QPIDD ====
systemctl status qpidd.service
ps auxw | grep qpid | grep -v grep
sasldblistusers2 -f /etc/qpid/qpidd.sasldb 
ls -l /etc/qpid/qpidd.acl
cat /etc/qpid/qpidd.acl | grep -v ^# | sort -u
echo ==== SYSTD ====
for i in /lib/systemd/system/ago*.service; do systemctl status $(basename $i); done
which dpkg > /dev/null && (
echo ==== PKGLI ====
dpkg -l | grep agoc
dpkg -l | grep qpid
)
echo ==== LSUSB ====
lsusb -v
echo ==== UDEVI ====
grep "/dev" /etc/opt/agocontrol/config.ini | cut -d "=" -f 2 | while read file; do echo "$file" $(udevadm info -q path -n "$file"); done
echo ==== DMESG ====
dmesg
echo ==== SYSLG ====
grep ago /var/log/daemon.log | tac | tail -5000
grep ago /var/log/syslog | tac | tail -5000
