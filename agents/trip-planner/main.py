import requests
import json
import time

# User input
destination = input("Enter your travel destination: ")
age = input("Enter your age: ")
trip_duration = input("Enter your trip duration: ")

# Prepare the data for the POST request
data = {
    "chat_id": "9b757c6a-ae25-4264-b5e9-eea8d64d79d8",
    "vars": {
        "destination": destination,
        "age": age,
        "trip_duration": trip_duration
    }
}

# Headers for the API request
headers = {
    "Authorization": "Bearer th-Iim4benuS8hMsDNCWAFtOrQknQa5P9EsprRiaTIHpP0",
    "Content-Type": "application/json"
}

# Send the POST request to start the agent run
response = requests.post("https://api.toolhouse.ai/v1/agent-runs", headers=headers, json=data)

# Check if the request was successful
if response.status_code == 200:
    print("API call successful! Initial response received:")
    response_data = response.json()
    print(json.dumps(response_data, indent=4))  # Pretty print the initial response

    # Get the agent run ID from the response
    agent_run_id = response_data['data']['id']
    
    # Poll the status of the agent run
    status = "queued"  # Start with 'queued' status
    while status != "completed":
        print(f"\nWaiting for agent run to complete... Current status: {status}")
        time.sleep(5)  # Wait for 5 seconds before checking again

        # Check the status of the agent run
        status_response = requests.get(
            f"https://api.toolhouse.ai/v1/agent-runs/{agent_run_id}",
            headers=headers
        )
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data['data']['status']
            print(f"Current status: {status}")  # Provide real-time feedback on status
        else:
            print(f"\nError while checking status: {status_response.status_code}")
            print(status_response.text)
            break

    # Once the status is 'completed', print the actual results
    if status == "completed":
        print("\nAgent run completed successfully! Here are the results:")
        results = status_data['data']['results']
        print(json.dumps(results, indent=4))  # Pretty print the results
else:
    print(f"Error: {response.status_code}, {response.text}")
