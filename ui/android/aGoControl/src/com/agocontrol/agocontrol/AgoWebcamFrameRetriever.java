package com.agocontrol.agocontrol;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URL;
import java.net.UnknownHostException;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.util.Log;

public class AgoWebcamFrameRetriever {
	
	private static final String TAG = AgoWebcamFrameRetriever.class.getSimpleName();
	
	private Context mContext;
	private AgoDevice myDevice;
	private String mUrl;
	
	public AgoWebcamFrameRetriever(Context context, AgoDevice _myDevice) {
		mContext = context;
		this.myDevice = _myDevice;
	}
	
	
	public Bitmap getBitmap() {
		Bitmap bitmap = null;
		
		AgoConnection connection = myDevice.getConnection();	
		try {
			Log.i(TAG, "getting video frame");
			 byte[] byteArray = connection.getVideoFrame(myDevice.getUuid());
            bitmap = BitmapFactory.decodeByteArray(byteArray, 0, byteArray.length);
        } catch (Exception ex){
           if (Global.DEBUG) Log.e(TAG, "getBitmap(): " + ex.getMessage());
           return BitmapFactory.decodeResource(mContext.getResources(),  R.drawable.ic_camera);
        }
		return bitmap;
	}
	
	private Bitmap decodeFile(byte[] byteArray) {
		
		try {
			final BitmapFactory.Options o = new BitmapFactory.Options();
            o.inJustDecodeBounds = true;
            o.inSampleSize = 8;
            o.inPurgeable = true;
            o.inTempStorage = new byte[16000];
            
            BitmapFactory.decodeByteArray(byteArray, 0, byteArray.length, o);
            
            final int REQUIRED_SIZE=70;
            int width_tmp=o.outWidth, height_tmp=o.outHeight;
            int scale=1;
            while(true){
                if(width_tmp/2<REQUIRED_SIZE || height_tmp/2<REQUIRED_SIZE)
                    break;
                width_tmp/=2;
                height_tmp/=2;
                scale*=2;
            }
            
            //decode with inSampleSize
            final BitmapFactory.Options o2 = new BitmapFactory.Options();
            o2.inSampleSize=scale;
            o2.inPurgeable = true;
            final Bitmap ret = BitmapFactory.decodeByteArray(byteArray, 0, byteArray.length, o2);
            return ret;
		} catch (Exception e) {
			
		}
		return null;
		
	}
	
	private void copyStream(InputStream is, OutputStream os)
    {
        final int buffer_size=1024;
        try
        {
            byte[] bytes=new byte[buffer_size];
            for(;;)
            {
              int count=is.read(bytes, 0, buffer_size);
              if(count==-1)
                  break;
              os.write(bytes, 0, count);
            }
        }
        catch(Exception ex){}
    }

}
