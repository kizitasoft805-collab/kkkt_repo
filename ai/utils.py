import requests
from django.conf import settings

def ask_qwen_interactive():
    """
    An interactive function to send prompts to the Qwen 2.5 Max API.
    Runs in a loop, allowing you to enter multiple prompts until you type 'exit' or 'quit'.
    """
    # Define the API endpoint
    url = "https://dashscope.aliyuncs.com/api/v1/services/qwen/invoke"

    print("Welcome to the Qwen Interactive Shell!")
    print("Type your questions below. Type 'exit' or 'quit' to stop.")

    while True:
        # Prompt the user for input
        prompt = input("\nEnter your question: ")

        # Check if the user wants to exit
        if prompt.lower() in ["exit", "quit"]:
            print("Exiting the Qwen Interactive Shell. Goodbye!")
            break

        # Prepare the data payload
        data = {
            "input": {
                "prompt": prompt  # The user's question or input
            },
            "parameters": {
                "model": "qwen-2.5-max"  # Use the Qwen 2.5 Max model
            }
        }

        # Set headers for authentication
        headers = {
            "Authorization": f"Bearer {settings.QWEN_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            # Make the POST request to the API
            response = requests.post(url, json=data, headers=headers)

            # Check if the request was successful
            if response.status_code == 200:
                api_response = response.json()
                answer = api_response.get("output", {}).get("text", "No answer found.")
                print(f"\nQwen's Answer: {answer}")
            else:
                # Handle errors
                print(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            # Handle exceptions (e.g., network issues)
            print(f"An exception occurred: {e}")