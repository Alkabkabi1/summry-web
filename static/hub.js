(function () {

  const form = document.querySelector(".upload-form");

  const overlay = document.getElementById("processing-overlay");

  const subjectSelect = document.getElementById("subject_slug");

  const newSubjectInput = document.getElementById("new_subject_name");



  if (form && overlay && form.querySelector('input[type="file"]')) {

    form.addEventListener("submit", () => {

      overlay.classList.remove("hidden");

      overlay.setAttribute("aria-hidden", "false");

    });

  }



  if (subjectSelect && newSubjectInput) {

    subjectSelect.addEventListener("change", () => {

      if (subjectSelect.value) {

        newSubjectInput.value = "";

      }

    });

    newSubjectInput.addEventListener("input", () => {

      if (newSubjectInput.value.trim()) {

        subjectSelect.value = "";

      }

    });

  }



  if (window.location.hash === "#packs") {

    const packs = document.getElementById("packs");

    if (packs) {

      packs.scrollIntoView({ behavior: "smooth", block: "start" });

    }

  }

})();


