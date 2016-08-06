# Android Raspberry Pi Keyboard
&copy; 2016 [Tobias Trumm](mailto:tobiastrumm@uni-muenster.de) licensed under MIT license

## Info
Use your Android device as an USB keyboard on your Raspberry Pi (or other Linux devices).

I wrote this app mainly because I wanted to learn how to communicate between Android and other devices over USB. Do not expect it to work flawlessly, not all keys will work. If you are looking for a simple way to control your Raspberry Pi from your Android device there are probably better solutions out there. Depending on the software keyboard on your Android device this app will work better or worse. I have got the best results using [Hacker's Keyboard](https://play.google.com/store/apps/details?id=org.pocketworkstation.pckeyboard).

## Python Dependencies
- [python-evdev](https://python-evdev.readthedocs.io/)
- [pyusb](https://walac.github.io/pyusb/)
- [pyudev](https://pyudev.readthedocs.io/)

## Usage
1. Install the app on your Android device and copy the python scripts from the `linux_client/` directory to your Raspberry Pi.
2. Attach your Android device to your Raspberry Pi with an USB cable.
3. Get the vendor ID of your Android device. Open a terminal and execute `lsusb`. You will see a list of USB devices with their vendor and product ID. The first 4 characters are the vendor ID.
4. Start the `accessory.py` script with `sudo python accessory.py xxxx`. Replace `xxxx` with your vendor ID.
5. A message asking for permission to use the USB connection should have appeared on your Android device. Accept it. Now you should be able to use your Android device as a keyboard.
6. To exit the python script, use `Ctrl` + `c`