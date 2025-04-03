# Create a file called deepseek_chat.py in your Django app directory
import os
import requests
from django.conf import settings

def deepseek_chat():
    """
    Interactive chat with DeepSeek API
    Type 'exit' to quit the chat
    """
    # API configuration
    api_url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    # System message to set assistant behavior
    messages = [{
        "role": "system",
        "content": "You are a helpful assistant. Respond concisely and accurately."
    }]

    print("DeepSeek Chat Interface (type 'exit' to quit)\n")

    while True:
        try:
            # Get user input
            user_input = input("You: ")
            
            if user_input.lower() == 'exit':
                print("Exiting chat...")
                break

            # Add user message to conversation history
            messages.append({"role": "user", "content": user_input})

            # API request payload
            payload = {
                "model": "deepseek-chat",  # or "deepseek-reasoner"
                "messages": messages,
                "temperature": 0.7,
                "stream": False
            }

            # Make API call
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()

            # Process response
            data = response.json()
            assistant_response = data['choices'][0]['message']['content']
            
            # Add assistant response to conversation history
            messages.append({"role": "assistant", "content": assistant_response})
            
            # Print formatted response
            print("\nDeepSeek:")
            print(assistant_response)
            print("\n" + "-"*50 + "\n")

        except requests.exceptions.RequestException as e:
            print(f"\nError connecting to API: {str(e)}")
            break
        except KeyError:
            print("\nUnexpected API response format")
            break
        except KeyboardInterrupt:
            print("\nExiting chat...")
            break

# To use in Django shell:
# python manage.py shell
# >>> from your_app.deepseek_chat import deepseek_chat
# >>> deepseek_chat()