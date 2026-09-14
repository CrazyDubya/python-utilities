#!/usr/bin/env python3
import requests
import json
import sys

def query_ollama(prompt, model="long-gemma", host="localhost", port="11434"):
    """Send a query to Ollama and stream the response"""
    url = f"http://{host}:{port}/api/generate"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "prompt": prompt,
        "stream": True
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

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("Enter your prompt: ")
    
    query_ollama(prompt, model="long-gemma")