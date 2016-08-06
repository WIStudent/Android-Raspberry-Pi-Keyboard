package de.tobiastrumm.raspberrykeyboard;

import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.hardware.usb.UsbAccessory;
import android.hardware.usb.UsbManager;
import android.os.ParcelFileDescriptor;
import android.support.annotation.NonNull;
import android.util.Log;

import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;

/**
 * Created by Tobias Trumm on 23.07.2016.
 */
public class UsbConnection {

    private static final String ACTION_USB_PERMISSION = "de.tobiastrumm.raspberrykeyboard.USB_PERMISSION";
    private final static String TAG = UsbConnection.class.getSimpleName();

    public enum Status{
        CONNECTED,
        DISCONNECTED,
        PERMISSION_REQUESTED,
        PERMISSION_DENIED
    }

    public interface StatusChangedListener{
        public void onStatusChanged(UsbConnection.Status status);
    }

    private Status status = Status.DISCONNECTED;

    private Context context;

    UsbAccessory accessory;
    private ParcelFileDescriptor parcelFileDescriptor = null;
    private FileInputStream inputStream = null;
    private FileOutputStream outputStream = null;

    UsbManager usbManager;

    // Usb Device was detached
    BroadcastReceiver detachedReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (UsbManager.ACTION_USB_ACCESSORY_DETACHED.equals(action)) {
                UsbAccessory accessory = intent.getParcelableExtra(UsbManager.EXTRA_ACCESSORY);
                if (accessory != null) {
                        Log.d(TAG, "Device was disconnected. Trying to call closeAccessory()");
                        closeAccessory();
                }
            }
        }
    };

    // Check if permission to connect to the device was granted.
    BroadcastReceiver permissionReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if(ACTION_USB_PERMISSION.equals(action)){
                UsbAccessory accessory = intent.getParcelableExtra(UsbManager.EXTRA_ACCESSORY);

                if(intent.getBooleanExtra(UsbManager.EXTRA_PERMISSION_GRANTED, false)){
                    if(accessory != null){
                        if(status == Status.PERMISSION_REQUESTED){
                            openAccessory();
                        }
                    }
                }
                else{
                    Log.d(TAG, "permission denied for accessory " +  accessory);
                    setStatus(Status.PERMISSION_DENIED);
                }
            }
        }
    };

    private PendingIntent permissionIntent;

    private StatusChangedListener statusChangedListener;

    /**
     * @param context Needed to get the UsbManager
     * @param statusChangedListener Whenever the status of the UsbConnection changes, the onStatusChanged method of the
     *                              StatusChangedListener is called. May be null.
     */
    public UsbConnection(@NonNull Context context, StatusChangedListener statusChangedListener){
        this.context = context;
        this.statusChangedListener = statusChangedListener;
        usbManager = (UsbManager) context.getSystemService(Context.USB_SERVICE);
        permissionIntent = PendingIntent.getBroadcast(context, 0, new Intent(ACTION_USB_PERMISSION), 0);
        context.registerReceiver(permissionReceiver, new IntentFilter(ACTION_USB_PERMISSION));
    }

    private void setStatus(UsbConnection.Status status){
        this.status = status;
        if(statusChangedListener != null){
            statusChangedListener.onStatusChanged(status);
        }
    }

    /**
     * Returns the status of the USB connection.
     * @return UsbConnection.Status
     */
    public Status getStatus(){
        return status;
    }

    /**
     * Connect to a device.
     * @return Status of the UsbConnection.
     */
    public Status connectToDevice(){
        if(status != Status.PERMISSION_REQUESTED && status != Status.CONNECTED){
            UsbAccessory[] accessoryList = usbManager.getAccessoryList();
            if(accessoryList == null) {
                setStatus(Status.DISCONNECTED);
                return status;
            }
            accessory = accessoryList[0];
            usbManager.requestPermission(accessory, permissionIntent);
            setStatus(Status.PERMISSION_REQUESTED);
        }
        return status;
    }


    private void openAccessory(){
        parcelFileDescriptor = usbManager.openAccessory(accessory);
        if (parcelFileDescriptor == null) {
            setStatus(Status.DISCONNECTED);
            return;
        }
        FileDescriptor fileDescriptor = parcelFileDescriptor.getFileDescriptor();
        inputStream = new FileInputStream(fileDescriptor);
        outputStream = new FileOutputStream(fileDescriptor);

        // Register the detachedReceiver.
        context.registerReceiver(detachedReceiver, new IntentFilter(UsbManager.ACTION_USB_ACCESSORY_DETACHED));

        setStatus(Status.CONNECTED);
    }

    /**
     * Disconnect from the device. The connection can be reopened by calling connectToDevice() again.
     */
    public void closeAccessory(){
        if(status == Status.CONNECTED){
            // Close the parcelFileDescriptor
            if(parcelFileDescriptor != null){
                try{
                    parcelFileDescriptor.close();
                } catch (IOException ignored) {}

            }
            parcelFileDescriptor = null;
            inputStream = null;
            outputStream = null;
            // Unregister the detachedReceiver
            context.unregisterReceiver(detachedReceiver);
        }
        setStatus(Status.DISCONNECTED);
    }

    /**
     * Closes the connection to the usb device. To reconnect, a new UsbConnection object
     * must be created.
     */
    public void onDestroy(){
        closeAccessory();
        context.unregisterReceiver(permissionReceiver);
    }


    /**
     * Write bytes to the device
     * @param bytes Array with data that should be written to the attached device.
     * @throws IOException
     * @throws IllegalStateException when UsbConnection is not in state CONNECTED
     */
    public void write(@NonNull byte[] bytes) throws IOException, IllegalStateException {
        if(status == Status.CONNECTED && outputStream != null){
            outputStream.write(bytes);
        }
        else{
            throw new IllegalStateException("Not ready to write. State: " + status);
        }
    }

    /**
     * Read data from the device
     * @param bytes Array that the data should be written to.
     * @return int Number of bytes read.
     * @throws IOException
     * @throws IllegalStateException when UsbConnection is not in state CONNECTED
     */
    public int read(byte[] bytes) throws IOException, IllegalStateException{
        if(status == Status.CONNECTED && inputStream != null){
            return inputStream.read(bytes);
        }
        else{
            throw new IllegalStateException("Not ready to read. State: " + status);
        }
    }
}
