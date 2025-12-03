const form = document.getElementById("login-form");
const email = document.getElementById("email");
const pass = document.getElementById("password");
const emailErr = document.getElementById("email-error");
const passErr = document.getElementById("password-error");

form.addEventListener("submit", (e) => {
  let valid = true;

  emailErr.classList.add("hidden");
  passErr.classList.add("hidden");

  if (!email.value.trim()) {
    emailErr.textContent = "Email requerido";
    emailErr.classList.remove("hidden");
    valid = false;
  }

  if (!pass.value.trim()) {
    passErr.textContent = "Contraseña requerida";
    passErr.classList.remove("hidden");
    valid = false;
  }

  if (!valid) e.preventDefault();
});
