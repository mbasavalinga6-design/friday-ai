const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.lang = "en-US";
recognition.continuous = false;
recognition.interimResults = false;

function speak(text) {
    window.speechSynthesis.cancel();
    let utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 1;
    utterance.pitch = 1.8;
    utterance.volume = 1;

    let voices = window.speechSynthesis.getVoices();
    let femaleVoice = voices.find(v =>
        v.name.includes("Female") ||
        v.name.includes("Zira") ||
        v.name.includes("Samantha") ||
        v.name.includes("Google UK English Female") ||
        v.name.includes("Microsoft Zira")
    );
    if (femaleVoice) utterance.voice = femaleVoice;
    window.speechSynthesis.speak(utterance);
}

function startVoice() {
    recognition.start();
    document.getElementById("micBtn").innerText = "🔴";
}

recognition.onresult = function(event) {
    let spokenText = event.results[0][0].transcript;
    document.getElementById("input").value = spokenText;
    document.getElementById("micBtn").innerText = "🎤";
    send();
}

recognition.onerror = function(event) {
    document.getElementById("micBtn").innerText = "🎤";
    alert("Mic error: " + event.error);
}

recognition.onend = function() {
    document.getElementById("micBtn").innerText = "🎤";
}

function greetBasava() {
    let greeting = "Hi Basava! I am Friday, your personal AI assistant. What can I do for you?";
    let chat = document.getElementById("chat");
    chat.innerHTML += `<p class="friday-msg"><b>🦾 Friday:</b> ${greeting}</p>`;
    sessionStorage.setItem("chatHistory", chat.innerHTML);
    speak(greeting);
}

window.onload = function() {
    window.speechSynthesis.getVoices();

    if (sessionStorage.getItem("loggedIn") === "true") {
        document.getElementById("loginBox").remove();
        document.getElementById("main").style.display = "block";

        let savedChat = sessionStorage.getItem("chatHistory");
        if (savedChat) {
            document.getElementById("chat").innerHTML = savedChat;
        }

        document.getElementById("input").addEventListener("keydown", function(e) {
            if (e.key === "Enter") {
                e.preventDefault();
                send();
            }
        });
    }
}

async function login() {
    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;

    try {
        let res = await fetch("https://friday-backend-wbmu.onrender.com", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ username, password })
        });

        let data = await res.json();

        if (data.status === "success") {
            sessionStorage.setItem("loggedIn", "true");
            sessionStorage.setItem("chatHistory", "");

            document.getElementById("loginBox").remove();
            document.getElementById("main").style.display = "block";

            document.getElementById("input").addEventListener("keydown", function(e) {
                if (e.key === "Enter") {
                    e.preventDefault();
                    send();
                }
            });

            setTimeout(() => {
                greetBasava();
            }, 500);

        } else {
            alert("Invalid login");
        }

    } catch (error) {
        alert("Could not connect to server. Make sure Flask is running.");
    }
}

async function send() {
    let input = document.getElementById("input");
    let chat = document.getElementById("chat");
    let command = input.value;

    if (!command.trim()) return;

    chat.innerHTML += `<p class="user-msg"><b>You:</b> ${command}</p>`;
    input.value = "";

    try {
        let res = await fetch("https://friday-backend-wbmu.onrender.com", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ command })
        });

        let data = await res.json();

        if (data.response === "GREET") {
            greetBasava();

        } else if (data.response.startsWith("PLAY:")) {
            let parts = data.response.replace("PLAY:", "").split("|");
            let song = parts[0].trim();
            let videoId = parts[1].trim();

            // FIXED: Open exact YouTube video in new tab
            if (videoId && videoId !== "none") {
                window.open(`https://www.youtube.com/watch?v=${videoId}`, "_blank");
            } else {
                window.open(`https://www.youtube.com/results?search_query=${encodeURIComponent(song)}`, "_blank");
            }

            chat.innerHTML += `<p class="friday-msg"><b>🦾 Friday:</b> 🎵 Playing ${song} for you Basava!</p>`;
            speak(`Playing ${song}`);

        } else {
            chat.innerHTML += `<p class="friday-msg"><b>🦾 Friday:</b> ${data.response}</p>`;
            speak(data.response);
        }

        sessionStorage.setItem("chatHistory", chat.innerHTML);
        chat.scrollTop = chat.scrollHeight;

    } catch (error) {
        chat.innerHTML += `<p class="friday-msg"><b>🦾 Friday:</b> ❌ Error connecting to server.</p>`;
        sessionStorage.setItem("chatHistory", chat.innerHTML);
    }
}

function viewHistory() {
    window.open("history.html", "_blank");
}

// Check reminders every 5 seconds
setInterval(async function() {
    try {
        let res = await fetch("https://friday-backend-wbmu.onrender.com");
        let data = await res.json();

        if (data.reminder) {
            let message = `Basava! Reminder! Reminder! You asked me to remind you to ${data.reminder}. Please do it now Basava!`;
            let chat = document.getElementById("chat");

            chat.innerHTML += `<p class="friday-msg" style="border-color: #ff4444; color: #ff4444; font-size: 16px;"><b>🔔 Friday:</b> ${message}</p>`;
            sessionStorage.setItem("chatHistory", chat.innerHTML);
            chat.scrollTop = chat.scrollHeight;

            window.speechSynthesis.cancel();
            let utterance = new SpeechSynthesisUtterance(message);
            utterance.lang = "en-US";
            utterance.rate = 1;
            utterance.pitch = 1.8;
            utterance.volume = 1;

            let voices = window.speechSynthesis.getVoices();
            let femaleVoice = voices.find(v =>
                v.name.includes("Female") ||
                v.name.includes("Zira") ||
                v.name.includes("Samantha") ||
                v.name.includes("Google UK English Female") ||
                v.name.includes("Microsoft Zira")
            );
            if (femaleVoice) utterance.voice = femaleVoice;

            window.speechSynthesis.speak(utterance);
            utterance.onend = function() {
                window.speechSynthesis.speak(new SpeechSynthesisUtterance(message));
            }
        }
    } catch (error) {
        console.log("Reminder check error:", error);
    }
}, 5000);