package com.agocontrol.agocontrol;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URL;
import java.net.UnknownHostException;
import java.util.HashMap;
import java.util.Stack;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.util.Log;
import android.widget.ImageView;

public class AgoWebcamFrameRetriever {
	
	private static final String TAG = AgoWebcamFrameRetriever.class.getSimpleName();
	
	private Context mContext;
	private AgoDevice mDevice;
	private String mUrl;
	
	public AgoWebcamFrameRetriever(Context context, AgoDevice myDevice) {
		mContext = context;
		mDevice = myDevice;
		mUrl = "http://" + myDevice.connection.host + ":8000/getvideoframe?uuid=" + myDevice.getUuid();
	}
	
	
	public Bitmap getBitmap() {
		
		Log.i(TAG, "getting video frame: " + mUrl);
		
		File f =  null; 
		Bitmap bitmap = null;
		try {
			File dir = mContext.getCacheDir();
			f=File.createTempFile("frame", null, dir);
            InputStream is=new  URL(mUrl).openStream();
            OutputStream os = new FileOutputStream(f);
            copyStream(is, os);
            os.close();
            bitmap = decodeFile(f);
            is.close();
        } catch (UnknownHostException uhe) {
        	if (Global.DEBUG) Log.e(TAG, "UnknownHostException . . . returning default");
        	return BitmapFactory.decodeResource(mContext.getResources(), R.drawable.ic_camera);
        	//return null;
        } catch (Exception ex){
           if (Global.DEBUG) Log.e(TAG, "getBitmap(): " + ex.getMessage());
           return BitmapFactory.decodeResource(mContext.getResources(),  R.drawable.ic_camera);
        } finally {
        	if (f != null) {
        		f.delete();
        	}
        }
		
		return bitmap;
	}
	
	private Bitmap decodeFile(File f) {
		
		try {
			final BitmapFactory.Options o = new BitmapFactory.Options();
            o.inJustDecodeBounds = true;
            o.inSampleSize = 8;
            o.inPurgeable = true;
            o.inTempStorage = new byte[16000];
            
            BitmapFactory.decodeStream(new FileInputStream(f),null,o);
            
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
            final FileInputStream is = new FileInputStream(f);
            final Bitmap ret = BitmapFactory.decodeStream(is, null, o2);
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
