const chatArea = document.getElementById("chat-area");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const modelDropdown = document.getElementById("model-dropdown");

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});

function appendMessage(text, sender) {
  const msg = document.createElement("div");
  msg.classList.add("message", sender);
  msg.textContent = text;
  chatArea.appendChild(msg);
  chatArea.scrollTop = chatArea.scrollHeight;
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  const selectedModel = modelDropdown.value;
  appendMessage(text, "user");
  userInput.value = "";

  // Show thinking message
  appendMessage("Thinking...", "bot");

  try {
    const res = await fetch("http://127.0.0.1:5000/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ 
        prompt: text, 
        service: selectedModel  // Changed from 'model' to 'service'
      })
    });

    const data = await res.json();
    
    // Remove thinking message
    document.querySelector(".bot:last-child").remove();
    
    // Handle both success and error responses
    if (data.response) {
      appendMessage(data.response, "bot");
    } else if (data.error) {
      appendMessage(`❌ Error: ${data.error}`, "bot");
    } else {
      appendMessage("❌ No response received", "bot");
    }

  } catch (error) {
    // Remove thinking message
    document.querySelector(".bot:last-child").remove();
    appendMessage(`⚠️ Network error: ${error.message}`, "bot");
    console.error("Fetch error:", error);
  }
}