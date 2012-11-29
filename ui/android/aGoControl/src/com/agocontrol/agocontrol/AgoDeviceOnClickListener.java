package com.agocontrol.agocontrol;

import android.view.View;


public class AgoDeviceOnClickListener implements View.OnClickListener {
	private AgoDevice myDevice;
	private String command;
	
	public AgoDeviceOnClickListener(AgoDevice _myDevice, String _command) {
		this.myDevice = _myDevice;
		this.command = _command;
		
	}
	
	public void onClick(View v) {
		System.out.println("UUID: " + myDevice.getName() + "clicked");
		AgoConnection connection = myDevice.getConnection();
		connection.sendCommand(myDevice.getUuid(), command);
		
	}

	public AgoDevice getAgoDevice() {
		return myDevice;
	}
}
