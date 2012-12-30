package com.agocontrol.agocontrol;

import java.io.IOException;

import org.apache.http.HttpResponse;
import org.apache.http.StatusLine;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.DefaultHttpClient;

import android.os.AsyncTask;
import android.util.Log;
import android.widget.SeekBar;

public class AgoDeviceSetLevelListener implements SeekBar.OnSeekBarChangeListener {

	private static final String TAG = AgoDeviceSetLevelListener.class.getSimpleName();
	
	private AgoDevice myDevice;
	
	public AgoDeviceSetLevelListener(AgoDevice _myDevice) {
		this.myDevice = _myDevice;
	}
	
	@Override
	public void onProgressChanged(SeekBar seekBar, int progress,
			boolean fromUser) {
		// TODO update UI with actual value in seekbar
	}

	@Override
	public void onStartTrackingTouch(SeekBar seekBar) {
		// TODO make the value visible
	}

	@Override
	public void onStopTrackingTouch(SeekBar seekBar) {
		// TODO make the value invisible
		new sendLevelAsync().execute(new Object[] {(Object)myDevice, (Object)Integer.valueOf(seekBar.getProgress())});
		
		
	}
	
	private class sendLevelAsync extends AsyncTask<Object, Void, Void> {

		@Override
		protected Void doInBackground(Object... params) {
			Log.i(TAG, "setting level async: " + params[1]);
			
			final AgoDevice dev = (AgoDevice)params[0];
			final String level = String.valueOf((Integer)params[1]);
			final String host = dev.connection.host;
		    HttpClient client = new DefaultHttpClient();
		    HttpGet httpGet = new HttpGet("http://" + host + ":8000/setdevicelevel/" + dev.getUuid().toString() + "/setlevel/" + level);
		    try {
		        HttpResponse response = client.execute(httpGet);
		        StatusLine statusLine = response.getStatusLine();
		        int statusCode = statusLine.getStatusCode();
		    } catch (ClientProtocolException e) {
			        e.printStackTrace();
			} catch (IOException e) {
			        e.printStackTrace();
			}
		
			return null;
		}
		
	}

}
