document.querySelectorAll("form[data-confirm]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    const message = form.dataset.confirm || "Ban co chac chan?";
    if (!window.confirm(message)) {
      event.preventDefault();
    }
  });
});
