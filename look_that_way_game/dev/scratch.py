import sys
import select
import time
import threading

def print_remaining_time(timeout, stop_event):
    """ Function to print remaining time every second """
    for remaining in range(timeout, 0, -1):
        if stop_event.is_set():  # Check if the countdown should be stopped
            print("\nCountdown stopped.")
            return
        print(f"\nTime remaining: {remaining} seconds", end='\r')
        time.sleep(1)
    print("Time's up! No input received within the given time.")

def get_user_input_with_timeout(timeout=3):
    """ Function to get user input with a timeout and display remaining time every second """
    print(f"You have {timeout} seconds to enter your input:")
    
    # Create an event to signal when to stop the countdown
    stop_event = threading.Event()

    # Start a background thread to print the countdown
    countdown_thread = threading.Thread(target=print_remaining_time, args=(timeout, stop_event))
    countdown_thread.start()

    # Wait for input for 'timeout' seconds
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)

    if rlist:
        user_input = sys.stdin.readline().strip()  # Read the input
        stop_event.set()  # Stop the countdown thread once input is received
        print(f"\nUser input: {user_input}")
        return user_input
    else:
        stop_event.set()  # Stop the countdown thread if no input is received
        print(f"\nTime's up! No input received within {timeout} seconds.")
        return None

# Example usage
timeout = 10  # Set the timeout to 3 seconds


# Capture user input with timeout and countdown
user_input = get_user_input_with_timeout(timeout)

if user_input:
    print(f"User entered: {user_input}")
else:
    print("Proceeding without user input.")

# You can continue the program logic here
time.sleep(1)  # Simulating program continuation
