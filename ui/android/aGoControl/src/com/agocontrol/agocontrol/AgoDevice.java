package com.agocontrol.agocontrol;

import java.util.UUID;

public class AgoDevice {
	UUID uuid;
	String name;
	String deviceType;
	int status;
	AgoConnection connection;

	public AgoDevice(UUID _uuid) {
		name = "";
		uuid = _uuid;
		deviceType = "switch";
		status = 0;
	}
	
	public AgoDevice(UUID _uuid, String _deviceType) {
		name = "";
		uuid = _uuid;
		deviceType = _deviceType;
		status = 0;
	}
		
	public AgoDevice(UUID _uuid, String _deviceType, String _name) {
		name = _name;
		uuid = _uuid;
		deviceType = _deviceType;
		status = 0;
	}
	public AgoDevice(UUID _uuid, String _deviceType, String _name, int _status) {
		name = _name;
		uuid = _uuid;
		deviceType = _deviceType;
		status = _status;
	}

	public int getStatus() { return status; }
	public String getDeviceType() { return deviceType; }
	public String getName() { return name; }
	public UUID getUuid() { return uuid; }
	public AgoConnection getConnection() { return connection; }
	public void setUuid(UUID _uuid) { uuid = _uuid; }
	public void setStatus(int _status) { status = _status; }
	public void setName(String _name) { name = _name; }
	public void setDeviceType(String _deviceType) { deviceType = _deviceType; }
	public void setConnection(AgoConnection _connection) { connection = _connection; }
	
	@Override
	public String toString() {
		return name;
		
	}

}
