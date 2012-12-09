package com.agocontrol.agocontrol;

import java.util.ArrayList;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.TextView;

public class DeviceAdapter extends BaseAdapter {

	private static final String TAG = DeviceAdapter.class.getSimpleName();
	
	protected Context mContext;
	protected ArrayList<AgoDevice> mDevices;
	protected LayoutInflater mInflater;
	
	public DeviceAdapter() {
		super();
	}

	public DeviceAdapter(Context context, ArrayList<AgoDevice> devices) {
		super();
		mContext = context;
		mDevices = devices;
		mInflater = LayoutInflater.from(context);
	}
	
	@Override
	public int getCount() {
		return mDevices.size();
	}

	@Override
	public Object getItem(int position) {
		return mDevices.get(position);
	}

	@Override
	public long getItemId(int position) {
		return mDevices.get(position).hashCode();
	}

	@Override
	public View getView(int position, View convertView, ViewGroup parent) {
		View v = convertView;
		if (convertView == null) {
			v = mInflater.inflate(android.R.layout.simple_list_item_1, null, false);
			ViewHolder holder = new ViewHolder();
			holder.deviceName = (TextView)v.findViewById(android.R.id.text1);
			v.setTag(holder);
		}
		AgoDevice device = (AgoDevice)getItem(position);
		ViewHolder holder = (ViewHolder)v.getTag();
		holder.deviceName.setText(device.name);
		return v;
	}
	
	protected class ViewHolder {
		public TextView deviceName;
	}

}
