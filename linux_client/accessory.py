import usb.core
import usb.util
import time
import struct
import sys

from attribs import *
from evdev import UInput, ecodes
import pyudev

# Insert the vendor ID of your android device here
ACCESSORY_VID = 0x18D1
ACCESSORY_PID = (0x2D00, 0x2D01, 0x2D04, 0x2D05)

# mapping between android keycodes.h and linux/input-event-codes.h
KEYCODE_TABLE = {
    7: ecodes.KEY_0,
    8: ecodes.KEY_1,
    9: ecodes.KEY_2,
    10: ecodes.KEY_3,
    11: ecodes.KEY_4,
    12: ecodes.KEY_5,
    13: ecodes.KEY_6,
    14: ecodes.KEY_7,
    15: ecodes.KEY_8,
    16: ecodes.KEY_9,

    19: ecodes.KEY_UP,
    20: ecodes.KEY_DOWN,
    21: ecodes.KEY_LEFT,
    22: ecodes.KEY_RIGHT,

    29: ecodes.KEY_A,
    30: ecodes.KEY_B,
    31: ecodes.KEY_C,
    32: ecodes.KEY_D,
    33: ecodes.KEY_E,
    34: ecodes.KEY_F,
    35: ecodes.KEY_G,
    36: ecodes.KEY_H,
    37: ecodes.KEY_I,
    38: ecodes.KEY_J,
    39: ecodes.KEY_K,
    40: ecodes.KEY_L,
    41: ecodes.KEY_M,
    42: ecodes.KEY_N,
    43: ecodes.KEY_O,
    44: ecodes.KEY_P,
    45: ecodes.KEY_Q,
    46: ecodes.KEY_R,
    47: ecodes.KEY_S,
    48: ecodes.KEY_T,
    49: ecodes.KEY_U,
    50: ecodes.KEY_V,
    51: ecodes.KEY_W,
    52: ecodes.KEY_X,
    53: ecodes.KEY_Y,
    54: ecodes.KEY_Z,
    55: ecodes.KEY_COMMA,
    56: ecodes.KEY_DOT,
    57: ecodes.KEY_LEFTALT,
    58: ecodes.KEY_RIGHTALT,
    59: ecodes.KEY_LEFTSHIFT,
    60: ecodes.KEY_RIGHTSHIFT,
    61: ecodes.KEY_TAB,
    62: ecodes.KEY_SPACE,

    66: ecodes.KEY_ENTER,
    67: ecodes.KEY_BACKSPACE,

    69: ecodes.KEY_MINUS,
    70: ecodes.KEY_EQUAL,
    71: ecodes.KEY_LEFTBRACE,
    72: ecodes.KEY_RIGHTBRACE,
    73: ecodes.KEY_BACKSLASH,
    74: ecodes.KEY_SEMICOLON,
    75: ecodes.KEY_APOSTROPHE,
    76: ecodes.KEY_SLASH,

    92: ecodes.KEY_PAGEUP,
    93: ecodes.KEY_PAGEDOWN,

    111: ecodes.KEY_ESC,

    113: ecodes.KEY_LEFTCTRL,
    114: ecodes.KEY_RIGHTCTRL,
    115: ecodes.KEY_CAPSLOCK,
    116: ecodes.KEY_SCROLLLOCK,

    120: ecodes.KEY_SYSRQ,
    121: ecodes.KEY_BREAK,

    124: ecodes.KEY_INSERT,
    125: ecodes.KEY_FORWARD,

    131: ecodes.KEY_F1,
    132: ecodes.KEY_F2,
    133: ecodes.KEY_F3,
    134: ecodes.KEY_F4,
    135: ecodes.KEY_F5,
    136: ecodes.KEY_F6,
    137: ecodes.KEY_F7,
    138: ecodes.KEY_F8,
    139: ecodes.KEY_F9,
    140: ecodes.KEY_F10,
    141: ecodes.KEY_F11,
    142: ecodes.KEY_F12,
    143: ecodes.KEY_NUMLOCK,
    144: ecodes.KEY_NUMERIC_0,
    145: ecodes.KEY_NUMERIC_1,
    146: ecodes.KEY_NUMERIC_2,
    147: ecodes.KEY_NUMERIC_3,
    148: ecodes.KEY_NUMERIC_4,
    149: ecodes.KEY_NUMERIC_5,
    150: ecodes.KEY_NUMERIC_6,
    151: ecodes.KEY_NUMERIC_7,
    152: ecodes.KEY_NUMERIC_8,
    153: ecodes.KEY_NUMERIC_9,
}


def get_evdev_keycode(android_keycode):
    """
    Get the linux keycode that correspond to the android keycode
    :param android_keycode: integer android keycode
    :return: integer linux keycode or -1 of no corresponding keycode exists.
    """
    try:
        return KEYCODE_TABLE[android_keycode]
    except KeyError:
        return -1


def find_accessory():
    """
    Find the accessory device and open its input and output endpoints.
    :return: A dictionary. Access input endpoint with key "ep_in" and output endpoint with "ep_out"
    """
    dev = usb.core.find(idVendor=ACCESSORY_VID)
    if dev is None:
        raise ValueError('Device not found')

    print("Device found")

    if dev.idProduct in ACCESSORY_PID:
        print("Device is in accessory mode")
    else:
        print("Device is not in accessory mode yet")

        activate_accessory_mode(dev)

        # By activating accessory mode, the android device has changed its product_id. That's why we have to search for
        # the device again.
        dev = usb.core.find(idVendor=ACCESSORY_VID)

        if dev is None:
            raise ValueError('Device not found')

        if dev.idProduct in ACCESSORY_PID:
            print("Device is in accessory mode")
        else:
            # if the device is still not in accessory mode, something went wrong
            raise ValueError("")

    dev.set_configuration()
    # Setting the configuration will result in the UsbManager starting an "accessory connected"
    # intent on the Android device. That's why a small delay is required before communication can start
    time.sleep(1)

    # Get the input and output endpoints for communication
    cfg = dev.get_active_configuration()
    intf = cfg[(0, 0)]

    ep_in = usb.util.find_descriptor(
        intf,
        custom_match=lambda e:
        usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)

    ep_out = usb.util.find_descriptor(
        intf,
        custom_match=lambda e:
        usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)

    # Make sure that the enpoints were found
    assert ep_in is not None
    assert ep_out is not None

    # Return the endpoints
    return {"ep_in": ep_in, "ep_out": ep_out}


def activate_accessory_mode(dev):
    """
    Tries to put the accessory device into accessory_mode
    :param dev: Device that should be put into accessory_mode
    """

    # Activate the accessory mode of the android device by sending the right conntrol commands.
    # See https://source.android.com/devices/accessories/aoa.html
    version = dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_IN, 51, 0, 0, 2)
    version = struct.unpack('<H', version)[0]
    if version < 1:
        raise ValueError("Device returned an unsupported protocol version (Version {}".format(version))

    # Send the MANUFACTURER, MODEL_NAME, DESCRIPTION; VERSION, URL and SERIAL_NUMBER information to the device
    assert dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_OUT, 52, 0, 0, MANUFACTURER) == len(MANUFACTURER)
    assert dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_OUT, 52, 0, 1, MODEL_NAME) == len(MODEL_NAME)
    assert dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_OUT, 52, 0, 2, DESCRIPTION) == len(DESCRIPTION)
    assert dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_OUT, 52, 0, 3, VERSION) == len(VERSION)
    assert dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_OUT, 52, 0, 4, URL) == len(URL)
    assert dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_OUT, 52, 0, 5, SERIAL_NUMBER) == len(
        SERIAL_NUMBER)

    # Final step to activate the accessory mode
    dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_OUT, 53, 0, 0, None)

    # Wait to give the android device some time to switch into accessory mode.
    time.sleep(1)


def read_data(ep_in):
    """
    Read the transmitted android keycodes from the input endpoint and trigger the corresponding key presses in linux.
    :param ep_in: input endpoint of the accessory device.
    """
    ui = UInput()
    while True:
        try:
            data = ep_in.read(3)
            keycode = data[1] * 0xFF + data[2]
            evdev_keycode = get_evdev_keycode(keycode)
            if data[0] == 0:
                print("Key down {}".format(keycode))
                if evdev_keycode != -1:
                    ui.write(ecodes.EV_KEY, evdev_keycode, 1)
                    ui.syn()
            elif data[0] == 1:
                print("Key up {}".format(keycode))
                if evdev_keycode != -1:
                    ui.write(ecodes.EV_KEY, evdev_keycode, 0)
                    ui.syn()
        except usb.core.USBError as e:
            # ignore exceptions caused by read timeout
            if e.errno == 110:
                pass
            else:
                print("failed to read input")
                print(e)
                break


def handle_attached_device():
    """
    Try to find the accessory device and start receiving keycodes from it if it is attached.
    The function returns if the device could not be found or if it was detached.
    """
    try:
        # try to get the endpoint and start reading data sent from the android device
        endpoints = find_accessory()
        ep_in = endpoints["ep_in"]
        time.sleep(1)
        read_data(ep_in)
    except usb.core.USBError as e:
        # in case the device was detached.
        print(e)
    except ValueError as e:
        # in case find_accessory() didn't find a fitting device.

        print(e)


def main():
    # In case the vendor ID was passed as argument.
    if len(sys.argv) == 2:
        global ACCESSORY_VID
        ACCESSORY_VID = int(sys.argv[1], 16)

    print("Used vendor ID: {}".format(hex(ACCESSORY_VID)))

    # in case the device was attached before this program was started.
    handle_attached_device()

    # use pyudev to detect usb events like plugging in a new device
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='usb')
    # Whenever a usb device is plugged in, try to establish the connection.
    for device in iter(monitor.poll, None):
        if device.action == 'add':
            print("Device connected:")
            handle_attached_device()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
