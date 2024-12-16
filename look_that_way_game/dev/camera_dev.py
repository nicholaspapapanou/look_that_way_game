import cv2
import time

# Initialize video capture object (0 is typically the default camera)
cap = cv2.VideoCapture(0)

# Check if the camera is opened successfully
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Set the duration for displaying the camera feed (in seconds)
display_duration = 10  # Example: display for 10 seconds
init_time = time.time()  # Record the start time

# Loop to capture and display frames
while time.time() - init_time < display_duration:
    ret, frame = cap.read()  # Read a frame from the camera
    if not ret:
        print("Error: Failed to capture image.")
        break
    
    # Display the frame
    cv2.imshow('Camera Feed', frame)
    
    # Wait for 1ms and check if 'q' is pressed to exit early
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture object and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()