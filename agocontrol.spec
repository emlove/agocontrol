%define version 1.0

Name: agocontrol
Group: Home Automation
Summary: ago control home automation suite
License: GPLv3
Version: %{version}
Release: 2
BuildRequires: gcc-c++ qpid-cpp-client-devel make
Requires: qpid-cpp-client python-qpid qpid-cpp-server systemd PyYAML python-sqlite3dbm
Source0: agocontrol-%{version}.tar.gz

BuildRoot: %{_tmppath}/agocontrol-root

%description
Control your devices from everywhere. Build scenarios and respond to events. ago control allows you to automate many things.

%package -n agocontrol-zwave
Summary: Z-Wave interface driver
Group: Home Automation
Requires: libopenzwave qpid-cpp-client
BuildRequires: libopenzwave-devel

%package -n agocontrol-admin
Summary: Web admin GUI
Group: Home Automation
Requires: python-cherrypy python-qpid python-mako python-simplejson

%description -n agocontrol-zwave
adds support for Zensys Z-Wave devices

%description -n agocontrol-admin
used for device setup and testing

%package -n agocontrol-extras
Summary: Extra devices
Group: Home Automation
Requires: qpid-cpp-client python-qpid

%description -n agocontrol-extras
adds support for additional devices

%prep

%setup -q

%build
make

%install
DESTDIR=${RPM_BUILD_ROOT} make install
mkdir -p ${RPM_BUILD_ROOT}/opt/agocontrol/admin
cp -r admin/* ${RPM_BUILD_ROOT}/opt/agocontrol/admin

%files
%defattr(-,root,root,-)
/opt/agocontrol/bin/agoresolver.py
/opt/agocontrol/bin/inventory.py
/opt/agocontrol/bin/agoevent.py
/opt/agocontrol/bin/agoscenario.py
/lib/systemd
/etc/opt/agocontrol/schema.yaml
/etc/opt/agocontrol/inventory.sql
/etc/opt/agocontrol/config.ini.tpl
/opt/agocontrol/bin/agodrain.py
/opt/agocontrol/bin/agologger.py
/opt/agocontrol/bin/agotimer
/opt/agocontrol/bin/messagesend
/opt/agocontrol/bin/messagesend.py
/opt/agocontrol/bin/boolParser.py

%files -n agocontrol-zwave
/opt/agocontrol/bin/agozwave
/etc/opt/agocontrol/ozw

%files -n agocontrol-admin
/opt/agocontrol/admin

%files -n agocontrol-extras
/opt/agocontrol/bin/agomeloware.py
/opt/agocontrol/bin/agochromoflex
/etc/opt/agocontrol/owfs
/opt/agocontrol/bin/agoowfs.py

%doc

%post
PASSWD=letmein

if ! getent group agocontrol > /dev/null ; then
	echo 'Adding system-group for agocontrol' 1>&2
	groupadd -r agocontrol
fi

if ! getent passwd agocontrol > /dev/null ; then
	echo 'Adding system-user for agocontrol' 1>&2
	adduser --system --home-dir /var/run/agocontrol -g agocontrol -G dialout agocontrol
fi


test -e /etc/opt/agocontrol/config.ini || (
	UUID=$(uuidgen)
	cat /etc/opt/agocontrol/config.ini.tpl | sed "s/<uuid>/${UUID}/" > /etc/opt/agocontrol/config.ini
)

test -e /etc/opt/agocontrol/inventory.db || (
	sqlite3 -init /etc/opt/agocontrol/inventory.sql /etc/opt/agocontrol/inventory.db .quit | tee
)

sasldblistusers2 -f /etc/qpid/qpidd.sasldb  | grep -q agocontrol || (
	echo $PASSWD | saslpasswd2 -c -p -f /etc/qpid/qpidd.sasldb -u QPID agocontrol
)

chown -R agocontrol:agocontrol /etc/opt/agocontrol

%post -n agocontrol-admin
chown -R agocontrol:agocontrol /opt/agocontrol/admin/mod

%changelog
* Thu Oct 29 2012 Harald Klein <hari at vt100.at>
- initial version
