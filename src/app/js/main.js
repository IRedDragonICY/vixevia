document.addEventListener("DOMContentLoaded", () => {
    const floatingButton = document.querySelector(".floating-button");
    const modal = new bootstrap.Modal(document.getElementById("settingsModal"));
    const ngrokForm = document.getElementById("ngrok-form");
    const apiKeyInput = document.getElementById("api-key");
    const ngrokStatus = document.getElementById("ngrok-status");
    const startNgrokButton = document.getElementById("start-ngrok");
    const stopNgrokButton = document.getElementById("stop-ngrok");

    floatingButton.addEventListener("click", () => {
        modal.show();
    });

    startNgrokButton.addEventListener("click", async () => {
        const apiKey = apiKeyInput.value;

        try {
            const response = await fetch("/api/start_ngrok", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: new URLSearchParams({ api_key: apiKey }),
            });

            const data = await response.json();
            if (response.ok) {
                ngrokStatus.innerHTML = `<div class="alert alert-success mt-3" role="alert">Ngrok is running. Public URL: <a href="${data.public_url}" target="_blank">${data.public_url}</a></div>`;
                startNgrokButton.style.display = "none";
                stopNgrokButton.style.display = "block";
            } else {
                ngrokStatus.innerHTML = `<div class="alert alert-danger mt-3" role="alert">${data.message}</div>`;
            }
        } catch (error) {
            console.error("Error starting ngrok:", error);
            ngrokStatus.innerHTML = `<div class="alert alert-danger mt-3" role="alert">Error starting ngrok.</div>`;
        }
    });

    stopNgrokButton.addEventListener("click", async () => {
        try {
            const response = await fetch("/api/stop_ngrok", { method: "POST" });
            const data = await response.json();
            ngrokStatus.innerHTML = `<div class="alert alert-${response.ok ? "success" : "danger"} mt-3" role="alert">${data.message}</div>`;
            if (response.ok) {
                stopNgrokButton.style.display = "none";
                startNgrokButton.style.display = "block";
            }
        } catch (error) {
            console.error("Error stopping ngrok:", error);
            ngrokStatus.innerHTML = `<div class="alert alert-danger mt-3" role="alert">Error stopping ngrok.</div>`;
        }
    });
});
