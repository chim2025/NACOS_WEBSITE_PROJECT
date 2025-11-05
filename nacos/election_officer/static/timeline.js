
console.log("=== SETTINGS JS LOADED ===");

// === TOAST SYSTEM ===
function showToast(message, sub = '', type = 'success') {
  const toast = document.getElementById('toast');
  const icon = document.getElementById('toast-icon');
  const msg = document.getElementById('toast-message');
  const submsg = document.getElementById('toast-sub');

  if (!toast || !icon || !msg) return;

  msg.textContent = message;
  submsg.textContent = sub;

  if (type === 'success') {
    icon.innerHTML = '<span class="material-symbols-outlined text-emerald-600 text-xl">check_circle</span>';
    toast.querySelector('div').className = 'bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-5 flex items-center gap-3 border border-emerald-200';
  } else {
    icon.innerHTML = '<span class="material-symbols-outlined text-red-600 text-xl">error</span>';
    toast.querySelector('div').className = 'bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-5 flex items-center gap-3 border border-red-200';
  }

  toast.classList.remove('opacity-0', 'pointer-events-none');
  toast.classList.add('opacity-100');

  setTimeout(hideToast, 4000);
}

function hideToast() {
  const toast = document.getElementById('toast');
  if (toast) {
    toast.classList.add('opacity-0', 'pointer-events-none');
  }
}

// === DOM READY ===
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM ready");

    // === TAB SWITCHING ===
    document.querySelectorAll('[data-page]').forEach(btn => {
        btn.addEventListener('click', () => {
            console.log("Tab clicked:", btn.dataset.page);

            document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
            document.querySelectorAll('[data-page]').forEach(b => b.classList.remove('active'));

            let targetPage;
            if (btn.dataset.page === 'settings') {
                targetPage = document.getElementById('page-settings');
            } else {
                targetPage = document.getElementById(`page-${btn.dataset.page}`);
            }

            if (targetPage) {
                targetPage.classList.remove('hidden');
                console.log("Page shown:", targetPage.id);

                if (btn.dataset.page === 'settings' && !targetPage.dataset.loaded) {
                    targetPage.dataset.loaded = 'true';
                    console.log("First load → fetching data");
                    loadSettingsPage();
                }
            }

            btn.classList.add('active');
        });
    });
});

// === LOAD SETTINGS PAGE ===
async function loadSettingsPage() {
    const form = document.getElementById('election-settings-form');
    const loading = document.getElementById('settings-loading');
    const page = document.getElementById('page-settings');

    if (!form || !loading) {
        console.error("Form or loading spinner not found");
        return;
    }

    loading.classList.remove('hidden');
    form.classList.add('hidden');

    try {
        await Promise.all([loadElectionOptions(), loadSettings()]);
        form.classList.remove('hidden');
        loading.classList.add('hidden');
        console.log("Settings page fully loaded");
    } catch (err) {
        console.error("Load failed:", err);
        loading.innerHTML = `<p class="text-red-600 text-center">Failed: ${err.message}</p>`;
    }
}

// === LOAD OPTIONS ===
async function loadElectionOptions() {
    const form = document.getElementById('election-settings-form');
    if (!form) return;

    const url = form.dataset.optionsUrl;
    console.log("Fetching options from:", url);

    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        console.log("Options loaded:", data);

        populateSelect('voter-levels', data.levels);
        populateSelect('candidate-levels', data.levels);
        populateSelect('voter-depts', data.departments);
        populateSelect('candidate-depts', data.departments);
    } catch (err) {
        console.error("Options failed:", err);
        showToast('Failed to load options', err.message, 'error');
    }
}

function populateSelect(selectId, items) {
    const select = document.getElementById(selectId);
    if (!select) return console.warn(`Select #${selectId} not found`);
    select.innerHTML = '';
    if (!items || items.length === 0) {
        select.innerHTML = '<option disabled>No options</option>';
        return;
    }
    items.forEach(item => {
        const opt = new Option(item.name, item.id);
        select.add(opt);
    });
}

// === LOAD SETTINGS ===
async function loadSettings() {
    const form = document.getElementById('election-settings-form');
    if (!form) return;

    const url = form.dataset.settingsUrl;
    console.log("Fetching settings from:", url);

    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        console.log("Settings loaded:", data);

        const startInput = document.getElementById('start_date_input');
        const endInput = document.getElementById('end_date_input');

        if (startInput) startInput.value = data.start_date?.slice(0, 16) || '';
        if (endInput) endInput.value = data.end_date?.slice(0, 16) || '';

        document.getElementById('allow-all-voters').checked = !!data.allow_all_voters;
        document.getElementById('allow-all-candidates').checked = !!data.allow_all_candidates;
        form.show_live_results.checked = data.show_live_results !== false;

        setMultiSelect('voter-levels', data.voter_levels || []);
        setMultiSelect('voter-depts', data.voter_departments || []);
        setMultiSelect('candidate-levels', data.candidate_levels || []);
        setMultiSelect('candidate-depts', data.candidate_departments || []);

        // Auto-toggle eligibility
        if (data.allow_all_voters) {
            selectAllOptions('voter-levels');
            selectAllOptions('voter-depts');
            toggleEligibility('voter', 'allow-all-voters', 'voter-levels', 'voter-depts');
        }
        if (data.allow_all_candidates) {
            selectAllOptions('candidate-levels');
            selectAllOptions('candidate-depts');
            toggleEligibility('candidate', 'allow-all-candidates', 'candidate-levels', 'candidate-depts');
        }

        updateDateDisplays();
    } catch (err) {
        console.error("Settings load failed:", err);
        showToast('Failed to load settings', err.message, 'error');
    }
}

function setMultiSelect(selectId, values) {
    const select = document.getElementById(selectId);
    if (!select) return;
    Array.from(select.options).forEach(opt => {
        opt.selected = values.includes(opt.value);
    });
}

function selectAllOptions(selectId) {
    const select = document.getElementById(selectId);
    if (select) {
        Array.from(select.options).forEach(opt => opt.selected = true);
    }
}

function toggleEligibility(section, checkboxId, levelId, deptId) {
    const checkbox = document.getElementById(checkboxId);
    const container = document.getElementById(levelId).closest('.grid');
    if (checkbox.checked) {
        container.classList.add('opacity-50', 'pointer-events-none');
    } else {
        container.classList.remove('opacity-50', 'pointer-events-none');
    }
}

// Attach toggle listeners
document.getElementById('allow-all-voters').addEventListener('change', () => {
    toggleEligibility('voter', 'allow-all-voters', 'voter-levels', 'voter-depts');
});
document.getElementById('allow-all-candidates').addEventListener('change', () => {
    toggleEligibility('candidate', 'allow-all-candidates', 'candidate-levels', 'candidate-depts');
});

// === SAVE ===
document.getElementById('election-settings-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const form = e.target;
    const url = form.dataset.saveUrl;
    console.log("Saving to:", url);

    const formData = new FormData(form);
    const data = {};
    for (let [k, v] of formData) {
        if (v === 'on') v = true;
        if (data[k]) {
            if (!Array.isArray(data[k])) data[k] = [data[k]];
            data[k].push(v);
        } else data[k] = v;
    }
    console.log("Data to send:", data);

    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify(data)
        });

        const text = await res.text();
        console.log("Raw response:", text);

        let result;
        try {
            result = JSON.parse(text);
        } catch (e) {
            throw new Error(`Invalid JSON: ${text.substring(0, 200)}`);
        }

        if (res.ok && result.success) {
            showToast('Settings saved successfully!', 'All changes applied.', 'success');
        } else {
            const error = result.error || result.detail || 'Unknown error';
            showToast('Save failed', error, 'error');
        }
    } catch (err) {
        console.error("Save failed:", err);
        showToast('Network error', err.message, 'error');
    }
});

// === DATE DISPLAY ===
function formatDateTimeLocal(iso) {
    if (!iso) return '';
    return new Date(iso).toLocaleString('en-US', {
        weekday: 'long', month: 'long', day: 'numeric',
        year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true
    });
}

function updateDateDisplays() {
    ['start_date_input', 'end_date_input'].forEach(id => {
        const input = document.getElementById(id);
        const display = document.getElementById(id.replace('_input', '_display'));
        if (input && display) {
            display.textContent = formatDateTimeLocal(input.value);
        }
    });
}

['start_date_input', 'end_date_input'].forEach(id => {
    const input = document.getElementById(id);
    if (input) {
        input.addEventListener('input', updateDateDisplays);
        input.addEventListener('change', updateDateDisplays);
    }
});

// === RELOAD ===
window.reloadSettings = () => {
    console.log("Manual reload");
    const content = document.getElementById('page-settings');
    if (content) content.removeAttribute('data-loaded');
    loadSettingsPage();
};
