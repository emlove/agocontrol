package com.agocontrol.agocontrol;

import java.util.ArrayList;

import android.annotation.TargetApi;
import android.app.Activity;
import android.app.Dialog;
import android.app.ListActivity;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.os.AsyncTask;
import android.os.Build;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.WindowManager;
import android.view.WindowManager.LayoutParams;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.SeekBar;
import android.widget.TextView;
import android.util.Log;

public class MainActivity extends ListActivity {
	
	private static final String TAG = MainActivity.class.getSimpleName();
	
	AgoConnection connection;
	ArrayList<AgoDevice> deviceList; 
	DeviceAdapter deviceAdapter;
	private ListView lv;
	String agoHostname = "";
	String agoPort = "";
	
	private ImageView mVideoFrame;
	
	ProgressDialog progDlg;
	
	static final private int MENU_PREFERENCES = Menu.FIRST + 1;
	private static final int SHOW_PREFERENCES = 1;
	
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        updateFromPreferences();
                
        deviceList = new ArrayList<AgoDevice>();
        setContentView(R.layout.devices_list_view);
        
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

    }
    
    private class openConnection extends AsyncTask <Void, Void, Void> {

		@Override
		protected Void doInBackground(Void... params) {
			Log.i(TAG, "Trying connection to " + agoHostname);
			connection = new AgoConnection(agoHostname);
			deviceList = connection.getDeviceList();
			return null;
		}

		@Override
		protected void onPostExecute(Void result) {
			
			deviceAdapter = new DeviceAdapter(MainActivity.this, deviceList);
	        setListAdapter(deviceAdapter);
			
			if (progDlg != null) {
				progDlg.dismiss();
			}
			progDlg = null;
			
			Log.i(TAG, deviceList.size() + " devices returned");
		}

		@Override
		protected void onPreExecute() {
			if (progDlg == null) {
				progDlg = ProgressDialog.show(MainActivity.this, null, getString(R.string.opening_connection), true, true);
			} else {
				progDlg.show();
			}
		}

		@Override
		protected void onCancelled() {
			// TODO Auto-generated method stub
			super.onCancelled();
		}
    	
    }

	@Override
	protected void onResume() {
		super.onResume();
		new openConnection().execute();
	}

	@Override
	protected void onListItemClick(ListView l, View v, int position, long id) {
		
		 final AgoDevice myDevice = deviceList.get(position);
		 Log.i(TAG, "clicked uuid " + myDevice.uuid.toString());
         final Dialog dialog = new Dialog(MainActivity.this);
         dialog.setTitle(myDevice.getName());
         dialog.setContentView(R.layout.device_control_dlg);
         dialog.getWindow().setLayout(WindowManager.LayoutParams.MATCH_PARENT, WindowManager.LayoutParams.WRAP_CONTENT);
         
         //show/hide views based on device type
         final LinearLayout llOnOff = (LinearLayout)dialog.findViewById(R.id.llOnOff);
         final LinearLayout llCamera = (LinearLayout)dialog.findViewById(R.id.llCamera);
         final FrameLayout flDimmer = (FrameLayout)dialog.findViewById(R.id.flDimmer);
         final SeekBar sbSetLevel = (SeekBar)dialog.findViewById(R.id.sbSetLevel);
         final Button btnGetVideoFrame = (Button)dialog.findViewById(R.id.btnGetVideoFrame);
         final Button btnRunScenario = (Button)dialog.findViewById(R.id.btnRunScenario);
         final Button btnOn = (Button)dialog.findViewById(R.id.btnOn);
         final Button btnOff = (Button)dialog.findViewById(R.id.btnOff);
         final TextView tvLevel = (TextView)dialog.findViewById(R.id.tvLevel);
         mVideoFrame = (ImageView)dialog.findViewById(R.id.ivVideoFrame);
         
         if (myDevice.deviceType.equalsIgnoreCase("switch") || myDevice.deviceType.equalsIgnoreCase("dimmer") ) {
        	 llOnOff.setVisibility(View.VISIBLE);
        	 btnOn.setOnClickListener(new AgoDeviceOnClickListener(myDevice, "on"));
        	 btnOff.setOnClickListener(new AgoDeviceOnClickListener(myDevice, "off"));
         }
         
         if (myDevice.deviceType.equalsIgnoreCase("dimmer")) {
        	 llOnOff.setVisibility(View.VISIBLE);
        	 flDimmer.setVisibility(View.VISIBLE);
        	 btnOn.setOnClickListener(new AgoDeviceOnClickListener(myDevice, "on"));
        	 btnOff.setOnClickListener(new AgoDeviceOnClickListener(myDevice, "off"));
        	 
        	 sbSetLevel.setOnSeekBarChangeListener(new AgoDeviceSetLevelListener(myDevice));
        	 
         } else if (myDevice.deviceType.equalsIgnoreCase("camera")) {
        	 llCamera.setVisibility(View.VISIBLE);
        	 btnGetVideoFrame.setOnClickListener(new View.OnClickListener() {
			
				@Override
				public void onClick(View v) {
					new getVideoFrame().execute(new Object[] {(Context)MainActivity.this, myDevice});
				}
			});
         } else if (myDevice.deviceType.equalsIgnoreCase("scenario")) {
        	 btnRunScenario.setVisibility(View.VISIBLE);
        	 btnRunScenario.setOnClickListener(new AgoDeviceOnClickListener(myDevice, "on"));
         }
         
         
         
//         Button button_on = (Button)dialog.findViewById(R.id.button_on);
//         button_on.setOnClickListener(new AgoDeviceOnClickListener(myDevice, "on"));
//         Button button_off = (Button)dialog.findViewById(R.id.button_off);
//         button_off.setOnClickListener(new AgoDeviceOnClickListener(myDevice, "off"));
         dialog.show();
	}
	
	private class getVideoFrame extends AsyncTask <Object, Void, Bitmap> {

		@Override
		protected Bitmap doInBackground(Object... params) {
			final AgoWebcamFrameRetriever awfr = new AgoWebcamFrameRetriever((Context)params[0], (AgoDevice)params[1]);
			return awfr.getBitmap();
		}

		@Override
		protected void onPostExecute(Bitmap result) {
			super.onPostExecute(result);
			if (progDlg != null) {
				progDlg.dismiss();
			}
			progDlg = null;
			mVideoFrame.setImageBitmap(result);
		}

		@Override
		protected void onPreExecute() {
			if (progDlg == null) {
				progDlg = ProgressDialog.show(MainActivity.this, null, getString(R.string.retrieving_video_frame), true, true);
			} else {
				progDlg.show();
			}
		}

		
	}
	
}
