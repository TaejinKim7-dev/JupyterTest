from openai import OpenAI
import os

# Load config
env_file = os.path.join(os.path.dirname(__file__), 'configs', 'jupyter_ai_openrouter.env')

# Read and set env vars
with open(env_file) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value.strip('"')

client = OpenAI(
  base_url=os.environ.get('OPENAI_API_BASE', 'https://openrouter.ai/api/v1'),
  api_key=os.environ.get('OPENAI_API_KEY', ''),
)

# Test with reasoning
response = client.chat.completions.create(
  model="poolside/laguna-m.1:free",
  messages=[
          {
            "role": "user",
            "content": "How many r's are in the word 'strawberry'?"
          }
        ],
  extra_body={"reasoning": {"enabled": True}}
)

# Extract the assistant message with reasoning_details
response = response.choices[0].message

print("=== First Response ===")
print(f"Content: {response.content}")
print(f"Reasoning: {response.reasoning_details}")

# Preserve the assistant message with reasoning_details
messages = [
  {"role": "user", "content": "How many r's are in the word 'strawberry'?"},
  {
    "role": "assistant",
    "content": response.content,
    "reasoning_details": response.reasoning_details  # Pass back unmodified
  },
  {"role": "user", "content": "Are you sure? Think carefully."}
]

# Second API call - model continues reasoning from where it left off
response2 = client.chat.completions.create(
  model="poolside/laguna-m.1:free",
  messages=messages,
  extra_body={"reasoning": {"enabled": True}}
)

print("\n=== Second Response ===")
print(f"Content: {response2.choices[0].message.content}")
print(f"Reasoning: {response2.choices[0].message.reasoning_details}")