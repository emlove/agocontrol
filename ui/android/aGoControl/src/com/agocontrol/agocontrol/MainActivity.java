package com.agocontrol.agocontrol;

import java.util.ArrayList;

import android.annotation.TargetApi;
import android.app.Activity;
import android.app.Dialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.ListView;
import android.util.Log;

public class MainActivity extends Activity {
	
	private static final String TAG = MainActivity.class.getSimpleName();
	
	AgoConnection connection;
	ArrayList<AgoDevice> deviceList; 
	private ListView lv;
	String agoHostname = "";
	String agoPort = "";
	
	static final private int MENU_PREFERENCES = Menu.FIRST + 1;
	private static final int SHOW_PREFERENCES = 1;
	
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        updateFromPreferences();
        
        Log.i(TAG, "Trying connection to " + agoHostname);
        
        connection = new AgoConnection(agoHostname);
        
        deviceList = connection.getDeviceList();
       
        setContentView(R.layout.devices_list_view);
        lv = (ListView) findViewById(R.id.devices_list_view);
        ArrayAdapter<AgoDevice> arrayAdapter = new ArrayAdapter<AgoDevice>(this, android.R.layout.simple_list_item_1, deviceList);
        lv.setAdapter(arrayAdapter);
        lv.setOnItemClickListener(new AdapterView.OnItemClickListener() {
        	public void onItemClick(AdapterView parentView, View childView, int position, long id) {
        		AgoDevice myDevice = deviceList.get(position);
        		System.out.println(myDevice.toString());
        		Dialog dialog = new Dialog(parentView.getContext());
        		dialog.setTitle(myDevice.getName());
        		dialog.setContentView(R.layout.dialog);
        		Button button_on = (Button)dialog.findViewById(R.id.button_on);
        		button_on.setOnClickListener(new AgoDeviceOnClickListener(myDevice, "on"));
        		Button button_off = (Button)dialog.findViewById(R.id.button_off);
        		button_off.setOnClickListener(new AgoDeviceOnClickListener(myDevice, "off"));
        		dialog.show();
        		
        		
        	}
		});
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
    	super.onCreateOptionsMenu(menu);
    	menu.add(0, MENU_PREFERENCES, Menu.NONE, R.string.menu_settings);
        // getMenuInflater().inflate(R.menu.activity_main, menu);
        return true;
    }
    
	@TargetApi(4)
	@SuppressWarnings("rawtypes")
	public boolean onOptionsItemSelected(MenuItem item) {
    	super.onOptionsItemSelected(item);
    	switch (item.getItemId()) {
    		case (MENU_PREFERENCES): {
    	 		Class c= Build.VERSION.SDK_INT < Build.VERSION_CODES.HONEYCOMB ? PreferencesActivity.class : FragmentPreferences.class;
    			Intent i = new Intent(this, c);
    			startActivityForResult(i, SHOW_PREFERENCES);
    			return true;
    		}
    	}
    	return false;
    }
    
    private void updateFromPreferences() {
    	Context context = getApplicationContext();
    	SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(context);
    	agoHostname = prefs.getString(PreferencesActivity.PREF_AGOCONTROL_HOSTNAME,  "192.168.80.2");
    	agoPort = prefs.getString(PreferencesActivity.PREF_AGOCONTROL_PORT,  "8000");
    	
    }

    public void onActivtyResult(int requestCode, int resultCode, Intent data) {
    	super.onActivityResult(requestCode, resultCode, data);
    	
    	if (requestCode == SHOW_PREFERENCES)
    		updateFromPreferences();
    	
    		connection = new AgoConnection(agoHostname);
        
    		deviceList = connection.getDeviceList();

    }
}
