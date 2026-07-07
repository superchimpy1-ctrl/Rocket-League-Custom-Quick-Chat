from pynput.keyboard import Key, Controller, Listener
import time
import threading

keyboard = Controller()

phrase_t = " Nice Rotation!"
phrase_r = " Your fault."
phrase_f = " Holy optimal!"


scanning_enabled = False


def on_press(key):
    global scanning_enabled
    try:

        if key == Key.f6:
            scanning_enabled = True
            print("Scanning enabled")

        elif key == Key.f7:
            scanning_enabled = False
            print("Scanning disabled")

        elif scanning_enabled:

            if key.char == 'v':
                keyboard.press('t')
                time.sleep(0.1)
                keyboard.release('t')
                keyboard.type(phrase_t)
                keyboard.press(Key.enter)
                keyboard.release(Key.enter)

            elif key.char == 'r':
                keyboard.press('t')
                time.sleep(0.1)
                keyboard.release('t')
                keyboard.type(phrase_r)
                keyboard.press(Key.enter)
                keyboard.release(Key.enter)

            elif key.char == 'f':
                keyboard.press('t')
                time.sleep(0.1)
                keyboard.release('t')
                keyboard.type(phrase_f)
                keyboard.press(Key.enter)
                keyboard.release(Key.enter)

    except AttributeError:
        pass
# Function to stop the program when 'c' is typed in the terminal
def stop_program():
    global running
    while True:
        user_input = input()
        if user_input == 'c':
            running = False
            listener.stop()
# Set up the listener to constantly wait for key presses
running = True
listener = Listener(on_press=on_press)
listener.start()  # Start the listener
# Start the thread to listen for user input in the terminal
input_thread = threading.Thread(target=stop_program)
input_thread.start()