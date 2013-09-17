package com.agocontrol.agocontrol;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.UUID;

import org.alexd.jsonrpc.*;
import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.StatusLine;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.DefaultHttpClient;
import org.json.JSONException;
import org.json.JSONObject;

import android.util.Log;

public class AgoConnection {
	String host;
	String port;
	String inventory;
	Double schemaVersion;
	ArrayList<AgoDevice> deviceList;
	JSONRPCClient client;
	public static String SCHEMA = "schema";
	public static String SCHEMA_VERSION = "version";
	public static String DEVICES = "inventory"; // TODO needs to be fixed in the resolver, should be devices
	public static String DEVICE_TYPE = "devicetype";
	public static String DEVICE_ROOM = "room";
	public static String DEVICE_STATE = "state";
	public static String DEVICE_NAME = "name";
	
	public AgoConnection(String host, String port) {
		this.host = host;
		this.port = port;
		System.out.println(host + ":" + port);
		client = JSONRPCClient.create("http://" + host + ":" + port + "/jsonrpc", JSONRPCParams.Versions.VERSION_2);
		client.setConnectionTimeout(2000);
		client.setSoTimeout(2000);
		deviceList = new ArrayList<AgoDevice>();
		getDevices();
	}
	
	public ArrayList<AgoDevice> getDeviceList() {
		return deviceList;
	}
	
	public void getDevices() {
		inventory = getInventory();
		try {
		      JSONObject inv = new JSONObject(inventory);
		      Log.i(AgoConnection.class.getName(),
		          "Number of entries " + inv.length());
		      JSONObject schema = inv.getJSONObject(SCHEMA);
		      schemaVersion = schema.getDouble(SCHEMA_VERSION);
		      System.out.println("schema version: " + schemaVersion);
		      
		      JSONObject devices = inv.getJSONObject(DEVICES);
		      Log.i(AgoConnection.class.getName(),
			          "Number of devices: " + devices.length());
		      Iterator<?> iter = devices.keys();
		      while (iter.hasNext()) {
		    	  String deviceUuid = (String)iter.next();
		    	  System.out.println("UUid: " + deviceUuid);
		    	  JSONObject device = devices.getJSONObject(deviceUuid);
		    	  String deviceType = device.getString(DEVICE_TYPE);
		    	  String deviceName = device.getString(DEVICE_NAME);
		    	  System.out.println(deviceType);
		    	  UUID tmpUuid = UUID.fromString(deviceUuid);
		    	  AgoDevice newDevice = new AgoDevice(tmpUuid, deviceType);
		    	  if (deviceName != null) newDevice.setName(deviceName);
		    	  newDevice.setConnection(this);
		    	  deviceList.add(newDevice);
		      }
		     
		    } catch (Exception e) {
		      e.printStackTrace();
		    }
	}
	
	public boolean sendCommand(UUID uuid, String command) {
	    try {
	    	JSONObject agocommand = new JSONObject();
	    	agocommand.put("command", command);
	    	agocommand.put("uuid", uuid.toString());
	    	JSONObject params = new JSONObject();
	    	params.put("content", agocommand); 
	    	JSONObject result = client.callJSONObject("message", params);
	    	return true;
	    } catch (JSONRPCException e) {
	    	  e.printStackTrace();
	    } catch (JSONException e) {
	    		e.printStackTrace();
		}
		return false;
	}
	
	public boolean setDeviceLevel(UUID uuid, String level) {
	    try {
	    	JSONObject agocommand = new JSONObject();
	    	agocommand.put("command", "setlevel");
	    	agocommand.put("level", level);
	    	agocommand.put("uuid", uuid.toString());
	    	JSONObject params = new JSONObject();
	    	params.put("content", agocommand); 
	    	JSONObject result = client.callJSONObject("message", params);
	    	return true;
	    } catch (JSONRPCException e) {
	    	  e.printStackTrace();
	    } catch (JSONException e) {
	    		e.printStackTrace();
		}
	    return false;
	}
	
	private String getInventory() {
	    StringBuilder builder = new StringBuilder();
	    try {
	    	JSONObject command = new JSONObject();
	    	command.put("command", "inventory");
	    	JSONObject params = new JSONObject();
	    	params.put("content", command); 
	    	JSONObject result = client.callJSONObject("message", params);
	    	builder.append(result.toString());
	    } catch (JSONRPCException e) {
	    	  e.printStackTrace();
	    } catch (JSONException e) {
	    		e.printStackTrace();
		}
	    return builder.toString();
	}

}
