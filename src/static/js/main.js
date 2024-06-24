document.addEventListener("DOMContentLoaded", () => {
    const floatingButton = document.querySelector(".floating-button");
    const modal = new bootstrap.Modal(document.getElementById("settingsModal"));

    floatingButton.addEventListener("click", () => {
        modal.show();
    });
});