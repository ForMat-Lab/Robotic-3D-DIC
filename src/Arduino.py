import pyfirmata
import serial.tools.list_ports
import logging

logger = logging.getLogger(__name__)

class ArduinoController:
    """
    A controller class for Arduino boards, using the pyFirmata library.
    Enhanced to detect Arduino devices based on VID/PID.
    """

    # Define known Arduino VID and PID tuples
    ARDUINO_VID_PID = [
    ('2341', '0043'),  # Official Arduino Uno
    ('2341', '0001'),  # Official Arduino Uno (Old)
    ('2A03', '0043'),  # Arduino Uno R3 (later versions)
    ('2341', '0243'),  # Arduino Mega 2560 R3
    ('2A03', '0044'),  # Arduino Mega 2560 R3 (later versions)
    ('2341', '8036'),  # Arduino Leonardo
    ('2A03', '8036'),  # Arduino Leonardo (later versions)
    ('2341', '8037'),  # Arduino Micro
    ('2A03', '8037'),  # Arduino Micro (later versions)
    ('2341', '824E'),  # Arduino Zero (Programming Port)
    ('2341', '814E'),  # Arduino Zero (Native USB Port)
    ('1A86', '7523'),  # CH340-Based Clones
    ('1A86', '5523'),  # CH341-Based Clones (alternate PID)
    ('0403', '6001'),  # FTDI FT232R-Based Clones
    ('067B', '2303'),  # Prolific PL2303-Based Clones
    ('10C4', 'EA60'),  # Silicon Labs CP2102-Based Clones
    ('10C4', 'EA70'),  # Silicon Labs CP2102N-Based Clones
    ('10C4', 'EA61'),  # Silicon Labs CP2104-Based Clones
    ('10C4', 'EA62'),  # Silicon Labs CP2104-Based Clones
    ('16C0', '0483'),  # Teensyduino (Teensy 2.0)
    ('16C0', '0485'),  # Teensyduino (Teensy 3.x and 4.x)
    # Add more VID/PID tuples for newer boards and variants as needed
]

    def __init__(self, port=None):
        """
        Initialize the connection to the Arduino board using the specified port.

        Args:
            port (str or None): COM port or device file for Arduino. If None, auto-detect.
        """
        self.board = None
        self.input_pins = {}
        self.output_pins = {}
        self.prev_states = {}

        if port is None:
            port = self.auto_detect_arduino_port()

        if port:
            try:
                self.board = pyfirmata.Arduino(port)
                self.it = pyfirmata.util.Iterator(self.board)
                self.it.start()
                logger.info(f"Connected to Arduino on port {port}")
            except Exception as e:
                logger.error(f"Failed to connect to Arduino on port {port}: {e}")
        else:
            logger.error("No Arduino port provided or detected. Board is not connected.")

    def auto_detect_arduino_port(self):
        """
        Auto-detect the Arduino COM port by scanning available ports
        and matching known VID/PID pairs.

        Returns:
            str or None: The detected port name, or None if not found.
        """
        ports = list(serial.tools.list_ports.comports())
        arduino_ports = []

        for port_info in ports:
            # Extract VID and PID in hexadecimal
            vid = port_info.vid
            pid = port_info.pid

            if vid is None or pid is None:
                continue  # Skip ports without VID/PID

            # Convert to hexadecimal string without '0x' and leading zeros
            vid_hex = format(vid, '04X')
            pid_hex = format(pid, '04X')

            # Check if VID/PID matches known Arduino devices
            if (vid_hex, pid_hex) in self.ARDUINO_VID_PID:
                arduino_ports.append(port_info.device)
                logger.info(f"Detected Arduino on port: {port_info.device} (VID: {vid_hex}, PID: {pid_hex})")

        if len(arduino_ports) == 1:
            return arduino_ports[0]
        elif len(arduino_ports) > 1:
            logger.warning("Multiple Arduino devices detected:")
            for idx, port in enumerate(arduino_ports):
                logger.warning(f"{idx + 1}: {port}")
            # Prompt the user to select a port
            selected_port = self.prompt_user_to_select_port(arduino_ports)
            return selected_port
        else:
            logger.error("No Arduino devices detected based on VID/PID.")
            return None

    def prompt_user_to_select_port(self, arduino_ports):
        """
        Prompt the user to select one Arduino port from the detected list.

        Args:
            arduino_ports (list of str): List of detected Arduino port names.

        Returns:
            str or None: The selected port name, or None if invalid selection.
        """
        print("Multiple Arduino devices detected. Please select one:")
        for idx, port in enumerate(arduino_ports):
            print(f"{idx + 1}: {port}")

        try:
            selection = int(input("Enter the number corresponding to your Arduino: "))
            if 1 <= selection <= len(arduino_ports):
                selected_port = arduino_ports[selection - 1]
                logger.info(f"User selected Arduino on port: {selected_port}")
                return selected_port
            else:
                logger.error("Invalid selection.")
                return None
        except ValueError:
            logger.error("Invalid input. Please enter a number.")
            return None

    def auto_detect_arduino_port_legacy(self):
        """
        Auto-detect the Arduino COM port by scanning available ports
        and trying to connect to each.

        Returns:
            str or None: Detected port name, or None if not found.
        """
        ports = list(serial.tools.list_ports.comports())
        for port_info in ports:
            try:
                test_board = pyfirmata.Arduino(port_info.device)
                test_board.exit()
                logger.info(f"Arduino detected on port: {port_info.device}")
                return str(port_info.device)
            except Exception:
                continue
        logger.error("Arduino not detected on any port.")
        return None
    def setup_digital_output(self, pin):
        """
        Setup a digital pin for output.

        Args:
            pin (int): The Arduino digital pin number for output.
        """
        if self.board:
            try:
                self.output_pins[pin] = self.board.get_pin(f'd:{pin}:o')
                self.set_digital(pin, False)
                logger.info(f"Set up digital output on pin {pin}.")
            except Exception as e:
                logger.error(f"Failed to set up digital output on pin {pin}: {e}")
        else:
            logger.error("Board is not connected. Cannot setup digital output pin.")

    def set_digital(self, pin, val):
        """
        Set the state of a configured digital pin to HIGH or LOW.

        Args:
            pin (int): The pin number to set.
            val (bool): True for HIGH, False for LOW.
        """
        if pin in self.output_pins:
            try:
                self.output_pins[pin].write(val)
                logger.debug(f"Pin {pin} set to {'HIGH' if val else 'LOW'}.")
            except Exception as e:
                logger.error(f"Failed to set pin {pin} to {'HIGH' if val else 'LOW'}: {e}")
        else:
            logger.warning(f"Pin {pin} not configured as output.")

    def setup_digital_input(self, pin):
        """
        Setup a digital pin for input and enable reporting.

        Args:
            pin (int): The Arduino digital pin number for input.
        """
        if self.board:
            try:
                self.input_pins[pin] = self.board.get_pin(f'd:{pin}:i')
                self.input_pins[pin].enable_reporting()
                initial_state = self.read_digital(pin)
                self.prev_states[pin] = initial_state if initial_state is not None else False
                logger.info(f"Set up digital input on pin {pin}.")
            except Exception as e:
                logger.error(f"Failed to set up digital input on pin {pin}: {e}")
        else:
            logger.error("Board is not connected. Cannot setup digital input pin.")

    def read_digital(self, pin):
        """
        Read the current state (True/False) of the specified input pin.

        Args:
            pin (int): The pin number to read.

        Returns:
            bool: The current state of the pin, or False if not configured / None.
        """
        if pin in self.input_pins:
            try:
                state = self.input_pins[pin].read()
                return bool(state) if state is not None else False
            except Exception as e:
                logger.error(f"Failed to read digital pin {pin}: {e}")
                return False
        else:
            logger.warning(f"Pin {pin} not configured as input.")
            return False

    def check_rising_edge(self, pin):
        """
        Check for a rising edge (LOW -> HIGH transition) on the specified pin.

        Args:
            pin (int): The pin number to check.

        Returns:
            bool: True if a rising edge is detected, False otherwise.
        """
        if pin not in self.input_pins:
            logger.warning(f"Pin {pin} not configured as input.")
            return False

        current_state = self.read_digital(pin)
        prev_state = self.prev_states.get(pin, current_state)
        self.prev_states[pin] = current_state

        if not prev_state and current_state:
            logger.debug(f"Rising edge detected on pin {pin}")
            return True
        return False

    def check_falling_edge(self, pin):
        """
        Check for a falling edge (HIGH -> LOW transition) on the specified pin.

        Args:
            pin (int): The pin number to check.

        Returns:
            bool: True if a falling edge is detected, False otherwise.
        """
        if pin not in self.input_pins:
            logger.warning(f"Pin {pin} not configured as input.")
            return False

        current_state = self.read_digital(pin)
        prev_state = self.prev_states.get(pin, current_state)
        self.prev_states[pin] = current_state

        if prev_state and not current_state:
            logger.debug(f"Falling edge detected on pin {pin}")
            return True
        return False

    def close(self):
        """
        Close the connection to the Arduino board if open.
        """
        if self.board:
            try:
                self.board.exit()
                logger.info("Connection to Arduino board closed.")
            except Exception as e:
                logger.error(f"Error while closing Arduino connection: {e}")

# Unit test for the ArduinoController class
if __name__ == "__main__":
    import logging
    import time

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def test_arduino_controller(input_pin = 6, output_pin = 2):
        """
        A test function to initialize the ArduinoController, set up digital input and output pins,
        read their states, and blink an signal on pin {output_pin}.
        """
        try:
            # Step 1: Initialize the ArduinoController (with auto-detect port)
            arduino = ArduinoController()
            if arduino.board is None:
                logging.error("Failed to initialize Arduino. Exiting test.")
                return

            # Step 2: Set up digital input pins
            arduino.setup_digital_input(input_pin)
            logging.info(f"Digital input set up on pin {input_pin}.")

            # Step 3: Set up digital output and blink signal
            arduino.setup_digital_output(output_pin)
            logging.info(f"Digital output set up on pin {output_pin}. Beginning to blink signal.")

            print(f"Reading digital pin {input_pin} and blinking signal on pin {output_pin}. Press 'Ctrl + C' to stop.")
            while True:
                # Blink signal
                arduino.set_digital(output_pin, True)
                logging.info(f"Signal on pin {output_pin} set to HIGH")
                time.sleep(1)

                arduino.set_digital(output_pin, False)
                logging.info(f"Signal on pin {output_pin} set to LOW")
                time.sleep(1)

                # Read state of digital input pin input_pin
                state_input_pin = arduino.read_digital(6)
                logging.info(f"Pin 6 state: {state_input_pin}")

        except KeyboardInterrupt:
            logging.info("Test interrupted by user.")

        except Exception as e:
            logging.error(f"An error occurred during the Arduino test: {e}")

        finally:
            # Step 4: Close the Arduino connection
            if arduino.board:
                arduino.close()
                logging.info("Arduino connection closed.")

    # Run the test
    test_arduino_controller()