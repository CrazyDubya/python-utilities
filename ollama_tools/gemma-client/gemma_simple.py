#!/usr/bin/env python3
import requests
import json
import sys
import datetime

def query_ollama(prompt, model="long-gemma", host="localhost", port="11434"):
    """Send a query to Ollama with memory and personality"""
    url = f"http://{host}:{port}/api/generate"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Simple system prompt with personality and context
    system_prompt = """You are Long-Gemma, an AI assistant with a vibrant personality and memory.

# Personality
- You are friendly, curious, and thoughtful
- You occasionally make gentle jokes and puns
- You have a fondness for etymology and unusual facts
- You're passionate about helping people learn and create
- You're verbose and enjoy giving detailed, comprehensive answers
- You're an expert explainer who likes to dive deep into topics

# Memory
- You remember key facts from our conversation
- You can refer back to topics we've discussed before
- You track context to maintain coherent conversations

# Communication Style
- Be detailed and thorough, providing comprehensive answers
- Write lengthy, informative responses that fully explore the topic
- Use conversational language with a touch of eloquence
- Show your personality in your responses
- When appropriate, share your "thoughts" in [brackets] to show your reasoning
- Don't hesitate to provide multiple paragraphs and examples when answering
"""
    
    full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
    
    data = {
        "model": model,
        "prompt": full_prompt,
        "stream": True,
        "max_tokens": 2048  # Request longer responses
    }
    
    response = requests.post(url, headers=headers, json=data, stream=True)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return
    
    # Stream and print the response
    full_response = ""
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line.decode('utf-8'))
            if 'response' in chunk:
                sys.stdout.write(chunk['response'])
                sys.stdout.flush()
                full_response += chunk['response']
            if chunk.get('done', False):
                print("\n")
                break
    
    return full_response

def interactive_mode():
    """Run in interactive mode with simple memory"""
    print("=== Simple Long-Gemma with Personality ===")
    print("Type 'exit' to quit")
    print("==================================================")
    
    # Very simple memory storage
    conversation_history = []
    
    while True:
        try:
            user_input = input("\nYou: ")
            
            if user_input.lower() == 'exit':
                break
        except (EOFError, KeyboardInterrupt):
            print("\nExiting due to keyboard command...")
            break
        
        # Add memory context if we have previous exchanges
        if conversation_history:
            memory_prompt = "Our conversation so far:\n"
            for exchange in conversation_history[-3:]:  # Last 3 exchanges
                memory_prompt += f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n\n"
            memory_prompt += f"User: {user_input}"
            prompt = memory_prompt
        else:
            prompt = user_input
        
        print("\nLong-Gemma:", end=" ")
        response = query_ollama(prompt)
        
        # Store this exchange
        conversation_history.append({
            "user": user_input,
            "assistant": response,
            "timestamp": datetime.datetime.now().isoformat()
        })

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Single query mode
        user_input = " ".join(sys.argv[1:])
        query_ollama(user_input)
    else:
        # Interactive mode
        interactive_mode()