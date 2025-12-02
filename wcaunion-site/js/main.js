// js/main.js

// 1) Set current year in any footer span#year (optional but nice)
(function () {
  const yearEl = document.getElementById("year");
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }
})();

// 2) Run after DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  // ========= MOBILE NAV TOGGLE (if present) =========
  const navToggle = document.querySelector(".nav-toggle");
  const nav = document.getElementById("site-nav");

  if (navToggle && nav) {
    navToggle.addEventListener("click", () => {
      const isExpanded = navToggle.getAttribute("aria-expanded") === "true";
      const nextState = !isExpanded;

      navToggle.setAttribute("aria-expanded", String(nextState));
      nav.classList.toggle("nav-open", nextState);
    });
  }

  // ========= CONTACT FORM → BACKEND =========
  const contactForm = document.getElementById("contact-form");
  const statusEl = document.getElementById("contact-status");

  if (contactForm) {
    const nameInput = document.getElementById("name");
    const emailInput = document.getElementById("email");
    const roleInput = document.getElementById("role");
    const programInput = document.getElementById("program");
    const messageInput = document.getElementById("message");

    contactForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      if (!statusEl) return;

      statusEl.textContent = "Sending...";
      statusEl.style.color = "";

      const name = nameInput?.value.trim() || "";
      const email = emailInput?.value.trim() || "";
      const role = roleInput?.value.trim() || "";
      const program = programInput?.value.trim() || "";
      const message = messageInput?.value.trim() || "";

      // Basic client-side validation
      if (!name || !email || !message) {
        statusEl.textContent =
          "Please fill out your name, email, and message.";
        statusEl.style.color = "red";
        return;
      }

      try {
        // For local dev: FastAPI running on 127.0.0.1:8000
        const response = await fetch("http://127.0.0.1:8000/api/contact", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name,
            email,
            role: role || null,
            program: program || null,
            message,
          }),
        });

        if (!response.ok) {
          let errorMsg = "Something went wrong. Please try again.";
          try {
            const data = await response.json();
            if (data && data.detail) {
              errorMsg = data.detail;
            }
          } catch (_) {
            // ignore JSON parse error, keep generic message
          }
          throw new Error(errorMsg);
        }

        const data = await response.json();
        statusEl.textContent =
          data.message || "Thanks, we received your message.";
        statusEl.style.color = "green";
        contactForm.reset();
      } catch (err) {
        console.error(err);
        statusEl.textContent =
          err instanceof Error && err.message
            ? err.message
            : "There was an error sending your message. Please try again.";
        statusEl.style.color = "red";
      }
    });
  }
});
