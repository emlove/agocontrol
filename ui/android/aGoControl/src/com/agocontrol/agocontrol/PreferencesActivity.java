package com.agocontrol.agocontrol;

import java.util.List;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.preference.PreferenceActivity;
import android.preference.PreferenceManager;


public class PreferencesActivity extends PreferenceActivity {
	public static final String PREF_AGOCONTROL_HOSTNAME = "PREF_AGOCONTROL_HOSTNAME";
	public static final String PREF_AGOCONTROL_PORT = "PREF_AGOCONTROL_PORT";
	
	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
	    
		addPreferencesFromResource(R.xml.userpreferences);
	}

	private void updateFromPreferences() {
		Context context = getApplicationContext();
		SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(context);
		
	}
}
