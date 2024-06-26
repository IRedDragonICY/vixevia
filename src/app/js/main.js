class NgrokController {
    constructor() {
        this.floatingButton = document.querySelector(".floating-button");
        this.modal = new bootstrap.Modal(document.getElementById("settingsModal"));
        this.ngrokForm = document.getElementById("ngrok-form");
        this.apiKeyInput = document.getElementById("api-key");
        this.ngrokStatus = document.getElementById("ngrok-status");
        this.startNgrokButton = document.getElementById("start-ngrok");
        this.stopNgrokButton = document.getElementById("stop-ngrok");

        this.initializeEvents();
    }

    initializeEvents() {
        this.floatingButton.addEventListener("click", () => this.modal.show());
        this.startNgrokButton.addEventListener("click", () => this.startNgrok());
        this.stopNgrokButton.addEventListener("click", () => this.stopNgrok());
    }

    async startNgrok() {
        const apiKey = this.apiKeyInput.value;
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
                this.updateNgrokStatus('success', `Ngrok is running. Public URL: <a href="${data.public_url}" target="_blank">${data.public_url}</a>`);
                this.toggleNgrokButtons();
            } else {
                this.updateNgrokStatus('danger', data.message);
            }
        } catch (error) {
            console.error("Error starting ngrok:", error);
            this.updateNgrokStatus('danger', "Error starting ngrok.");
        }
    }

    async stopNgrok() {
        try {
            const response = await fetch("/api/stop_ngrok", { method: "POST" });
            const data = await response.json();
            this.updateNgrokStatus(response.ok ? 'success' : 'danger', data.message);
            if (response.ok) this.toggleNgrokButtons();
        } catch (error) {
            console.error("Error stopping ngrok:", error);
            this.updateNgrokStatus('danger', "Error stopping ngrok.");
        }
    }

    updateNgrokStatus(status, message) {
        this.ngrokStatus.innerHTML = `<div class="alert alert-${status} mt-3" role="alert">${message}</div>`;
    }

    toggleNgrokButtons() {
        this.startNgrokButton.style.display = this.startNgrokButton.style.display === "none" ? "block" : "none";
        this.stopNgrokButton.style.display = this.stopNgrokButton.style.display === "none" ? "block" : "none";
    }
}

document.addEventListener("DOMContentLoaded", () => new NgrokController());
