from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import time

app = Flask(__name__)
CORS(app)

# Load API keys from config.json once at startup
try:
    with open("config.json") as f:
        keys = json.load(f)
except FileNotFoundError:
    raise FileNotFoundError("❌ 'config.json' not found. Please provide the file with API keys.")

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.json
        prompt = data.get("prompt")
        service = data.get("service")

        if service == "groq":
            return ask_groq(prompt, keys.get("groq", ""))
        elif service == "huggingface":
            return ask_huggingface(prompt, keys.get("huggingface", ""))
        elif service == "together":
            return ask_together(prompt, keys.get("together", ""))
        elif service == "replicate":
            return ask_replicate(prompt, keys.get("replicate", ""))
        elif service == "gemini":
            return ask_gemini(prompt, keys["gemini"])
        elif service == "openrouter":
            return ask_openrouter(prompt, keys.get("openrouter", ""))
        # Keep original paid services as backup
        elif service == "openai":
            return ask_openai(prompt, keys["openai"])
        elif service == "deepinfra":
            return ask_deepinfra(prompt, keys["deepinfra"])
        else:
            return jsonify({"response": "Invalid service selected."})
    except Exception as e:
        print("Error in /ask route:", str(e))
        return jsonify({"response": f"Internal server error: {str(e)}"}), 500


def ask_groq(prompt, key):
    """Groq API - FREE and very fast (6000 tokens/min)"""
    if not key:
        return jsonify({"error": "❌ Get your FREE Groq API key from: https://console.groq.com"}), 400
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant",  # Fast and free model
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return jsonify({"response": result['choices'][0]['message']['content']})
        else:
            return jsonify({"error": "No response from Groq API"}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Groq API request failed: {str(e)}"}), 500


def ask_huggingface(prompt, key):
    """Hugging Face Inference API - FREE with generous limits"""
    if not key:
        return jsonify({"error": "❌ Get your FREE Hugging Face API key from: https://huggingface.co/settings/tokens"}), 400
    
    # Using a free, reliable model
    url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    data = {"inputs": prompt, "parameters": {"max_length": 1000}}

    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and len(result) > 0:
            if "generated_text" in result[0]:
                return jsonify({"response": result[0]["generated_text"]})
            elif "error" in result[0]:
                # Model might be loading, try alternative
                return ask_huggingface_alt(prompt, key)
        
        return jsonify({"error": f"Unexpected Hugging Face response: {result}"}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Hugging Face API request failed: {str(e)}"}), 500


def ask_huggingface_alt(prompt, key):
    """Alternative Hugging Face model - Google FLAN-T5"""
    url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    data = {"inputs": prompt}

    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and len(result) > 0 and "generated_text" in result[0]:
            return jsonify({"response": result[0]["generated_text"]})
        else:
            return jsonify({"error": "Hugging Face model is loading, try again in a few seconds"}), 503
            
    except Exception as e:
        return jsonify({"error": f"Hugging Face alternative failed: {str(e)}"}), 500


def ask_together(prompt, key):
    """Together AI - FREE tier available"""
    if not key:
        return jsonify({"error": "❌ Get your FREE Together AI key from: https://api.together.xyz"}), 400
    
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Llama-2-7b-chat-hf",  # Free model
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return jsonify({"response": result['choices'][0]['message']['content']})
        else:
            return jsonify({"error": "No response from Together AI"}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Together AI request failed: {str(e)}"}), 500


def ask_replicate(prompt, key):
    """Replicate API - Has free tier"""
    if not key:
        return jsonify({"error": "❌ Get your FREE Replicate key from: https://replicate.com"}), 400
    
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {key}",
        "Content-Type": "application/json"
    }
    data = {
        "version": "meta/llama-2-7b-chat:8e6975e5ed6174911a6ff3d60540dfd4844201974602551e10e9e87ab143d81e7",
        "input": {"prompt": prompt, "max_length": 1000}
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if 'urls' in result and 'get' in result['urls']:
            # Poll for result
            get_url = result['urls']['get']
            for _ in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                get_response = requests.get(get_url, headers=headers)
                get_result = get_response.json()
                
                if get_result['status'] == 'succeeded':
                    output = get_result.get('output', [])
                    if output:
                        return jsonify({"response": ''.join(output)})
                elif get_result['status'] == 'failed':
                    return jsonify({"error": "Replicate model failed"}), 500
            
            return jsonify({"error": "Replicate request timed out"}), 500
        else:
            return jsonify({"error": f"Unexpected Replicate response: {result}"}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Replicate API request failed: {str(e)}"}), 500


def ask_openrouter(prompt, key):
    """OpenRouter - Access to many free models"""
    if not key:
        return jsonify({"error": "❌ Get your FREE OpenRouter key from: https://openrouter.ai"}), 400
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "microsoft/wizardlm-2-8x22b",  # Free model on OpenRouter
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return jsonify({"response": result['choices'][0]['message']['content']})
        else:
            return jsonify({"error": "No response from OpenRouter"}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"OpenRouter request failed: {str(e)}"}), 500


def ask_gemini(prompt, key):
    """Google Gemini - Your working service"""
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1000
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        result = response.json()

        if ("candidates" in result and len(result["candidates"]) > 0 and 
            "content" in result["candidates"][0] and 
            "parts" in result["candidates"][0]["content"] and 
            len(result["candidates"][0]["content"]["parts"]) > 0):
            return jsonify({"response": result["candidates"][0]["content"]["parts"][0]["text"]})
        else:
            return jsonify({"error": f"Unexpected Gemini response: {result}"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Gemini API request failed: {str(e)}"}), 500


# Keep original functions for backward compatibility
def ask_openai(prompt, key):
    """OpenAI - Requires billing"""
    return jsonify({"error": "OpenAI requires billing setup. Use free alternatives above!"}), 402


def ask_deepinfra(prompt, key):
    """DeepInfra - Requires payment"""
    return jsonify({"error": "DeepInfra requires payment. Use free alternatives above!"}), 402


if __name__ == "__main__":
    app.run(debug=True)