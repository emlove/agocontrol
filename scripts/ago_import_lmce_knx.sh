#!/bin/bash
# import knx devices from LinuxMCE into AgoControl
# (c) Serge Wagener 2013 (foxi352)
#

# AgoControl files
XML_File=/etc/opt/agocontrol/knx/devices.xml
AGODB=/etc/opt/agocontrol/db/inventory.db

# LinuxMCE database access
#
# On your LinuxMCE installation launch the following two commande from shell:
#  mysql -u root -e "CREATE USER 'agocontrol'@'%' IDENTIFIED BY  'agopass';"
#  mysql -u root -e "GRANT SELECT ON * . * TO  'agocontrol'@'%';"

MySqlHost=192.168.80.1
MySqlDB=pluto_main
MySqlUser=agocontrol
MySqlPasswd=agopass

if [[ -n "$MySqlPasswd" ]]; then
	PassParm="-p$MySqlPasswd"
fi

# LinuxMCE hardcoded
DT_EIB=49
DT_KNX=2195
DT_Light_OnOff=37
DT_Light_Dimmer=38
DT_Light_RGB=1993
DT_Drapes=68
DT_Thermometer=1744
DT_WallOutlet=1897
DD_FloorplanObjectType=11
DD_Channel=12

#
# Functions
#

# Get installation ID
LMCE_GetInstallationID()
{
	qry="SELECT PK_Installation FROM Installation LIMIT 1;"
	InstallationID=$($mysql_cmd "use $MySqlDB; $qry;" )
}

# Get ID of LinuxMCE KNX device
LMCE_GetKNXDeviceID()
{
	qry="SELECT PK_Device FROM Device WHERE (FK_DeviceTemplate=$DT_EIB OR FK_DeviceTemplate=$DT_KNX) AND FK_Installation=$InstallationID ORDER BY Description ASC"
	KNXDeviceID=$($mysql_cmd "use $MySqlDB; $qry;")
}

# Get UUID of room if exists, or create room if missing in AgoControl database
AGO_GetOrCreateRoom()
{
	RoomUUID=
	RoomUUID=$($sqlite $AGODB "SELECT uuid FROM rooms WHERE name='$1' LIMIT 1")
	if [[ -z "$RoomUUID" ]]; then	
		RoomUUID=$($uuidgen)
		$sqlite $AGODB "INSERT INTO rooms VALUES('$RoomUUID','$1',NULL);"
	fi
	echo $RoomUUID
}

# Get UUID of device if exists, or create device if missing in AgoControl database
AGO_GetOrCreateDevice()
{
	DeviceUUID=
	DeviceUUID=$($sqlite $AGODB "SELECT uuid FROM devices WHERE name='$1' LIMIT 1")
	if [[ -z "$DeviceUUID" ]]; then	
		DeviceUUID=$($uuidgen)
		$sqlite $AGODB "INSERT INTO devices VALUES('$DeviceUUID','$1','$2');"
	fi
	echo $DeviceUUID
}

# Import lights (on/off, dimmers and rgb)
ImportLights()
{
	echo "Importing lights"
	array=()
	
	qry="SELECT Device.PK_Device, Device.Description, Device.FK_DeviceTemplate, DD12.IK_DeviceData, Room.Description AS room \
	FROM Device \
	INNER JOIN DeviceTemplate ON FK_DeviceTemplate=PK_DeviceTemplate \
	LEFT JOIN Device_DeviceData AS DD12 ON DD12.FK_Device=PK_Device \
	LEFT JOIN Device_DeviceData AS DD11 ON DD11.FK_Device=PK_Device \
	LEFT JOIN Room ON PK_Room=FK_Room \
	WHERE FK_DeviceTemplate IN ($DT_Light_OnOff,$DT_Light_Dimmer,$DT_Light_RGB) \
	AND FK_Device_ControlledVia IN ($KNXDeviceID) \
	AND DD12.FK_DeviceData=$DD_Channel \
	AND DD11.FK_DeviceData=$DD_FloorplanObjectType \
	AND Device.FK_Installation=$InstallationID \
	ORDER BY room ASC"

	# read all lights into array
	while read -r line; do
    		array+=("$line")
	done < <($mysql_cmd "use $MySqlDB; $qry;")
	
	# write light by light into xml file
	for row in "${array[@]}"; do
		id=`echo "$row"| cut -f1`;
		description=`echo "$row"| cut -f2`;
		template=`echo "$row"| cut -f3`;
		port=`echo "$row"| cut -f4`;		
		room=`echo "$row"| cut -f5`;		
		echo "	$room: $description"

		RoomUUID=$(AGO_GetOrCreateRoom "$room")
		DeviceUUID=$(AGO_GetOrCreateDevice "$description" "$RoomUUID")
		#echo "	<!-- $room: $description (lmce:$id) -->" >> $XML_File

		# On/Off light
		if [[ $template -eq $DT_Light_OnOff ]]; then
			onoff=`echo "$port"| cut -d"|" -f1`;
			status=`echo "$port"| cut -d"|" -f2`;
			echo "	<device uuid=\"$DeviceUUID\" type=\"switch\">" >> $XML_File
			echo "		<ga type=\"onoff\">$onoff</ga>" >> $XML_File
			echo "		<ga type=\"onoffstatus\">$status</ga>" >> $XML_File
			echo "	</device>" >> $XML_File		
		fi

		# Dimmable light
		if [[ $template -eq $DT_Light_Dimmer ]]; then
			onoff=`echo "$port"| cut -d"|" -f1`;
			setlevel=`echo "$port"| cut -d"|" -f2`;
			levelstatus=`echo "$port"| cut -d"|" -f4`;
			echo "	<device uuid=\"$DeviceUUID\" type=\"dimmer\">" >> $XML_File
			echo "		<ga type=\"onoff\">$onoff</ga>" >> $XML_File
			echo "		<ga type=\"setlevel\">$setlevel</ga>" >> $XML_File
			echo "		<ga type=\"levelstatus\">$levelstatus</ga>" >> $XML_File
			echo "	</device>" >> $XML_File		
		fi

		# RGB light
		if [[ $template -eq $DT_Light_RGB ]]; then
			onoff=`echo "$port"| cut -d"|" -f1`;
			red=`echo "$port"| cut -d"|" -f2`;
			green=`echo "$port"| cut -d"|" -f3`;
			blue=`echo "$port"| cut -d"|" -f4`;
			echo "	<device uuid=\"$DeviceUUID\" type=\"dimmerrgb\">" >> $XML_File
			echo "		<ga type=\"onoff\">$onoff</ga>" >> $XML_File
			echo "		<ga type=\"red\">$red</ga>" >> $XML_File
			echo "		<ga type=\"green\">$green</ga>" >> $XML_File
			echo "		<ga type=\"blue\">$blue</ga>" >> $XML_File
			echo "	</device>" >> $XML_File		
		fi						
	done
}

# Import blinds, shutters and drapes
ImportBlinds()
{
	echo "Importing blinds, drapes and shutters"
	array=()
	
	qry="SELECT Device.PK_Device, Device.Description, Device.FK_DeviceTemplate, DD12.IK_DeviceData, Room.Description AS room \
	FROM Device \
	INNER JOIN DeviceTemplate ON FK_DeviceTemplate=PK_DeviceTemplate \
	LEFT JOIN Device_DeviceData AS DD12 ON DD12.FK_Device=PK_Device \
	LEFT JOIN Device_DeviceData AS DD11 ON DD11.FK_Device=PK_Device \
	LEFT JOIN Room ON PK_Room=FK_Room \
	WHERE FK_DeviceTemplate IN ($DT_Drapes) \
	AND FK_Device_ControlledVia IN ($KNXDeviceID) \
	AND DD12.FK_DeviceData=$DD_Channel \
	AND DD11.FK_DeviceData=$DD_FloorplanObjectType \
	AND Device.FK_Installation=$InstallationID \
	ORDER BY room ASC"

	# read all lights into array
	while read -r line; do
    		array+=("$line")
	done < <($mysql_cmd "use $MySqlDB; $qry;")
	
	# write device by device into xml file
	for row in "${array[@]}"; do
		id=`echo "$row"| cut -f1`;
		description=`echo "$row"| cut -f2`;
		template=`echo "$row"| cut -f3`;
		port=`echo "$row"| cut -f4`;		
		room=`echo "$row"| cut -f5`;		
		echo "	$room: $description"

		RoomUUID=$(AGO_GetOrCreateRoom "$room")
		DeviceUUID=$(AGO_GetOrCreateDevice "$description" "$RoomUUID")
		#echo "	<!-- $room: $description (lmce:$id) -->" >> $XML_File

		# Drapes
		if [[ $template -eq $DT_Drapes ]]; then
			setlevel=`echo "$port"| cut -d"|" -f1`;
			levelstatus=`echo "$port"| cut -d"|" -f2`;
			onoff=`echo "$port"| cut -d"|" -f3`;
			stop=`echo "$port"| cut -d"|" -f4`;
			echo "	<device uuid=\"$DeviceUUID\" type=\"drapes\">" >> $XML_File
			echo "		<ga type=\"onoff\">$onoff</ga>" >> $XML_File
			echo "		<ga type=\"setlevel\">$setlevel</ga>" >> $XML_File
			echo "		<ga type=\"levelstatus\">$levelstatus</ga>" >> $XML_File
			echo "		<ga type=\"stop\">$stop</ga>" >> $XML_File
			echo "	</device>" >> $XML_File		
		fi
	done
}

# Import blinds, shutters and drapes
ImportClimate()
{
	echo "Importing climate devices"
	array=()
	
	qry="SELECT Device.PK_Device, Device.Description, Device.FK_DeviceTemplate, DD12.IK_DeviceData, Room.Description AS room \
	FROM Device \
	INNER JOIN DeviceTemplate ON FK_DeviceTemplate=PK_DeviceTemplate \
	LEFT JOIN Device_DeviceData AS DD12 ON DD12.FK_Device=PK_Device \
	LEFT JOIN Room ON PK_Room=FK_Room \
	WHERE FK_DeviceTemplate IN ($DT_Thermometer, $DT_WallOutlet) \
	AND FK_Device_ControlledVia IN ($KNXDeviceID) \
	AND DD12.FK_DeviceData=$DD_Channel \
	AND Device.FK_Installation=$InstallationID \
	ORDER BY room ASC"

	# read all lights into array
	while read -r line; do
    		array+=("$line")
	done < <($mysql_cmd "use $MySqlDB; $qry;")
	
	# write device by device into xml file
	for row in "${array[@]}"; do
		id=`echo "$row"| cut -f1`;
		description=`echo "$row"| cut -f2`;
		template=`echo "$row"| cut -f3`;
		port=`echo "$row"| cut -f4`;		
		room=`echo "$row"| cut -f5`;		
		echo "	$room: $description"

		RoomUUID=$(AGO_GetOrCreateRoom "$room")
		DeviceUUID=$(AGO_GetOrCreateDevice "$description" "$RoomUUID")
		#echo "	<!-- $room: $description (lmce:$id) -->" >> $XML_File

		# Thermometers
		if [[ $template -eq $DT_Thermometer ]]; then
			temperature=`echo "$port"| cut -d"|" -f1`;
			echo "	<device uuid=\"$DeviceUUID\" type=\"multilevelsensor\">" >> $XML_File
			echo "		<ga type=\"temperature\">$temperature</ga>" >> $XML_File
			echo "	</device>" >> $XML_File		
		fi

		# Wall Outlets
		if [[ $template -eq $DT_WallOutlet ]]; then
			onoff=`echo "$port"| cut -d"|" -f1`;
			status=`echo "$port"| cut -d"|" -f2`;
			echo "	<device uuid=\"$DeviceUUID\" type=\"switch\">" >> $XML_File
			echo "		<ga type=\"onoff\">$onoff</ga>" >> $XML_File
			echo "		<ga type=\"onoffstatus\">$status</ga>" >> $XML_File
			echo "	</device>" >> $XML_File		
		fi
	done
}


#
# Main worker spaghetti
#

launch=1
distro=unknown
code=unknown

# Verify Linux distribution and version
lsb_release=$(which lsb_release)
if [[ -z "$lsb_release" ]]; then
	launch=0
else
	code=$($lsb_release -c|cut -f2)
	if [[ "$code" != "wheezy" ]]; then
		distro=$($lsb_release -i|cut -f2)
		launch=0
	fi	
fi

if [[ launch -eq "0" ]]; then
	echo "*** This script was tested under Debian wheezy but you seem to run $distro $code !"
	echo "*** While it should still work, you run this script @ your own risk !"
	echo
	read -p "Continue (y/n) ?" -n 1 -r
	echo
	if [[ $REPLY =~ ^[Nn]$ ]]; then
    	exit 1
    fi
fi

# Verify that sqlite binary exists
sqlite=$(which sqlite3)
if [[ -z "$sqlite" ]]; then
	echo "*** ERROR: No sqlite3 binary found."
	exit 1
else
	echo "SQLITE: binary found -> $sqlite"	
fi

# Verify that mysql client binary exists
mysql=$(which mysql)
if [[ -z "$mysql" ]]; then
	echo "*** ERROR: No mysql client found."
	echo "	I'm trying to install it. If successfull restart this script afterwards. If not try to install mysql-client manually"
	echo ""
	apt-get -y install mysql-client
	exit 1
else
	echo "MYSQL: binary found -> $mysql"
	mysql_cmd="$mysql -f -h $MySqlHost -u$MySqlUser $PassParm -se"	
fi

# Verify that uuidgen binary exists
uuidgen=$(which uuidgen)
if [[ -z "$uuidgen" ]]; then
	echo "*** ERROR: uuidgen binary not found."
	echo "	I'm trying to install it. If successfull restart this script afterwards. If not try to install uuid-runtime manually"
	echo ""
	apt-get -y install uuid-runtime
	exit 1
else
	echo "UUIDGEN: binary found -> $uuidgen"
fi

# Verify that systemctl binary exists
systemctl=$(which systemctl)
if [[ -z "$systemctl" ]]; then
	echo "*** ERROR: systemctl binary not found."
	echo "	This scripts only supports stoping and starting services using systemctl. Please stop agoknx and agoresolver before launching this script !"
	echo
	read -p "Continue script (y/n) ?" -n 1 -r
	echo
	if [[ $REPLY =~ ^[nN]$ ]]; then
    		exit 1	
	fi
else
	echo "SYSTEMCTL: binary found -> $systemctl"
fi

echo ""

# Get LinuxMCE specific parameters
LMCE_GetInstallationID
if [[ -z "$InstallationID" ]]; then
	echo "*** ERROR: No installation ID found, check database connection."
	exit 1
else
	echo "LMCE: Installation ID = $InstallationID"	
fi
LMCE_GetKNXDeviceID
if [[ -z "$KNXDeviceID" ]]; then
	echo "*** ERROR: No KNX device found in your LinuxMCE installation, check database connection and / or config."
	exit 1
else
	echo "LMCE: KNX Device_ID = $KNXDeviceID"
fi

# Do the job
if [[ -n "$systemctl" ]]; then
	$systemctl stop agoknx.service
	$systemctl stop agoresolver.service
fi

echo "<devices>" > $XML_File

# Import lights
echo
read -p "Import lights (y/n) ?" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ImportLights
fi

# Import blinds
echo
read -p "Import blinds / drapes / shutters (y/n) ? " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ImportBlinds
fi

# Import climate devices
echo
read -p "Import climate devices (y/n) ? " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ImportClimate
fi

echo "</devices>" >> $XML_File

if [[ -n "$systemctl" ]]; then
	$systemctl start agoresolver.service
	$systemctl start agoknx.service
fi

exit 0
