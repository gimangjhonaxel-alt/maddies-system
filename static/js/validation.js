(function () {
    "use strict";

    // Same rules as the server (forms.py), so both sides agree.
    // Email: no spaces, no "@@", no leading/trailing/double dots, needs a domain
    // with a dot and a letters-only ending (so "name@gmail" is rejected).
    var EMAIL_PATTERN = /^[^\s@.]+(\.[^\s@.]+)*@[^\s@.]+(\.[^\s@.]+)*\.[A-Za-z]{2,}$/;
    var PHONE_PATTERN = /^(09\d{9}|\+639\d{9})$/;
    var PASSWORD_PAIRS = {
        confirm_password: "password",
        confirm_new_password: "new_password"
    };

    function isVisible(input) {
        return !input.closest(".d-none");
    }

    function isCheckable(input) {
        var skipped = ["hidden", "submit", "button", "file", "checkbox", "radio"];
        return !input.disabled && skipped.indexOf(input.type) === -1 && isVisible(input);
    }

    function cleanValue(input) {
        // Never change passwords; trim everything else.
        return input.type === "password" ? input.value : input.value.trim();
    }

    function validateInput(input, form) {
        if (!isCheckable(input)) {
            return "";
        }
        var value = cleanValue(input);
        var name = input.name;

        // These two boxes are only visible when they apply, so empty means missing.
        if ((name === "gcash_reference" || name === "delivery_address") && value === "") {
            return name === "gcash_reference"
                ? "Please enter your GCash reference number."
                : "Please enter your delivery address.";
        }
        if (input.required && value === "") {
            return "This field is required.";
        }
        if (value === "") {
            return "";
        }

        if (input.type === "email" && !EMAIL_PATTERN.test(value)) {
            return "Enter a valid email address, like name@example.com.";
        }
        if (name === "customer_phone" && !PHONE_PATTERN.test(value)) {
            return "Enter a valid mobile number, like 09171234567.";
        }

        var minLength = parseInt(input.getAttribute("minlength"), 10);
        if (!isNaN(minLength) && value.length < minLength) {
            return "Please use at least " + minLength + " characters.";
        }
        if (name === "gcash_reference" && value.length < 6) {
            return "Please enter your GCash reference number (at least 6 characters).";
        }

        if (input.type === "number") {
            var number = Number(value);
            if (isNaN(number)) {
                return "Enter a valid number.";
            }
            if (input.min !== "" && number < Number(input.min)) {
                return "The smallest allowed value is " + input.min + ".";
            }
            if (input.max !== "" && number > Number(input.max)) {
                return "The largest allowed value is " + input.max + ".";
            }
        }

        if (PASSWORD_PAIRS[name]) {
            var other = form.querySelector('[name="' + PASSWORD_PAIRS[name] + '"]');
            if (other && other.value !== input.value) {
                return "Passwords must match.";
            }
        }
        return "";
    }

    function clearError(input) {
        input.classList.remove("is-invalid");
        var next = input.nextElementSibling;
        if (next && next.classList.contains("js-error")) {
            next.remove();
        }
    }

    function showError(input, message) {
        clearError(input);
        if (!message) {
            return;
        }
        input.classList.add("is-invalid");
        var box = document.createElement("div");
        box.className = "invalid-feedback js-error";
        box.textContent = message;
        input.insertAdjacentElement("afterend", box);
    }

    function isTextLike(input) {
        return input.tagName === "TEXTAREA" ||
            ["text", "email", "tel"].indexOf(input.type) !== -1;
    }

    // Use our own messages instead of the browser's pop-up bubbles.
    document.querySelectorAll("form").forEach(function (form) {
        form.setAttribute("novalidate", "");
    });

    // Check the whole form when it is submitted.
    document.addEventListener("submit", function (event) {
        var form = event.target;
        var firstInvalid = null;

        // form.elements also includes boxes that sit outside the <form> tag
        // but belong to it (like the stock page's quantity boxes).
        Array.from(form.elements).filter(function (el) {
            return el.tagName === "INPUT" || el.tagName === "TEXTAREA";
        }).forEach(function (input) {
            if (isTextLike(input) && isCheckable(input)) {
                input.value = input.value.trim();
            }
            var message = validateInput(input, form);
            showError(input, message);
            if (message && !firstInvalid) {
                firstInvalid = input;
            }
        });

        if (firstInvalid) {
            event.preventDefault();
            firstInvalid.focus();
        }
    }, true);

    // Check a field as soon as the person leaves it (only if they typed something).
    document.addEventListener("focusout", function (event) {
        var input = event.target;
        if (!input.matches || !input.matches("input, textarea") || !input.form) {
            return;
        }
        if (input.value !== "") {
            showError(input, validateInput(input, input.form));
        }
    });

    // Clear the message as soon as they start fixing it.
    document.addEventListener("input", function (event) {
        var input = event.target;
        if (input.classList && input.classList.contains("is-invalid")) {
            clearError(input);
        }
    });
})();