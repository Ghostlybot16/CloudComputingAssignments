from google.cloud import pubsub_v1  # Import Google Cloud Pub/Sub library
import os  # For environment variable manipulation
import glob  # For locating files
import json  # For serializing data
import csv  # For reading CSV files

# Locate the service account JSON file to set Google Cloud credentials
credentials_file = r"C:\\UniveristyAssignments\\CloudComputing\\Assignment1\\csvReader\\cloud-pubsub-test-449001-f7e393bceee3.json"
if credentials_file:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file  # Set credentials as an environment variable

# Define Google Cloud project and topic names
gcp_project_id = "cloud-pubsub-test-449001"
pubsub_topic = "csvSerializer"

# Initialize the Pub/Sub publisher client
publisher = pubsub_v1.PublisherClient()

# Create the full topic path
topic_path = publisher.topic_path(gcp_project_id, pubsub_topic)

# Function to read CSV and publish each row as a Pub/Sub message
def publish_csv_records(file_path):
    try:
        print(f"Processing CSV file: {file_path}")  # Indicate the start of file processing
        with open(file_path, mode="r") as csv_file:
            # Create a CSV reader to process the file row by row
            csv_reader = csv.reader(csv_file)
            headers = next(csv_reader)  # Extract the headers from the first row

            for row in csv_reader:  # Loop through the remaining rows
                # Map CSV row data to headers to form a dictionary
                message_dict = {headers[index]: row[index] for index in range(len(headers))}
                # Serialize the dictionary into a JSON string
                message_json = json.dumps(message_dict).encode("utf-8")

                # Publish the serialized message to Pub/Sub
                publish_future = publisher.publish(topic_path, message_json)

                # Wait for the publish to complete to ensure delivery
                publish_future.result()
                print(f"Published message: {message_json}")  # Log the published message
        print("All records successfully published.")  # Indicate completion of publishing
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}. Please check the file path.")
    except Exception as e:
        print(f"An error occurred while publishing messages: {e}")  # Log any errors

# Path to the CSV file
csv_file_path = r"C:\\UniveristyAssignments\\CloudComputing\\Assignment1\\csvReader\\Labels.csv"

# Execute the function to process the CSV and publish messages
publish_csv_records(csv_file_path)
