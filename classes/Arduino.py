import pyfirmata
import logging
import time

class ArduinoController:
    def __init__(self, port="COM3"):
        """
        Initialize the connection to the Arduino board using the specified port.
        """
        self.pins = {}
        self.prev_states = {}
        try:
            self.board = pyfirmata.Arduino(port)
            self.it = pyfirmata.util.Iterator(self.board)
            self.it.start()
            logging.info(f"Connected to Arduino on port {port}")
        except Exception as e:
            logging.error(f"Failed to connect to Arduino: {e}")
            self.board = None

    def setup_digital_input(self, pin):
        """
        Setup a digital pin for input.
        """
        if self.board:
            self.pins[pin] = self.board.get_pin(f'd:{pin}:i')  # d for digital, i for input
            self.prev_states[pin] = None  # Initialize the previous state as None
            logging.info(f"Set up digital input on pin {pin}")
        else:
            logging.error("Board is not connected. Cannot setup pin.")

    def read_digital(self, pin):
        """
        Read the state of a configured digital pin. Returns True if the pin is HIGH, False if LOW.
        """
        if pin in self.pins:
            return self.pins[pin].read()
        else:
            logging.warning(f"Pin {pin} not configured. Call setup_digital_input first.")
            return None

    def check_rising_edge(self, pin):
        """
        Check for a rising edge (LOW to HIGH transition) on the specified pin.
        Returns True if a rising edge is detected, otherwise False.
        """
        if pin in self.pins:
            current_state = self.pins[pin].read()
            if current_state is True and self.prev_states[pin] is False:
                self.prev_states[pin] = current_state
                return True
            self.prev_states[pin] = current_state
        return False

    def close(self):
        """
        Close the connection to the Arduino board.
        """
        if self.board:
            self.board.exit()
            logging.info("Connection to the board closed")

# # Example usage
# if __name__ == "__main__":
#     try:
#         board = ArduinoController(port="COM4")
#         board.setup_digital_input(6)
#         board.setup_digital_input(7)
#         while True:
#             state_6 = board.read_digital(6)
#             state_7 = board.read_digital(7)
#             print(f"Pin 6: {state_6}, Pin 7: {state_7}")
#             time.sleep(0.1)  # Add a delay to avoid flooding the output
#     except KeyboardInterrupt:
#         print("KeyboardInterrupt")
#     finally:
#         board.close()