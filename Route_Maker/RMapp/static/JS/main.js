const autocompleteUrl = window.routeMakerConfig?.autocompleteUrl;
const autocompleteState = new WeakMap();
const autocompleteCache = new Map();
let activeInput = null;

function debounce(fn, wait) {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), wait);
    };
}

function getAutocompleteState(input) {
    if (autocompleteState.has(input)) {
        return autocompleteState.get(input);
    }

    const wrapper = input.closest(".autocomplete-field");
    const menu = document.createElement("div");
    menu.className = "autocomplete-menu";
    menu.hidden = true;
    wrapper.appendChild(menu);

    const state = { wrapper, menu, controller: null, activeQuery: "" };
    autocompleteState.set(input, state);
    return state;
}

function closeMenu(input) {
    const state = getAutocompleteState(input);
    state.menu.hidden = true;
    state.menu.innerHTML = "";
}

function selectSuggestion(input, value) {
    input.value = value;
    activeInput = input;
    closeMenu(input);
}

function renderSuggestions(input, results) {
    const state = getAutocompleteState(input);
    state.menu.innerHTML = "";

    if (!results.length) {
        state.menu.hidden = true;
        return;
    }

    results.forEach((result) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "autocomplete-option";
        button.innerHTML = `
        <span class="autocomplete-option-title">${result.address_line1 || result.formatted_address}</span>
        <span class="autocomplete-option-subtitle">${result.address_line2 || result.formatted_address}</span>
        `;
        button.addEventListener("mousedown", (event) => {
            event.preventDefault();
            selectSuggestion(input, result.formatted_address);
        });
        state.menu.appendChild(button);
    });

    state.menu.hidden = false;
}

async function fetchSuggestions(input) {
    const query = input.value.trim();
    const state = getAutocompleteState(input);

    if (query.length < 3 || !autocompleteUrl) {
        closeMenu(input);
        return;
    }

    if (autocompleteCache.has(query)) {
        renderSuggestions(input, autocompleteCache.get(query));
        return;
    }

    if (state.controller) {
        state.controller.abort();
    }

    state.controller = new AbortController();
    state.activeQuery = query;

    try {
        const response = await fetch(`${autocompleteUrl}?q=${encodeURIComponent(query)}`, {
            headers: { "X-Requested-With": "XMLHttpRequest" },
            signal: state.controller.signal,
        });

        if (!response.ok) {
            closeMenu(input);
            return;
        }

        const payload = await response.json();
        if (state.activeQuery !== query) {
            return;
        }

        const results = payload.results || [];
        autocompleteCache.set(query, results);
        renderSuggestions(input, results);
    } catch (error) {
        if (error.name === "AbortError") {
            return;
        }
        closeMenu(input);
    }
}

function bindAutocomplete(input) {
    getAutocompleteState(input);
    const debouncedFetch = debounce(() => fetchSuggestions(input), 120);
    input.addEventListener("input", debouncedFetch);
    input.addEventListener("focus", () => {
        activeInput = input;
        debouncedFetch();
    });
    input.addEventListener("blur", () => {
        setTimeout(() => closeMenu(input), 120);
    });
}

document.querySelectorAll(".route-autocomplete").forEach((input) => {
    bindAutocomplete(input);
});

document.addEventListener("click", (event) => {
    document.querySelectorAll(".route-autocomplete").forEach((input) => {
        const state = getAutocompleteState(input);
        if (!state.wrapper.contains(event.target)) {
            closeMenu(input);
        }
    });
});

document.querySelectorAll(".quick-place-btn").forEach((button) => {
    button.addEventListener("click", () => {
        const targetInput = activeInput || document.getElementById("Origin_form");
        targetInput.value = button.dataset.address || "";
        targetInput.focus();
    });
});

const addDestinoBtn = document.getElementById("Add-Detino-btn");
addDestinoBtn.addEventListener("click", () => {
    const containerDestinos = document.getElementById("destinos");
    const newDestino = document.createElement("div");
    newDestino.className = "mb-3 autocomplete-field";
    newDestino.innerHTML = `
      <input type="text" class="form-control route-input route-autocomplete Destino_input" name="Destino_form" placeholder="Dirección de destino" autocomplete="off">
    `;
    containerDestinos.appendChild(newDestino);
    bindAutocomplete(newDestino.querySelector(".Destino_input"));
});

const routeMaker = document.getElementById("RM");
const form = document.getElementById("FA");
routeMaker.addEventListener("click", () => {
    form.submit();
});
