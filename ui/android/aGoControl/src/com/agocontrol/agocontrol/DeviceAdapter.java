package com.agocontrol.agocontrol;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.ImageView;
import android.widget.TextView;

public class DeviceAdapter extends BaseAdapter {

	private static final String TAG = DeviceAdapter.class.getSimpleName();
	
	protected Context mContext;
	protected ArrayList<AgoDevice> mDevices;
	protected LayoutInflater mInflater;
	
	Comparator<AgoDevice> deviceComparator = new Comparator<AgoDevice>() {
		public int compare(AgoDevice obj1, AgoDevice obj2) {
			return obj1.getName().compareToIgnoreCase(obj2.getName());
		}
	};
	
	public DeviceAdapter() {
		super();
	}

	public DeviceAdapter(Context context, ArrayList<AgoDevice> devices) {
		super();
		mContext = context;
		mDevices = devices;
		Collections.sort(devices, deviceComparator);
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
			v = mInflater.inflate(R.layout.device_item, null, false);
			ViewHolder holder = new ViewHolder();
			holder.deviceName = (TextView)v.findViewById(R.id.tvDeviceName);
			holder.deviceType = (ImageView)v.findViewById(R.id.ivDeviceType);
			v.setTag(holder);
		}
		AgoDevice device = (AgoDevice)getItem(position);
		ViewHolder holder = (ViewHolder)v.getTag();
		holder.deviceName.setText(device.name);
		
		if (device.deviceType.equalsIgnoreCase("switch")) {
			holder.deviceType.setImageResource(R.drawable.ic_on_off);
		} else if (device.deviceType.equalsIgnoreCase("dimmer")) {
			holder.deviceType.setImageResource(R.drawable.ic_dimmer);
		} else if (device.deviceType.equalsIgnoreCase("camera")) {
			holder.deviceType.setImageResource(R.drawable.ic_camera);
		} else if (device.deviceType.equalsIgnoreCase("zwavecontroller")) {
			holder.deviceType.setImageResource(R.drawable.ic_zwave_controller);
		} else if (device.deviceType.equalsIgnoreCase("controller")) {
			holder.deviceType.setImageResource(R.drawable.ic_zwave_controller);
		} else if (device.deviceType.equalsIgnoreCase("scenario")) {
			holder.deviceType.setImageResource(R.drawable.ic_launcher);
		} else {
			holder.deviceType.setImageResource(R.drawable.ic_unknown);
		}
		
				
		return v;
	}
	
	protected class ViewHolder {
		public TextView deviceName;
		public ImageView deviceType;
	}

	
}
