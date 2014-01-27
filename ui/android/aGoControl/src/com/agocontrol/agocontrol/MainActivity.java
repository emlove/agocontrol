package com.agocontrol.agocontrol;

import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.Arrays;

import android.annotation.TargetApi;
import android.app.Activity;
import android.app.Dialog;
import android.app.ListActivity;
import android.app.PendingIntent;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.IntentFilter.MalformedMimeTypeException;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.nfc.NdefMessage;
import android.nfc.NdefRecord;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.nfc.tech.Ndef;
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
	public static final String MIME_TEXT_PLAIN = "text/plain";
	
	private NfcAdapter mNfcAdapter;
	
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
        
        mNfcAdapter = NfcAdapter.getDefaultAdapter(this);
        
        if (mNfcAdapter != null) {
        	
        	if (!mNfcAdapter.isEnabled()) {
        		// TODO: adapter is disabled
        	} else {
        		
        		// we're good to go
        	}
        } else {
        	// TODO: nfc not available
        	
        }
        
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
    	agoPort = prefs.getString(PreferencesActivity.PREF_AGOCONTROL_PORT,  "8008");
    	
    }

    public void onActivtyResult(int requestCode, int resultCode, Intent data) {
    	super.onActivityResult(requestCode, resultCode, data);
    	
    	if (requestCode == SHOW_PREFERENCES)
    		updateFromPreferences();

    }
    
    private class openConnection extends AsyncTask <Void, Void, Void> {

		@Override
		protected Void doInBackground(Void... params) {
			Log.i(TAG, "Trying connection to " + agoHostname + ":" + agoPort);
			connection = new AgoConnection(agoHostname, agoPort);
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
    }

	@Override
	protected void onPause() {
		stopForegroundDispatch(this, mNfcAdapter);
		super.onPause();
	}
	
	public static void stopForegroundDispatch(final Activity activity, NfcAdapter adapter) {
		if (adapter != null) {
			adapter.disableForegroundDispatch(activity);
		}
	}

	
	@Override
	protected void onResume() {
		super.onResume();
		setupForegroundDispatch(this, mNfcAdapter);
		new openConnection().execute();
	}

	@Override
    protected void onNewIntent(Intent intent) {
		handleIntent(intent);
	}
	private void handleIntent(Intent intent) {
	    String action = intent.getAction();
	    if (NfcAdapter.ACTION_NDEF_DISCOVERED.equals(action)) {
	        String type = intent.getType();
	        if (MIME_TEXT_PLAIN.equals(type)) {
	            Tag tag = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG);
	            new NdefReaderTask().execute(tag);
	        } else {
	            Log.d(TAG, "Wrong mime type: " + type);
	        }
	    } else if (NfcAdapter.ACTION_TECH_DISCOVERED.equals(action)) {
	        // In case we would still use the Tech Discovered Intent
	        Tag tag = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG);
	        String[] techList = tag.getTechList();
	        String searchedTech = Ndef.class.getName();
	        for (String tech : techList) {
	            if (searchedTech.equals(tech)) {
	                new NdefReaderTask().execute(tag);
	                break;
	            }
	        }
	    }
    }
	
	private class NdefReaderTask extends AsyncTask<Tag, Void, String> {
	    @Override
	    protected String doInBackground(Tag... params) {
	        Tag tag = params[0];
	        Ndef ndef = Ndef.get(tag);
	        if (ndef == null) {
	            // NDEF is not supported by this Tag.
	            return null;
	        }
	        NdefMessage ndefMessage = ndef.getCachedNdefMessage();
	        NdefRecord[] records = ndefMessage.getRecords();
	        for (NdefRecord ndefRecord : records) {
	            if (ndefRecord.getTnf() == NdefRecord.TNF_WELL_KNOWN && Arrays.equals(ndefRecord.getType(), NdefRecord.RTD_TEXT)) {
	                try {
	                    
	                    String text = readText(ndefRecord);
	    	        	connection.sendEvent("event.proximity.ndef", text);
	    	        	return text;
	                } catch (UnsupportedEncodingException e) {
	                    Log.e(TAG, "Unsupported Encoding", e);
	                }
	            }
	        }
	        return null;
	    }
	    private String readText(NdefRecord record) throws UnsupportedEncodingException {
	        /*
	         * See NFC forum specification for "Text Record Type Definition" at 3.2.1
	         *
	         * http://www.nfc-forum.org/specs/
	         *
	         * bit_7 defines encoding
	         * bit_6 reserved for future use, must be 0
	         * bit_5..0 length of IANA language code
	         */
	        byte[] payload = record.getPayload();
	        // Get the Text Encoding
	        String textEncoding = ((payload[0] & 128) == 0) ? "UTF-8" : "UTF-16";
	        // Get the Language Code
	        int languageCodeLength = payload[0] & 0063;
	        // String languageCode = new String(payload, 1, languageCodeLength, "US-ASCII");
	        // e.g. "en"
	        // Get the Text
	        return new String(payload, languageCodeLength + 1, payload.length - languageCodeLength - 1, textEncoding);
	    }
	    @Override
	    protected void onPostExecute(String result) {
	        // if (result != null) {
	        // }
	    }
	}
	
	
	public static void setupForegroundDispatch(final Activity activity, NfcAdapter adapter) {
		if (adapter == null) return;
        final Intent intent = new Intent(activity.getApplicationContext(), activity.getClass());
        intent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
        final PendingIntent pendingIntent = PendingIntent.getActivity(activity.getApplicationContext(), 0, intent, 0);
        IntentFilter[] filters = new IntentFilter[1];
        String[][] techList = new String[][]{};
        // Notice that this is the same filter as in our manifest.
        filters[0] = new IntentFilter();
        filters[0].addAction(NfcAdapter.ACTION_NDEF_DISCOVERED);
        filters[0].addCategory(Intent.CATEGORY_DEFAULT);
        try {
            filters[0].addDataType(MIME_TEXT_PLAIN);
        } catch (MalformedMimeTypeException e) {
            throw new RuntimeException("Check your mime type.");
        }
        adapter.enableForegroundDispatch(activity, pendingIntent, filters, techList);
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
