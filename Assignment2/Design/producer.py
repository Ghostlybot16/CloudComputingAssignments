from google.cloud import pubsub_v1  # pip install google-cloud-pubsub
import glob  # for searching for JSON file
import json
import os
import csv

#Search for the JSON service account key
files = glob.glob("*.json")
if files:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = files[0]
else:
    print("❌ No service account JSON found!")
    exit()

#Set the project_id with your project ID
project_id = "argon-tractor-449801-j7"
topic_name = "design-CSV-Records"

#Create a publisher and get the topic path for the publisher
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)
print(f"Publishing messages to {topic_path}.")

#Path to the CSV file
file_path = "Labels.csv"

#✅ Function to Convert Data Types from CSV
def convert_value(value):
    """Convert CSV values to int, float, or keep as string."""
    try:
        if "." in value:  # If it has a decimal, convert to float
            return float(value)
        return int(value)  # Otherwise, convert to int
    except ValueError:
        return value  # If conversion fails, return as string

#✅ Open and Read the CSV File
with open(file_path, mode='r') as csv_file:
    reader = csv.DictReader(csv_file)

    for row in reader:
        # Convert each value dynamically
        converted_row = {key: convert_value(value) for key, value in row.items()}

        # Serialize the message correctly
        message = json.dumps(converted_row).encode('utf-8')

        #send the value
        print("Publishing record:", message)
        # Publish the message
        future = publisher.publish(topic_path, message)

        # Ensure publishing is successful
        future.result()

print("All records have been published.")