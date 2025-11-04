document.addEventListener('DOMContentLoaded', () => {
  console.log('Contest Modal – Enhanced with Status Check');

  // === ELEMENTS ===
  const contestModal = document.getElementById('contest-modal');
  const contestNowBtn = document.getElementById('contest-now-btn');
  const closeContestModal = document.getElementById('close-contest-modal');
  const exitBtn = document.getElementById('exit-btn');
  const submitContest = document.getElementById('submit-contest');
  const manifestoInput = document.getElementById('manifesto-input');
  const positionsContainer = document.getElementById('positions-container');
  const step1 = document.getElementById('step-1');
  const step2 = document.getElementById('step-2');
  const resultPdf = document.getElementById('result-pdf');
  const accountPdf = document.getElementById('account-pdf');
  const resultFilename = document.getElementById('result-filename');
  const accountFilename = document.getElementById('account-filename');
  const pdfFrame = document.getElementById('pdf-frame');
  const pdfViewer = document.getElementById('pdf-viewer');
  const charCount = document.getElementById('char-count');
  const progressCircle = document.getElementById('progress-circle');

  const alreadySubmitted = document.getElementById('already-submitted');
  const closeAlreadySubmitted = document.getElementById('close-already-submitted');

  // === STATE ===
  let selectedPosition = null;
  let hasUploaded = false;
  let hasApplied = false;

  // === CSRF TOKEN ===
  const getCsrfToken = () => {
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input) return input.value;
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : null;
  };

  // === CHECK IF ALREADY APPLIED ===
 async function checkApplicationStatus() {
  try {
    const res = await fetch(window.APP_URLS.check_contest_status);
    const data = await res.json();

    hasApplied = data.applied || false;
    console.log('data',data)

    if (!hasApplied) {
      // Not applied → show normal modal
      return;
    }

    if (data.approved) {
      // APPROVED → Show FINAL MESSAGE
      document.getElementById('already-submitted').innerHTML = `
        <div class="text-center py-8">
          <div class="w-20 h-20 mx-auto mb-4 bg-emerald-100 rounded-full flex items-center justify-center">
            <svg class="w-12 h-12 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <h3 class="text-2xl font-bold text-emerald-700 mb-2">Finally, You Have Been Approved!</h3>
          <p class="text-gray-600">Your application has been reviewed and approved by the election officer.</p>
        </div>
      `;
      showAlreadySubmitted();
    } else if (data.rejected) {
      // REJECTED → Show rejection
      document.getElementById('already-submitted').innerHTML = `
        <div class="text-center py-8">
          <div class="w-20 h-20 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
            <svg class="w-12 h-12 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </div>
          <h3 class="text-2xl font-bold text-red-700 mb-2">Application Rejected</h3>
          <p class="text-gray-600">Unfortunately, your application did not meet the requirements.</p>
        </div>
      `;
      showAlreadySubmitted();
    } else {
      // PENDING → Show awaiting
      document.getElementById('already-submitted').innerHTML = `
        <div class="text-center py-8">
          <div class="w-20 h-20 mx-auto mb-4 bg-yellow-100 rounded-full flex items-center justify-center animate-pulse">
            <svg class="w-12 h-12 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <h3 class="text-2xl font-bold text-yellow-700 mb-2">Congratulations! Awaiting Approval</h3>
          <p class="text-gray-600">Your application has been submitted. Please wait for officer review.</p>
        </div>
      `;
      showAlreadySubmitted();
    }
  } catch (err) {
    console.error('Failed to check status:', err);
  }
}
  // === SHOW ALREADY SUBMITTED ===
  function showAlreadySubmitted() {
    step1.classList.add('hidden');
    step2.classList.add('hidden');
    alreadySubmitted.classList.remove('hidden');
  }

  // === LOAD POSITIONS ===
  function loadPositions() {
    positionsContainer.innerHTML = '<p class="col-span-2 text-sm text-gray-500">Loading positions...</p>';
    fetch(window.APP_URLS.get_positions_api)
      .then(r => { if (!r.ok) throw new Error('Network error'); return r.json(); })
      .then(data => {
        const positions = data.positions || [];
        if (positions.length === 0) {
          positionsContainer.innerHTML = '<p class="col-span-2 text-sm text-red-500">No positions available.</p>';
          return;
        }
        positionsContainer.innerHTML = positions.map(pos => `
          <div class="position-option p-4 bg-gray-50 dark:bg-gray-800 rounded-xl border-2 border-transparent cursor-pointer transition-all hover:border-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/30"
               data-id="${pos.id}" data-name="${pos.name}">
            <div class="font-semibold text-emerald-700 dark:text-emerald-400">${pos.name}</div>
            ${pos.description ? `<div class="text-xs text-gray-600 dark:text-gray-400 mt-1">${pos.description}</div>` : ''}
          </div>
        `).join('');

        document.querySelectorAll('.position-option').forEach(option => {
          option.addEventListener('click', () => {
            if (selectedPosition === option) {
              option.classList.remove('selected', 'border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-900/30');
              selectedPosition = null;
            } else {
              document.querySelectorAll('.position-option').forEach(opt => opt.classList.remove('selected', 'border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-900/30'));
              option.classList.add('selected', 'border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-900/30');
              selectedPosition = option;
            }
            toggleNextButton();
          });
        });
      })
      .catch(err => {
        console.error('Failed to load positions:', err);
        positionsContainer.innerHTML = '<p class="col-span-2 text-sm text-red-500">Error loading positions.</p>';
      });
  }

  // === MODAL OPEN ===
  contestNowBtn?.addEventListener('click', async () => {
    contestModal.classList.remove('hidden');
    contestModal.style.display = 'flex';
    alreadySubmitted.classList.add('hidden');
    step1.classList.remove('hidden');
    step2.classList.add('hidden');
    resetForm();
    adjustModalHeight();
    await checkApplicationStatus();
    if (!hasApplied) loadPositions();
  });

  // === CLOSE MODAL ===
  [closeContestModal, exitBtn, closeAlreadySubmitted].forEach(btn => {
    btn?.addEventListener('click', () => {
      contestModal.classList.add('hidden');
      contestModal.style.display = 'none';
      resetForm();
    });
  });

  // === NEXT / BACK ===
  const nextBtn = document.getElementById('next-btn');
  const backBtn = document.getElementById('back-btn');
  nextBtn?.addEventListener('click', () => {
    if (nextBtn.dataset.disabled !== 'true' && selectedPosition && manifestoInput.value.trim()) {
      step1.classList.add('hidden');
      step2.classList.remove('hidden');
      progressCircle.style.strokeDashoffset = '0';
      toggleSubmitButton();
    }
  });
  backBtn?.addEventListener('click', () => {
    step1.classList.remove('hidden');
    step2.classList.add('hidden');
    progressCircle.style.strokeDashoffset = '31.4';
    toggleNextButton();
  });

  // === FILE UPLOADS ===
  document.getElementById('upload-result-btn')?.addEventListener('click', () => resultPdf.click());
  document.getElementById('upload-account-btn')?.addEventListener('click', () => accountPdf.click());
  resultPdf?.addEventListener('change', handleFileChange);
  accountPdf?.addEventListener('change', handleFileChange);

  function handleFileChange(e) {
    const file = e.target.files[0];
    const isResult = e.target === resultPdf;
    const filenameEl = isResult ? resultFilename : accountFilename;
    if (file && file.type === 'application/pdf') {
      filenameEl.textContent = file.name;
      displayPdf(file);
      hasUploaded = resultPdf.files.length > 0 && accountPdf.files.length > 0;
    } else {
      filenameEl.textContent = 'No file selected';
      hasUploaded = resultPdf.files.length > 0 && accountPdf.files.length > 0;
    }
    toggleSubmitButton();
  }
  function displayPdf(file) {
    const url = URL.createObjectURL(file);
    pdfViewer.classList.remove('hidden');
    pdfFrame.src = url;
  }

  // === SUBMIT ===
  submitContest?.addEventListener('click', () => {
    if (submitContest.dataset.disabled !== 'true' && hasUploaded && selectedPosition) {
      const csrftoken = getCsrfToken();
      if (!csrftoken) return;

      const formData = new FormData();
      formData.append('position', selectedPosition.dataset.name);
      formData.append('manifesto', manifestoInput.value);
      formData.append('statement_of_result', resultPdf.files[0]);
      formData.append('account_statement', accountPdf.files[0]);

      fetch(window.APP_URLS.submit_contest_application, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken },
        body: formData
      })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(d => {
        if (d.success) {
          hasApplied = true;
          showAlreadySubmitted();
          // No alert()
        } else {
          alert('Error: ' + (d.message || 'Unknown error'));
        }
      })
      .catch(err => {
        console.error('Submit error:', err);
        alert('Network error. Please try again.');
      });
    }
  });

  // === CHARACTER COUNT ===
  manifestoInput?.addEventListener('input', () => {
    const count = manifestoInput.value.length;
    charCount.textContent = `${count}/200`;
    toggleNextButton();
  });

  // === TOGGLE BUTTONS ===
  function toggleNextButton() {
    const valid = selectedPosition && manifestoInput.value.trim().length > 0 && manifestoInput.value.length <= 200;
    nextBtn.dataset.disabled = valid ? 'false' : 'true';
  }
  function toggleSubmitButton() {
    const valid = resultPdf.files[0] && accountPdf.files[0];
    submitContest.dataset.disabled = valid ? 'false' : 'true';
  }

  // === RESET FORM ===
  function resetForm() {
    manifestoInput.value = '';
    charCount.textContent = '0/200';
    selectedPosition = null;
    hasUploaded = false;
    resultFilename.textContent = 'No file selected';
    accountFilename.textContent = 'No file selected';
    pdfFrame.src = '';
    pdfViewer.classList.add('hidden');
    resultPdf.value = '';
    accountPdf.value = '';
    step1.classList.remove('hidden');
    step2.classList.add('hidden');
    progressCircle.style.strokeDashoffset = '31.4';
    toggleNextButton();
    toggleSubmitButton();
  }

  // === KEYBOARD ADJUST ===
  function adjustModalHeight() {
    const viewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
    const keyboardHeight = window.innerHeight - viewportHeight;
    const contentArea = contestModal.querySelector('.max-h-\\[calc\\(80vh-140px\\)\\]');
    if (contentArea) {
      contentArea.style.maxHeight = keyboardHeight > 100
        ? `calc(80vh - ${keyboardHeight + 60}px - 6rem)`
        : 'calc(80vh - 140px)';
    }
  }
  window.addEventListener('resize', () => contestModal.style.display === 'flex' ? adjustModalHeight() : null);
  manifestoInput?.addEventListener('focus', adjustModalHeight);
  manifestoInput?.addEventListener('blur', adjustModalHeight);

  // Init
  toggleNextButton();
  toggleSubmitButton();
});