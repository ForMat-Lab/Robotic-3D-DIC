import pyfirmata
import serial.tools.list_ports
import logging

logger = logging.getLogger(__name__)

class ArduinoController:
    """
    A controller class for Arduino boards, using the pyFirmata library.
    """

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
            pin (int): The Arduino pin to set as output.
        """
        if self.board:
            self.output_pins[pin] = self.board.get_pin(f'd:{pin}:o')
            self.set_digital(pin, False)
            logger.info(f"Set up digital output on pin {pin}.")
        else:
            logger.error("Board not connected; cannot setup output pin.")

    def set_digital(self, pin, val):
        """
        Set state of a digital output pin.

        Args:
            pin (int): Pin number.
            val (bool): True for HIGH, False for LOW.
        """
        if pin in self.output_pins:
            self.output_pins[pin].write(val)
            logger.debug(f"Pin {pin} set to {'HIGH' if val else 'LOW'}.")
        else:
            logger.warning(f"Pin {pin} not configured as output.")

    def setup_digital_input(self, pin):
        """
        Setup a digital pin for input and enable reporting.

        Args:
            pin (int): The Arduino pin to set as input.
        """
        if self.board:
            self.input_pins[pin] = self.board.get_pin(f'd:{pin}:i')
            self.input_pins[pin].enable_reporting()
            initial_state = self.read_digital(pin)
            self.prev_states[pin] = initial_state if initial_state is not None else False
        else:
            logger.error("Board not connected; cannot setup input pin.")

    def read_digital(self, pin):
        """
        Read current state of a digital input pin.

        Args:
            pin (int): Pin number.

        Returns:
            bool: Current pin state (True or False).
        """
        if pin in self.input_pins:
            state = self.input_pins[pin].read()
            return bool(state) if state is not None else False
        else:
            logger.warning(f"Pin {pin} not configured as input.")
            return False

    def check_rising_edge(self, pin):
        """
        Check for a rising edge (LOW -> HIGH).

        Args:
            pin (int): Pin to check.

        Returns:
            bool: True if rising edge is detected.
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
        Check for a falling edge (HIGH -> LOW).

        Args:
            pin (int): Pin to check.

        Returns:
            bool: True if falling edge is detected.
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

    