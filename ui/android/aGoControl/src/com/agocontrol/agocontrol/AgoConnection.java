package com.agocontrol.agocontrol;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.UUID;

import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.StatusLine;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.DefaultHttpClient;
import org.json.JSONObject;

import android.util.Log;

public class AgoConnection {
	String host;
	String inventory;
	Double schemaVersion;
	ArrayList<AgoDevice> deviceList;

	public static String SCHEMA = "schema";
	public static String SCHEMA_VERSION = "version";
	public static String DEVICES = "inventory"; // TODO needs to be fixed in the resolver, should be devices
	public static String DEVICE_TYPE = "devicetype";
	public static String DEVICE_ROOM = "room";
	public static String DEVICE_STATE = "state";
	public static String DEVICE_NAME = "name";
	
	public AgoConnection(String _host) {
		System.out.println(_host);
		this.host = _host;
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
		      Iterator iter = devices.keys();
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
	    HttpClient client = new DefaultHttpClient();
	    HttpGet httpGet = new HttpGet("http://" + host + ":8000/command/" + uuid.toString() + "/" + command);
	    try {
	        HttpResponse response = client.execute(httpGet);
	        StatusLine statusLine = response.getStatusLine();
	        int statusCode = statusLine.getStatusCode();
	        if (statusCode == 200) {
	        	return true;
	        }
	    } catch (ClientProtocolException e) {
		        e.printStackTrace();
		} catch (IOException e) {
		        e.printStackTrace();
		}
		return false;
	}
	private String getInventory() {
	    StringBuilder builder = new StringBuilder();
	    HttpClient client = new DefaultHttpClient();
	    HttpGet httpGet = new HttpGet("http://" + host + ":8000/getinventory");
	    try {
	        HttpResponse response = client.execute(httpGet);
	        StatusLine statusLine = response.getStatusLine();
	        int statusCode = statusLine.getStatusCode();
	        if (statusCode == 200) {
	          HttpEntity entity = response.getEntity();
	          InputStream content = entity.getContent();
	          BufferedReader reader = new BufferedReader(new InputStreamReader(content));
	          String line;
	          while ((line = reader.readLine()) != null) {
	            builder.append(line);
	          }
	        } else {
	          Log.e(AgoConnection.class.toString(), "Failed to download file");
	        }
	      } catch (ClientProtocolException e) {
	        e.printStackTrace();
	      } catch (IOException e) {
	        e.printStackTrace();
	      }
	    return builder.toString();
	}

}
