import signal  # For handling system signals like Ctrl+C
from google.cloud import pubsub_v1  # Google Cloud Pub/Sub client library
import os  # For setting environment variables
import glob  # For locating files
import json  # For processing JSON data
import sys  # For exiting the script

# Locate the credentials JSON file to set up Google Cloud authentication
credentials_file = r"C:\\UniveristyAssignments\\CloudComputing\\Assignment1\\csvReader\\cloud-pubsub-test-449001-f7e393bceee3.json"
if credentials_file:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file  # Set the credentials as an environment variable

# Define Google Cloud project and subscription details
gcp_project = "cloud-pubsub-test-449001"
pubsub_subscription = "csvSerializer-sub"

# Initialize the Pub/Sub subscriber client
subscriber = pubsub_v1.SubscriberClient()

# Build the full subscription path
subscription_path = subscriber.subscription_path(gcp_project, pubsub_subscription)

# Flag for gracefully shutting down the subscriber
should_exit = False

# Function to process received messages
def handle_message(message):
    """Callback function to process Pub/Sub messages."""
    print("\nMessage received!")
    try:
        # Decode the message data and deserialize it from JSON
        message_content = json.loads(message.data.decode("utf-8"))
        print("Deserialized Message Content:")
        # Log each key-value pair in the message
        for key, value in message_content.items():
            print(f"  {key}: {value}")
        message.ack()  # Acknowledge the message to indicate successful processing
        print("Message acknowledged.")
    except json.JSONDecodeError as e:
        # Handle cases where the message is not valid JSON
        print(f"Error decoding message: {e}")
        message.nack()  # Reject the message so it can be retried later

# Signal handler to handle Ctrl+C (SIGINT) gracefully
def signal_handler(sig, frame):
    """Handles shutdown signals to gracefully exit the script."""
    global should_exit
    print("\nShutdown signal received. Preparing to exit...")
    should_exit = True  # Set the exit flag to True
    sys.exit(0)  # Exit the script

# Attach the signal handler to Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

print(f"Listening for messages on {subscription_path}...\n")

# Start listening to messages
with subscriber:
    # Subscribe to the Pub/Sub subscription and register the message handler
    pull_future = subscriber.subscribe(subscription_path, callback=handle_message)
    try:
        # Keep the script running until a shutdown signal is received
        while not should_exit:
            pass  # Keep the loop running to listen for messages
    except Exception as error:
        # Log errors that occur during message processing
        print(f"An error occurred: {error}")
        pull_future.cancel()  # Cancel the subscription listener
        pull_future.result()  # Ensure any exceptions are properly raised
