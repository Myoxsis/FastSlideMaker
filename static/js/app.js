async function generateDeck(event) {
  event.preventDefault();

  const payload = {
    topic: document.getElementById("topic").value,
    audience: document.getElementById("audience").value,
    tone: document.getElementById("tone").value,
    slide_count: Number(document.getElementById("slide_count").value),
  };

  const output = document.getElementById("output");
  output.textContent = "Generating...";

  const response = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  output.textContent = JSON.stringify(data, null, 2);
}

document.getElementById("deck-form").addEventListener("submit", generateDeck);
