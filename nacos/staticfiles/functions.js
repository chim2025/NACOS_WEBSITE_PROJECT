
  document.addEventListener("DOMContentLoaded", function () {
    console.log("Main dashboard script loaded");

    // === CSRF & ELEMENTS ===
    const CSRF = document.getElementById('csrf_token')?.value || 
                 document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    const pages = document.querySelectorAll('.page');
    const navBtns = document.querySelectorAll('.nav-btn');
    const notifBadge = document.getElementById('notif-badge');

    // === GLOBAL FUNCTIONS (must be available to onclick) ===
    window.openModal = function(id) {
      const modal = document.getElementById(id);
      if (modal) modal.classList.add('active');
      if (id === 'position-modal') loadPositions();
    };

    window.closeModal = function(id) {
      const modal = document.getElementById(id);
      if (modal) modal.classList.remove('active');
    };

window.refreshLiveView = function() {
    const container = document.getElementById('live-view');
    if (!container) return;

    container.innerHTML = `
        <div class="text-center py-8">
            <div class="inline-flex items-center gap-2 text-gray-500 dark:text-gray-400">
                <span class="material-symbols-outlined animate-spin text-xl">sync</span>
                <span class="text-sm">Loading results...</span>
            </div>
        </div>
    `;

    fetch(window.APP_URLS.live_results)
        .then(r => r.json())
        .then(data => {
            if (!data.live || data.live.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-xl">
                        <span class="material-symbols-outlined text-5xl text-gray-400 mb-3 block">bar_chart</span>
                        <p class="text-gray-600 dark:text-gray-300">No election data available</p>
                    </div>
                `;
                return;
            }

            const isEnded = data.election_status === 'ended';

            container.innerHTML = `
                <!-- Status Header -->
                <div class="text-center mb-6">
                    <h3 class="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mb-2">
                        ${isEnded ? 'Final Results' : 'Live Election Results'}
                    </h3>
                    <span class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold
                        ${isEnded 
                            ? 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' 
                            : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300 animate-pulse'}">
                        <span class="w-2 h-2 rounded-full ${isEnded ? 'bg-gray-500' : 'bg-emerald-500'}"></span>
                        ${isEnded ? 'Election Ended' : 'Live Now'}
                    </span>
                </div>

                <!-- Results Grid -->
                <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    ${data.live.map(pos => {
                        const totalVotes = pos.candidates.reduce((s, c) => s + c.votes, 0);
                        const maxVotes = Math.max(...pos.candidates.map(c => c.votes), 1);
                        return `
                            <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-5 border border-gray-200 dark:border-gray-700 
                                        transition-all hover:shadow-xl hover:-translate-y-1">
                                <div class="flex justify-between items-start mb-4">
                                    <h4 class="font-bold text-lg text-gray-800 dark:text-white truncate pr-2">
                                        ${pos.position}
                                    </h4>
                                    <div class="text-right">
                                        <p class="text-xs text-gray-500">Total Votes</p>
                                        <p class="font-bold text-emerald-600 dark:text-emerald-400">${totalVotes}</p>
                                    </div>
                                </div>

                                <div class="space-y-4">
                                    ${pos.candidates.length === 0 ? `
                                        <p class="text-center text-gray-500 text-sm italic py-4">No candidates</p>
                                    ` : ''}
                                    ${pos.candidates.map(c => {
                                        const pct = (c.votes / maxVotes) * 100;
                                        const isWinner = c.votes === maxVotes && maxVotes > 0;
                                        return `
                                            <div class="flex items-center gap-3 group">
                                                <!-- Profile -->
                                                <div class="relative flex-shrink-0">
                                                    <img src="${c.photo || '/static/default-avatar.png'}"
                                                         class="w-12 h-12 rounded-full object-cover ring-2 ring-white shadow-md
                                                                group-hover:ring-emerald-500 transition-all duration-300">
                                                    ${isWinner ? `
                                                        <div class="absolute -top-1 -right-1 w-6 h-6 bg-gradient-to-br from-yellow-400 to-amber-500 
                                                                    rounded-full flex items-center justify-center shadow-lg animate-pulse">
                                                            <span class="material-symbols-outlined text-white text-sm">star</span>
                                                        </div>
                                                    ` : ''}
                                                </div>

                                                <!-- Details -->
                                                <div class="flex-1 min-w-0">
                                                    <p class="font-semibold text-gray-800 dark:text-white truncate text-sm">
                                                        ${c.name}
                                                    </p>
                                                    <p class="text-xs text-gray-500 truncate">
                                                        ${c.matric || c.batch || '—'}
                                                    </p>
                                                    <div class="flex justify-between items-center mt-1 text-xs">
                                                        <span class="font-bold text-emerald-600 dark:text-emerald-400">${c.votes} votes</span>
                                                        <span class="text-gray-500">${pct.toFixed(1)}%</span>
                                                    </div>
                                                    <div class="mt-1.5 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                                                        <div class="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full 
                                                                     transition-all duration-1000 ease-out"
                                                             style="width: ${pct}%"></div>
                                                    </div>
                                                </div>
                                            </div>
                                        `;
                                    }).join('')}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>

                <!-- Footer -->
                <div class="mt-6 text-center text-xs text-gray-500 dark:text-gray-400">
                    Last updated: <span id="result-timestamp">just now</span>
                </div>
            `;

            // Update timestamp
            const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const ts = container.querySelector('#result-timestamp');
            if (ts) ts.textContent = now;

            // Auto-refresh only if live
            if (!isEnded && !window.liveInterval) {
                window.liveInterval = setInterval(refreshLiveView, 5000);
            } else if (isEnded && window.liveInterval) {
                clearInterval(window.liveInterval);
                window.liveInterval = null;
            }
        })
        .catch(err => {
            console.error(err);
            container.innerHTML = `
                <div class="text-center py-12 bg-red-50 dark:bg-red-900/20 rounded-xl">
                    <span class="material-symbols-outlined text-5xl text-red-500 mb-3 block">error</span>
                    <p class="text-red-600 dark:text-red-400">Failed to load results</p>
                </div>
            `;
        });
};



    // === NAVIGATION ===
    function showPage(id) {
      pages.forEach(p => p.classList.remove('active'));
      const pageEl = document.getElementById(`page-${id}`);
      if (pageEl) pageEl.classList.add('active');
      navBtns.forEach(b => b.classList.remove('active'));
      const btn = document.querySelector(`[data-page="${id}"]`);
      if (btn) btn.classList.add('active');
      if (id === 'notifications') loadNotifications();
      history.pushState({page: id}, '', `#${id}`);
    }

    navBtns.forEach(btn => btn.addEventListener('click', () => showPage(btn.dataset.page)));
    window.addEventListener('popstate', e => showPage((e.state?.page) || 'home'));
    showPage(location.hash.slice(1) || 'home');

    // === DARK MODE ===
    const darkToggle = document.getElementById('dark-mode-toggle');
    if (darkToggle) {
      darkToggle.addEventListener('click', () => {
        document.documentElement.classList.toggle('dark');
        const isDark = document.documentElement.classList.contains('dark');
        localStorage.setItem('darkMode', isDark);
      });
    }

    const savedDark = localStorage.getItem('darkMode');
    if (savedDark === 'true' || (!savedDark && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
    }

    // === MODAL CLOSE ON BACKDROP ===
    window.addEventListener('click', e => {
      if (e.target.classList.contains('modal')) {
        closeModal(e.target.id);
      }
    });

    // === SHOW MODAL MESSAGE ===
    window.showModalMessage = function(modalId, type, text) {
      const msgEl = document.getElementById(modalId + '-msg');
      if (!msgEl) return;
      msgEl.textContent = text;
      msgEl.className = 'form-message ' + type;
      msgEl.style.display = 'block';
      setTimeout(() => { msgEl.style.display = 'none'; }, 4000);
    };

    // === CREATE POSITION ===
document.getElementById('position-form').onsubmit = function(e) {
  e.preventDefault();

  const msgEl = document.getElementById('position-msg');
  if (msgEl) msgEl.style.display = 'none';

  const fd = new FormData(this);
  fetch(window.APP_URLS.create_position, {
    method: 'POST',
    headers: { 'X-CSRFToken': CSRF },
    body: fd
  })
  .then(r => r.json())
  .then(d => {
    if (d.success) {
      this.reset();
      loadPositions();
      showTopMessage('Position created successfully!', 'success');
    } else {
      showTopMessage(d.message || 'Failed to create', 'error');
    }
  })
  .catch(() => {
    showTopMessage('Network error', 'error');
  });
};

    // === TIMELINE FORM ===
    const timelineForm = document.getElementById('timeline-form-modal');
    if (timelineForm) {
      timelineForm.onsubmit = function(e) {
        e.preventDefault();
        const startInput = this.querySelector('[name="start_date"]');
        const endInput = this.querySelector('[name="end_date"]');
        const now = new Date();
        const start = new Date(startInput.value);
        const end = new Date(endInput.value);

        const msgEl = document.getElementById('timeline-msg');
        if (msgEl) msgEl.style.display = 'none';

        if (isNaN(start) || isNaN(end)) {
          showModalMessage('timeline', 'error', 'Please select valid dates.');
          return;
        }
        if (start <= now) {
          showModalMessage('timeline', 'error', 'Start time must be in the future.');
          return;
        }
        if (end <= start) {
          showModalMessage('timeline', 'error', 'End time must be after start time.');
          return;
        }

        const fd = new FormData(this);
        fetch(window.APP_URLS.update_timeline, {
          method: 'POST',
          headers: { 'X-CSRFToken': CSRF },
          body: fd
        })
        .then(r => r.json())
        .then(d => {
          if (d.success) {
            showModalMessage('timeline', 'success', 'Timeline saved successfully!');
            setTimeout(() => {
              closeModal('time-modal');
              location.reload();
            }, 1200);
          } else {
            showModalMessage('timeline', 'error', d.message || 'Failed to save timeline.');
          }
        })
        .catch(() => {
          showModalMessage('timeline', 'error', 'Network error. Please try again.');
        });
      };
    }


    const form = document.getElementById('position-form');
    const toggleBtn = document.getElementById('toggle-position-form');
    const addIcon = document.getElementById('add-icon');
    const minusIcon = document.getElementById('minus-icon');
    const list = document.getElementById('position-list');
   
    const topMessage = document.getElementById('position-top-message');

function showTopMessage(text, type = 'success') {
    if (!topMessage) return;

    topMessage.textContent = text;
    topMessage.className = `
        fixed top-4 left-1/2 -translate-x-1/2 z-50
        px-6 py-3 rounded-xl text-center font-medium
        shadow-lg transition-all duration-300
        ${type === 'success' 
            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' 
            : 'bg-red-100 text-red-800 border border-red-300'
        }
    `;

    topMessage.classList.remove('hidden');

    // Smooth fade out
    setTimeout(() => {
        topMessage.classList.add('opacity-0');
        setTimeout(() => {
            topMessage.classList.add('hidden');
            topMessage.classList.remove('opacity-0');
        }, 300);
    }, 3000);
}

    

    // Toggle form visibility
    function toggleForm(show) {
      if (show) {
        form.style.display = 'block';
        addIcon.classList.add('hidden');
        minusIcon.classList.remove('hidden');
      } else {
        form.style.display = 'none';
        addIcon.classList.remove('hidden');
        minusIcon.classList.add('hidden');
      }
    }

    toggleBtn?.addEventListener('click', () => {
      const shouldShow = form.style.display === 'none';
      toggleForm(shouldShow);
    });

    // === LOAD POSITIONS WITH DELETE BUTTON ===
    window.loadPositions = function() {
      if (!list) return;
      list.innerHTML = '<p class="position-empty">Loading...</p>';

      fetch(window.APP_URLS.get_positions)
        .then(r => r.json())
        .then(d => {
          if (!d.positions || d.positions.length === 0) {
            list.innerHTML = '<p class="position-empty">No positions created yet.</p>';
            toggleForm(true); // Show form if empty
            return;
          }

          list.innerHTML = d.positions.map(p => `
            <div class="position-item" style="position:relative; padding:12px; border:1px solid #e5e7eb; border-radius:8px; margin-bottom:8px; background:#fafafa;">
              <!-- DELETE BUTTON -->
              <button
                onclick="deletePosition(${p.id}, this)"
                style="position:absolute; top:8px; right:8px; background:#ef4444; color:white; border:none; width:24px; height:24px; border-radius:6px; cursor:pointer;"
                title="Delete">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m-8 0h10m-9 4v10m6-10v10"/>
                </svg>
              </button>
              <div class="position-name font-medium">${p.name}</div>
              <div class="position-desc text-sm text-gray-600">${p.description || 'No description'}</div>
            </div>
          `).join('');

          // === AUTO TOGGLE FORM BASED ON COUNT ===
          const count = d.positions.length;
          if (count <= 3) {
            toggleForm(true);  // Show form
          } else {
            toggleForm(false); // Hide form, show +
          }
        })
        .catch(() => {
          list.innerHTML = '<p class="position-empty text-red-500">Failed to load.</p>';
        });
    };

  window.deletePosition = function(id, button) {
  if (!confirm('Delete this position?')) return;

  const item = button.closest('.position-item');
  item.style.opacity = '0.5';

  // CORRECT: Append id + trailing slash
  const url = (window.APP_URLS.delete_position || '') + id + '/';

  console.log('DELETE URL:', url);  // Should show: /officer/position/delete/5/

  fetch(url, {
    method: 'POST',
    headers: {
      'X-CSRFToken': CSRF,
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
  })
  .then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  })
  .then(data => {
    if (data.success) {
      item.remove();
      loadPositions(); 
      showTopMessage('Position deleted successfully!', 'success'); 
    } else {
      showTopMessage(data.message || 'Delete failed', 'error');
      item.style.opacity = '1';
    }
  })
  .catch(err => {
    console.error('Delete error:', err);
    showTopMessage('Network error', 'error');
    item.style.opacity = '1';
  });
};

    // === APPROVE / REJECT ===
    document.querySelectorAll('.approve-btn').forEach(b =>
      b.onclick = () => handleApp(b.dataset.id, 'approve')
    );
    document.querySelectorAll('.reject-btn').forEach(b =>
      b.onclick = () => {
        const reason = prompt('Rejection reason:');
        if (reason) handleApp(b.dataset.id, 'reject', reason);
      }
    );

    function handleApp(id, action, reason = '') {
      const body = `application_id=${id}&action=${action}${reason ? '&rejection_reason=' + encodeURIComponent(reason) : ''}`;
      fetch(window.APP_URLS.manage_application, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': CSRF
        },
        body
      })
      .then(r => r.json())
      .then(d => {
        alert(d.success ? 'Updated!' : d.message || 'Error');
        if (d.success) location.reload();
      });
    }

    // === NOTIFICATIONS ===
    window.loadNotifications = function() {
      fetch(window.APP_URLS.notifications)
        .then(r => r.json())
        .then(d => {
          const list = document.getElementById('notif-list');
          if (!d.notifications?.length) {
            list.innerHTML = '<p class="text-center text-gray-500">No notifications.</p>';
            notifBadge?.classList.add('hidden');
            return;
          }
          notifBadge.textContent = d.notifications.length;
          notifBadge.classList.remove('hidden');
          list.innerHTML = d.notifications.map(n => `
            <div class="info-card p-4 flex justify-between items-start">
              <div>
                <p class="font-medium">${n.text}</p>
                <p class="text-xs text-gray-500 mt-1">${n.time}</p>
              </div>
              <button class="text-xs text-emerald-600 hover:underline" onclick="this.parentElement.parentElement.remove(); updateBadge()">
                Mark as Read
              </button>
            </div>
          `).join('');
        });
    };

    function updateBadge() {
      const count = document.querySelectorAll('#notif-list > div').length;
      if (count === 0) {
        notifBadge.classList.add('hidden');
      } else {
        notifBadge.textContent = count;
      }
    }

    setInterval(() => {
      if (document.getElementById('page-notifications')?.classList.contains('active')) {
        loadNotifications();
      }
    }, 30000);

    // === COUNTDOWN ===
    window.updateGreetingAndCountdown = function() {
      const now = new Date();
      const hours = now.getHours();
      let greeting = 'Good morning';
      if (hours >= 12 && hours < 17) greeting = 'Good afternoon';
      else if (hours >= 17) greeting = 'Good evening';
      const greetingEl = document.getElementById('greeting-message');
      if (greetingEl) greetingEl.textContent = greeting + ',';

      const timerEl = document.getElementById('countdown-timer');
      if (!timerEl) return;

      const url = window.APP_URLS?.get_latest_timeline;
      if (!url) {
        timerEl.innerHTML = '<span class="countdown-empty">URL missing</span>';
        return;
      }
      timerEl.innerHTML = '<span class="countdown-empty">Loading...</span>';

      fetch(url)
        .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
        .then(data => {
          if (data.success && data.latest && data.latest.start_date && data.latest.end_date) {
            const startDate = new Date(data.latest.start_date);
            const endDate = new Date(data.latest.end_date);
            if (isNaN(startDate) || isNaN(endDate)) {
              timerEl.innerHTML = '<span class="countdown-empty">Invalid date</span>';
              return;
            }
            startCountdown(startDate, endDate, timerEl);
          } else {
            timerEl.innerHTML = '<span class="countdown-empty">No election scheduled</span>';
          }
        })
        .catch(err => {
          console.error('Countdown error:', err);
          timerEl.innerHTML = '<span class="countdown-empty">Error loading</span>';
        });
    };

    function startCountdown(startDate, endDate, el) {
      let interval = null;
      function formatCountdown(ms) {
        const days  = Math.floor(ms / (1000 * 60 * 60 * 24));
        const hours = Math.floor((ms % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const mins  = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));
        const secs  = Math.floor((ms % (1000 * 60)) / 1000);
        const parts = [];
        if (days) parts.push(`${days}d`);
        parts.push(`${hours.toString().padStart(2,'0')}:${mins.toString().padStart(2,'0')}:${secs.toString().padStart(2,'0')}`);
        return parts.join(' ');
      }
      function update() {
        const now = new Date();
        const toStart = startDate - now;
        const toEnd = endDate - now;
        if (toStart > 0) {
          el.innerHTML = formatCountdown(toStart);
        } else if (toEnd > 0) {
          el.innerHTML = '<span style="color:white; font-weight:700;">Election is LIVE!</span>';
        } else {
          el.innerHTML = '<span style="color:#f87171; font-weight:700;">Election Ended</span>';
          if (interval) clearInterval(interval);
        }
      }
      if (interval) clearInterval(interval);
      update();
      interval = setInterval(update, 1000);
    }

    // === DELETE TIMELINE (from previous fix) ===
    window.deleteTimeline = function(timelineId, button) {
      if (!confirm('Delete this timeline permanently?')) return;
      timelineId = parseInt(timelineId, 10);
      const item = button.closest('.tl-item');
      if (!item) return;
      item.style.opacity = '0.5';

      let url = window.APP_URLS?.delete_timeline || '';
      if (url && !url.endsWith('/')) url += '/';
      url += timelineId + '/';

      fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': CSRF,
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
      })
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => {
        if (data.success) {
          item.remove();
          const btn = document.querySelector('.view-all-btn');
          if (btn) {
            const m = btn.textContent.match(/\((\d+)\)/);
            if (m) {
              let c = parseInt(m[1]) - 1;
              if (c <= 1) btn.remove();
              else btn.textContent = `View All (${c})`;
            }
          }
          updateGreetingAndCountdown();
        } else {
          alert(data.message || 'Delete failed');
          item.style.opacity = '1';
        }
      })
      .catch(err => {
        console.error('Delete error:', err);
        alert('Network error');
        item.style.opacity = '1';
      });
    };

    // === APP_URLS ===
    const deleteUrl = "{% url 'delete_timeline' 999 %}";
    window.APP_URLS = window.APP_URLS || {};
    window.APP_URLS.delete_timeline = deleteUrl.replace(/\/999\/?$/, '');

    // === INITIALIZE ===
    updateGreetingAndCountdown();
    refreshLiveView()
  });
