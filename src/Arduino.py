import pyfirmata
import serial.tools.list_ports
import logging
import time

class ArduinoController:
    def __init__(self, port=None):
        """
        Initialize the connection to the Arduino board using the specified port.
        """
        self.input_pins = {}
        self.output_pins = {}
        self.prev_states = {}

        if port is None:
            port = self.auto_detect_arduino_port()  # Auto-detect the port if not provided

        if port:
            try:
                self.board = pyfirmata.Arduino(port)
                self.it = pyfirmata.util.Iterator(self.board)
                self.it.start()
                logging.info(f"Connected to Arduino on port {port}")
            except Exception as e:
                logging.error(f"Failed to connect to Arduino: {e}")
                self.board = None
        else:
            logging.error("No Arduino found. Please specify a port.")

    def auto_detect_arduino_port(self):
        """
        Auto-detect the Arduino COM port by scanning available ports and trying to connect.
        """
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            try:
                # Try to connect to each available port
                board = pyfirmata.Arduino(port.device)
                board.exit()  # Immediately close the connection after detection
                logging.info(f"Arduino detected on port: {port.device}")
                return str(port.device)
            except Exception:
                continue
        logging.error("Arduino not detected on any port.")
        return None

    def setup_digital_output(self, pin: int):
        """
        Setup a digital pin for output.
        """
        if self.board:
            self.output_pins[pin] = self.board.get_pin(f'd:{pin}:o')  # d for digital, o for output
            self.set_digital(pin, False)
            logging.info(f"Set up digital output on pin {pin} with initial state {self.prev_states[pin]}")
        else:
            logging.error("Board is not connected. Cannot setup pin.")

    def set_digital(self, pin: int, val: bool):
        """
        Set the state of a configured digital pin.
        """
        if pin in self.output_pins:
            self.output_pins[pin].write(val)
        else:
            logging.warning(f"Pin {pin} not configured. Call setup_digital_output first.")

    def setup_digital_input(self, pin: int):
        """
        Setup a digital pin for input.
        """
        if self.board:
            self.input_pins[pin] = self.board.get_pin(f'd:{pin}:i')  # d for digital, i for input
            self.input_pins[pin].enable_reporting()
            # Initialize previous state
            initial_state = self.read_digital(pin)
            self.prev_states[pin] = initial_state if initial_state is not None else False
            logging.info(f"Set up digital input on pin {pin}.")
        else:
            logging.error("Board is not connected. Cannot setup pin.")

    def read_digital(self, pin: int):
        """
        Read the state of a configured digital pin.
        """
        if pin in self.input_pins:
            state = self.input_pins[pin].read()
            if state is None:
                return False  # Default to False if state is None
            return bool(state)
        else:
            logging.warning(f"Pin {pin} not configured. Call setup_digital_input first.")
            return False

    def check_rising_edge(self, pin: int):
        """
        Check for a rising edge (LOW to HIGH transition) on the specified pin.
        Returns True if a rising edge is detected, otherwise False.
        """
        if pin in self.input_pins:
            current_state = self.read_digital(pin)
            prev_state = self.prev_states.get(pin, current_state)
            self.prev_states[pin] = current_state
            if prev_state == False and current_state == True:
                logging.debug(f"Rising edge detected on pin {pin}")
                return True
        else:
            logging.warning(f"Pin {pin} not configured. Call setup_digital_input first.")
        return False

    def check_falling_edge(self, pin: int):
        """
        Check for a falling edge (HIGH to LOW transition) on the specified pin.
        Returns True if a falling edge is detected, otherwise False.
        """
        if pin in self.input_pins:
            current_state = self.read_digital(pin)
            prev_state = self.prev_states.get(pin, current_state)
            self.prev_states[pin] = current_state
            if prev_state == True and current_state == False:
                logging.debug(f"Falling edge detected on pin {pin}")
                return True
        else:
            logging.warning(f"Pin {pin} not configured. Call setup_digital_input first.")
        return False

    def close(self):
        """
        Close the connection to the Arduino board.
        """
        if self.board:
            self.board.exit()
            logging.info("Connection to the Arduino board closed")

# Unit test for the ArduinoController class
if __name__ == "__main__":
    import logging
    import time

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def test_arduino_controller():
        """
        A test function to initialize the ArduinoController, set up digital input pins,
        and read their states.
        """
        try:
            # Step 1: Initialize the ArduinoController (with auto-detect port)
            arduino = ArduinoController()
            if arduino.board is None:
                logging.error("Failed to initialize Arduino. Exiting test.")
                return

            # Step 2: Set up digital input pins (using pin 6 as an example)
            arduino.setup_digital_input(6)
            logging.info("Digital input set up on pin 6.")

            # Step 3: Start reading the digital pin state
            print("Reading digital pin states. Press 'Ctrl + C' to stop.")
            while True:
                state_6 = arduino.read_digital(6)
                logging.info(f"Pin 6 state: {state_6}")
                time.sleep(1)  # Add a delay to avoid flooding the output

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