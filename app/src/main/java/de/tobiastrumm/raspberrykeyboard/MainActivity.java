package de.tobiastrumm.raspberrykeyboard;

import android.content.Context;
import android.content.Intent;
import android.hardware.usb.UsbManager;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.util.Log;
import android.view.KeyEvent;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.TextView;

import java.io.IOException;

public class MainActivity extends AppCompatActivity implements UsbConnection.StatusChangedListener{

    private final static String TAG = MainActivity.class.getSimpleName();

    TextView tv_status;
    Button button;

    UsbConnection usbConnection;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tv_status = (TextView) findViewById(R.id.tv_status);

        button = (Button) findViewById(R.id.button);
        button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                showSoftKeyboard(tv_status);
            }
        });

        usbConnection = new UsbConnection(this, this);
        usbConnection.connectToDevice();
    }

    @Override
    protected void onDestroy() {
        if(usbConnection != null){
            usbConnection.onDestroy();
        }
        super.onDestroy();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        if (UsbManager.ACTION_USB_ACCESSORY_ATTACHED.equals(intent.getAction())) {
            usbConnection.connectToDevice();
        }
        super.onNewIntent(intent);
    }

    /**
     * Opens the software keyboard
     * @param view The view that should be focused on
     */
    public void showSoftKeyboard(View view) {
        // Force focus to the view and open the keyboard
        if (view.requestFocus()) {
            InputMethodManager imm = (InputMethodManager)
                    getSystemService(Context.INPUT_METHOD_SERVICE);
            imm.showSoftInput(view, InputMethodManager.SHOW_IMPLICIT);
        }
    }

    /**
     * Handle KeyDown events
     * @param keyCode keycode of the key that was pressed down.
     */
    private void handleKeyDown(int keyCode){
        try {
            byte[] bytes = new byte[3];
            // the first byte holds the event type (0 = key down)
            bytes[0] = 0;
            // the other bytes are holding the keycode
            bytes[1] = (byte) ((keyCode >> 8) & 0xFF);
            bytes[2] = (byte) (keyCode & 0xFF);
            usbConnection.write(bytes);
        } catch (IOException e) {
            Log.d(TAG, "could not send data. IOException");
        } catch (IllegalStateException e) {
            Log.d(TAG, "could not send data. IllegalStateException");
        }
    }

    /**
     * Handle KeyUp events
     * @param keyCode keycode of the key that was released.
     */
    private void handleKeyUp(int keyCode){
        try {
            byte[] bytes = new byte[3];
            // the first byte holds the event type (1 = key up)
            bytes[0] = 1;
            // the other bytes are holding the keycode
            bytes[1] = (byte) ((keyCode >> 8) & 0xFF);
            bytes[2] = (byte) (keyCode & 0xFF);
            usbConnection.write(bytes);
        } catch (IOException e) {
            Log.d(TAG, "could not send data. IOException");
        } catch (IllegalStateException e){
            Log.d(TAG, "could not send data. IllegalStateException");

        }
    }

    @Override
    public boolean dispatchKeyEvent(KeyEvent event) {
        // Intercept all KeyDown and KeyUp events
        if(event.getAction() == KeyEvent.ACTION_DOWN) {
            handleKeyDown(event.getKeyCode());
            return true;
        }
        else if(event.getAction() == KeyEvent.ACTION_UP){
            handleKeyUp(event.getKeyCode());
            return true;
        }
        return super.dispatchKeyEvent(event);
    }


    @Override
    public void onStatusChanged(UsbConnection.Status status) {
        // Update the status TextView whenever the status of the UsbConnection is changed.
        String status_text = getString(R.string.status, status);
        tv_status.setText(status_text);
    }
}
