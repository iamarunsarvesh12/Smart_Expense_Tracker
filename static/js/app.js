/**
 * Smart Home Expense Tracker - Client-side Application Logic
 * Phase 4: AI Voice Assistant & Natural Language Parser Integration
 */

// Application State
const state = {
    currentYear: new Date().getFullYear(),
    currentMonth: new Date().getMonth() + 1, // 1-12
    selectedDate: formatDate(new Date()),
    monthlyData: null,
    rollingData: null,
    categoryChart: null,
    dailyChart: null,
    isRecording: false,
    recognition: null,
    lastTranscript: ""
};

// Category Configuration & Theme Colors
const CATEGORY_CONFIG = {
    "Food & Groceries": {
        icon: "fa-solid fa-basket-shopping",
        bg: "bg-emerald-100",
        text: "text-emerald-700",
        color: "#10b981",
        amtId: "cat-amt-food",
        pctId: "cat-pct-food",
        barId: "cat-bar-food"
    },
    "Fuel & Commute": {
        icon: "fa-solid fa-gas-pump",
        bg: "bg-amber-100",
        text: "text-amber-700",
        color: "#f59e0b",
        amtId: "cat-amt-fuel",
        pctId: "cat-pct-fuel",
        barId: "cat-bar-fuel"
    },
    "Stationery & Office": {
        icon: "fa-solid fa-pen-ruler",
        bg: "bg-sky-100",
        text: "text-sky-700",
        color: "#0284c7",
        amtId: "cat-amt-stationery",
        pctId: "cat-pct-stationery",
        barId: "cat-bar-stationery"
    },
    "Medical & Healthcare": {
        icon: "fa-solid fa-heart-pulse",
        bg: "bg-rose-100",
        text: "text-rose-700",
        color: "#f43f5e",
        amtId: "cat-amt-medical",
        pctId: "cat-pct-medical",
        barId: "cat-bar-medical"
    },
    "General & Daily Utilities": {
        icon: "fa-solid fa-bolt",
        bg: "bg-purple-100",
        text: "text-purple-700",
        color: "#a855f7",
        amtId: "cat-amt-utilities",
        pctId: "cat-pct-utilities",
        barId: "cat-bar-utilities"
    }
};

// Payment Mode Badges
const PAYMENT_BADGES = {
    "UPI": { bg: "bg-indigo-50", text: "text-indigo-700", border: "border-indigo-200", icon: "fa-solid fa-mobile-screen" },
    "Cash": { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200", icon: "fa-solid fa-money-bill-1" },
    "Credit Card": { bg: "bg-violet-50", text: "text-violet-700", border: "border-violet-200", icon: "fa-solid fa-credit-card" },
    "Debit Card": { bg: "bg-cyan-50", text: "text-cyan-700", border: "border-cyan-200", icon: "fa-solid fa-credit-card" },
    "Net Banking": { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200", icon: "fa-solid fa-building-columns" }
};

// =============================================================================
// Initialization
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    initSpeechRecognition();
    loadDashboardData();
});

function initEventListeners() {
    // Calendar Navigation
    document.getElementById('btn-prev-month').addEventListener('click', () => changeMonth(-1));
    document.getElementById('btn-next-month').addEventListener('click', () => changeMonth(1));
    document.getElementById('btn-current-month').addEventListener('click', goToCurrentMonth);

    // Manual Modal Triggers
    const modal = document.getElementById('modal-add-expense');
    document.getElementById('btn-open-add-modal').addEventListener('click', () => openAddModal());
    document.getElementById('btn-add-for-selected-date').addEventListener('click', () => openAddModal(state.selectedDate));
    document.getElementById('btn-empty-add').addEventListener('click', () => openAddModal(state.selectedDate));
    document.getElementById('btn-close-modal').addEventListener('click', closeAddModal);
    document.getElementById('btn-cancel-modal').addEventListener('click', closeAddModal);
    document.getElementById('form-add-expense').addEventListener('submit', handleExpenseSubmit);

    // Voice Assistant Triggers
    document.getElementById('btn-voice-header').addEventListener('click', toggleVoiceRecognition);
    document.getElementById('btn-voice-fab').addEventListener('click', toggleVoiceRecognition);
    document.getElementById('btn-empty-voice').addEventListener('click', toggleVoiceRecognition);
    document.getElementById('btn-stop-voice').addEventListener('click', stopVoiceRecognition);
    document.getElementById('btn-cancel-voice').addEventListener('click', cancelVoiceRecognition);

    // Voice Confirmation Modal Handlers
    const confirmModal = document.getElementById('modal-voice-confirm');
    document.getElementById('btn-close-voice-confirm').addEventListener('click', closeVoiceConfirmModal);
    document.getElementById('btn-cancel-voice-confirm').addEventListener('click', closeVoiceConfirmModal);
    document.getElementById('form-voice-confirm').addEventListener('submit', handleVoiceConfirmSubmit);

    // Export Dropdown
    const exportBtn = document.getElementById('btn-export-menu');
    const exportMenu = document.getElementById('export-menu');
    exportBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        exportMenu.classList.toggle('hidden');
    });
    document.addEventListener('click', () => {
        if (!exportMenu.classList.contains('hidden')) {
            exportMenu.classList.add('hidden');
        }
    });

    // Close Modals on ESC key or backdrop click
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeAddModal();
            closeVoiceConfirmModal();
            cancelVoiceRecognition();
        }
    });
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeAddModal();
    });
    confirmModal.addEventListener('click', (e) => {
        if (e.target === confirmModal) closeVoiceConfirmModal();
    });
}

// =============================================================================
// Web Speech API - Voice Assistant Engine
// =============================================================================

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.warn('Web Speech API is not supported in this browser.');
        return;
    }

    try {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-IN'; // Optimized for Indian English & transliterated Tanglish numbers

        recognition.onstart = () => {
            state.isRecording = true;
            state.lastTranscript = "";
            setVoiceUIState(true);
            document.getElementById('voice-live-transcript').textContent = 'Listening... Speak now.';
        };

        recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            const currentText = finalTranscript || interimTranscript;
            if (currentText) {
                state.lastTranscript = currentText;
                document.getElementById('voice-live-transcript').textContent = `"${currentText}"`;
            }
        };

        recognition.onerror = (event) => {
            console.warn('Speech recognition error:', event.error);
            setVoiceUIState(false);
            if (event.error === 'not-allowed') {
                showToast('Microphone access denied. Please allow microphone permissions.', 'error');
            } else if (event.error === 'no-speech') {
                showToast('No speech was detected. Please try again.', 'error');
            } else {
                showToast(`Voice input error: ${event.error}`, 'error');
            }
        };

        recognition.onend = () => {
            state.isRecording = false;
            setVoiceUIState(false);

            if (state.lastTranscript && state.lastTranscript.trim().length > 0) {
                processVoiceTranscript(state.lastTranscript.trim());
            }
        };

        state.recognition = recognition;
    } catch (err) {
        console.error('Failed to initialize Speech Recognition:', err);
    }
}

function toggleVoiceRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition || !state.recognition) {
        showToast('Voice Recognition is not supported by this browser. Please use Chrome or Edge.', 'error');
        return;
    }

    if (state.isRecording) {
        stopVoiceRecognition();
    } else {
        startVoiceRecognition();
    }
}

function startVoiceRecognition() {
    if (!state.recognition) return;
    try {
        state.recognition.start();
    } catch (e) {
        console.warn('Recognition start error:', e);
    }
}

function stopVoiceRecognition() {
    if (state.recognition && state.isRecording) {
        state.recognition.stop();
    }
    setVoiceUIState(false);
}

function cancelVoiceRecognition() {
    if (state.recognition && state.isRecording) {
        state.lastTranscript = "";
        state.recognition.abort();
    }
    setVoiceUIState(false);
}

function setVoiceUIState(isRecording) {
    const overlay = document.getElementById('voice-listening-overlay');
    const fabIcon = document.getElementById('fab-mic-icon');
    const fabBtn = document.getElementById('btn-voice-fab');
    const headerPulse = document.getElementById('voice-header-pulse');

    if (isRecording) {
        overlay.classList.remove('hidden');
        fabBtn.classList.add('recording-pulse', 'bg-rose-600');
        fabIcon.className = 'fa-solid fa-stop text-xl';
        headerPulse.classList.add('bg-rose-500');
    } else {
        overlay.classList.add('hidden');
        fabBtn.classList.remove('recording-pulse', 'bg-rose-600');
        fabIcon.className = 'fa-solid fa-microphone text-xl';
        headerPulse.classList.remove('bg-rose-500');
    }
}

// =============================================================================
// NLP Voice Extraction & Confirmation Flow
// =============================================================================

async function processVoiceTranscript(transcript) {
    showToast('Analyzing speech with AI engine...', 'info');

    try {
        const response = await fetch('/api/parse-voice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: transcript })
        });

        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || 'Unable to extract expense details');
        }

        openVoiceConfirmModal(result.transcript, result.data);
    } catch (err) {
        console.error('Voice parse error:', err);
        showToast(err.message || 'Failed to parse voice command. Try again.', 'error');
    }
}

function openVoiceConfirmModal(rawTranscript, extractedData) {
    const modal = document.getElementById('modal-voice-confirm');

    // Populate transcript text
    document.getElementById('voice-original-text').textContent = `"${rawTranscript}"`;

    // Populate pre-filled form fields
    document.getElementById('voice-input-date').value = extractedData.date || formatDate(new Date());
    document.getElementById('voice-input-time').value = (extractedData.time || new Date().toTimeString()).slice(0, 5);
    document.getElementById('voice-input-category').value = extractedData.category || "Food & Groceries";
    document.getElementById('voice-input-item').value = extractedData.item || "";
    document.getElementById('voice-input-amount').value = extractedData.amount > 0 ? extractedData.amount : "";
    document.getElementById('voice-input-payment-mode').value = extractedData.payment_mode || "UPI";
    document.getElementById('voice-input-notes').value = extractedData.notes || `Voice input: "${rawTranscript}"`;

    modal.classList.remove('hidden');
    document.getElementById('voice-input-amount').focus();
}

function closeVoiceConfirmModal() {
    document.getElementById('modal-voice-confirm').classList.add('hidden');
}

async function handleVoiceConfirmSubmit(e) {
    e.preventDefault();

    const submitBtn = document.getElementById('btn-save-voice-confirm');
    const originalText = submitBtn.innerHTML;

    const payload = {
        date: document.getElementById('voice-input-date').value,
        time: document.getElementById('voice-input-time').value ? `${document.getElementById('voice-input-time').value}:00` : '',
        category: document.getElementById('voice-input-category').value,
        item: document.getElementById('voice-input-item').value.trim(),
        amount: parseFloat(document.getElementById('voice-input-amount').value),
        payment_mode: document.getElementById('voice-input-payment-mode').value,
        notes: document.getElementById('voice-input-notes').value.trim()
    };

    try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Saving...</span>`;

        const response = await fetch('/api/expenses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.message || 'Failed to save expense');
        }

        // Play synthetic confirmation chime
        playSuccessChime();

        showToast(`Voice expense recorded: ${payload.item} (₹${payload.amount})`, 'success');
        closeVoiceConfirmModal();

        // Refresh state
        state.selectedDate = payload.date;
        await loadDashboardData();
    } catch (err) {
        console.error('Confirmation save error:', err);
        showToast(err.message || 'Error recording expense', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// =============================================================================
// Web Audio API - Synthesized Success Chime
// =============================================================================

function playSuccessChime() {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;

        const ctx = new AudioCtx();
        const now = ctx.currentTime;

        // Two-tone rising chime (E5 -> B5)
        const osc1 = ctx.createOscillator();
        const osc2 = ctx.createOscillator();
        const gain = ctx.createGain();

        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(659.25, now); // E5
        osc1.frequency.setValueAtTime(987.77, now + 0.12); // B5

        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);

        osc1.connect(gain);
        gain.connect(ctx.destination);

        osc1.start(now);
        osc1.stop(now + 0.5);
    } catch (e) {
        // Audio synthesis fallback (silent)
    }
}

// =============================================================================
// Core Data Fetchers
// =============================================================================

async function loadDashboardData() {
    await Promise.all([
        fetchMonthlySummary(state.currentYear, state.currentMonth),
        fetchRollingSummary(),
        fetchDailyExpenses(state.selectedDate),
        fetchTodayExpense()
    ]);
}

async function fetchMonthlySummary(year, month) {
    try {
        const response = await fetch(`/api/summary/monthly?year=${year}&month=${month}`);
        if (!response.ok) throw new Error('Failed to load monthly summary');
        const data = await response.json();
        state.monthlyData = data;

        // Update UI
        updateMonthBadge(data.month_label);
        document.getElementById('calendar-title').textContent = data.month_label;
        document.getElementById('stat-month-total').textContent = formatCurrency(data.total_spending);
        document.getElementById('stat-month-transactions').textContent = `${data.transaction_count} transaction${data.transaction_count === 1 ? '' : 's'} recorded`;

        // Update Category highlight cards
        updateCategoryCards(data.category_breakdown, data.category_percentages);

        // Render Calendar Grid & Analytics Charts
        renderCalendar(year, month, data.daily_totals);
        renderCharts(data);
    } catch (error) {
        console.error('Error fetching monthly summary:', error);
        showToast('Error loading monthly summary', 'error');
    }
}

async function fetchRollingSummary() {
    try {
        const response = await fetch('/api/summary/rolling-3-months');
        if (!response.ok) throw new Error('Failed to load rolling summary');
        const data = await response.json();
        state.rollingData = data;

        document.getElementById('stat-rolling-daily-avg').textContent = formatCurrency(data.daily_average);
        document.getElementById('stat-rolling-total').textContent = `Total: ${formatCurrency(data.total_expense)} over ${data.period.total_days} days`;
    } catch (error) {
        console.error('Error fetching rolling summary:', error);
    }
}

async function fetchTodayExpense() {
    try {
        const todayStr = formatDate(new Date());
        const response = await fetch(`/api/expenses?date=${todayStr}`);
        if (!response.ok) return;
        const data = await response.json();
        document.getElementById('stat-today-total').textContent = formatCurrency(data.daily_total);
        document.getElementById('stat-today-date').textContent = new Date().toLocaleDateString('default', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch (error) {
        console.error('Error fetching today expense:', error);
    }
}

async function fetchDailyExpenses(dateStr) {
    state.selectedDate = dateStr;
    const titleEl = document.getElementById('selected-date-title');
    const totalEl = document.getElementById('selected-date-total');
    const countEl = document.getElementById('selected-date-count');
    const listContainer = document.getElementById('daily-expenses-list');
    const emptyState = document.getElementById('daily-empty-state');

    // Human formatted title
    const dateObj = new Date(dateStr + "T00:00:00");
    titleEl.textContent = dateObj.toLocaleDateString('default', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' });

    listContainer.innerHTML = `
        <div class="py-8 text-center text-slate-400">
            <i class="fa-solid fa-circle-notch fa-spin text-xl text-brand-600 mb-2"></i>
            <p class="text-xs">Loading expenses...</p>
        </div>
    `;
    emptyState.classList.add('hidden');

    try {
        const response = await fetch(`/api/expenses?date=${dateStr}`);
        if (!response.ok) throw new Error('Failed to fetch expenses');
        const data = await response.json();

        totalEl.textContent = formatCurrency(data.daily_total);
        countEl.textContent = `(${data.count} item${data.count === 1 ? '' : 's'})`;

        if (!data.expenses || data.expenses.length === 0) {
            listContainer.innerHTML = '';
            emptyState.classList.remove('hidden');
            return;
        }

        emptyState.classList.add('hidden');
        listContainer.innerHTML = data.expenses.map(exp => createExpenseCard(exp)).join('');
    } catch (error) {
        console.error('Error loading daily expenses:', error);
        listContainer.innerHTML = `<div class="p-4 text-xs text-rose-600 bg-rose-50 rounded-xl">Error loading expenses for this date.</div>`;
    }
}

// =============================================================================
// Calendar Component
// =============================================================================

function renderCalendar(year, month, dailyTotals) {
    const grid = document.getElementById('calendar-grid');
    grid.innerHTML = '';

    const dailyMap = {};
    if (Array.isArray(dailyTotals)) {
        dailyTotals.forEach(item => {
            dailyMap[item.date] = item;
        });
    }

    const firstDayIndex = new Date(year, month - 1, 1).getDay(); // 0 = Sunday
    const daysInMonth = new Date(year, month, 0).getDate();
    const todayStr = formatDate(new Date());

    // Leading padding cells
    for (let i = 0; i < firstDayIndex; i++) {
        const emptyCell = document.createElement('div');
        emptyCell.className = 'calendar-tile rounded-xl border border-transparent bg-slate-50/50 opacity-40';
        grid.appendChild(emptyCell);
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dayExpense = dailyMap[dateStr];
        const isToday = (dateStr === todayStr);
        const isSelected = (dateStr === state.selectedDate);

        const tile = document.createElement('button');
        tile.type = 'button';
        tile.dataset.date = dateStr;
        tile.className = `calendar-tile rounded-xl border p-2 flex flex-col justify-between text-left transition-all ${
            isSelected 
                ? 'selected' 
                : isToday 
                    ? 'today border-blue-400 bg-blue-50/70' 
                    : 'border-slate-200/90 bg-white hover:bg-slate-50'
        }`;

        tile.innerHTML = `
            <div class="flex items-center justify-between w-full">
                <span class="text-xs font-bold ${isToday ? 'text-blue-700 font-extrabold' : 'text-slate-700'}">
                    ${day}
                </span>
                ${dayExpense ? `<span class="h-2 w-2 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/40"></span>` : ''}
            </div>
            <div class="w-full truncate text-[11px] font-semibold text-right ${dayExpense ? 'text-emerald-700' : 'text-slate-300'}">
                ${dayExpense ? formatCurrencyCompact(dayExpense.total) : '—'}
            </div>
        `;

        tile.addEventListener('click', () => {
            document.querySelectorAll('.calendar-tile').forEach(t => t.classList.remove('selected'));
            tile.classList.add('selected');
            fetchDailyExpenses(dateStr);
        });

        grid.appendChild(tile);
    }
}

function changeMonth(delta) {
    state.currentMonth += delta;
    if (state.currentMonth < 1) {
        state.currentMonth = 12;
        state.currentYear -= 1;
    } else if (state.currentMonth > 12) {
        state.currentMonth = 1;
        state.currentYear += 1;
    }
    fetchMonthlySummary(state.currentYear, state.currentMonth);
}

function goToCurrentMonth() {
    const now = new Date();
    state.currentYear = now.getFullYear();
    state.currentMonth = now.getMonth() + 1;
    state.selectedDate = formatDate(now);
    fetchMonthlySummary(state.currentYear, state.currentMonth);
    fetchDailyExpenses(state.selectedDate);
}

// =============================================================================
// UI Component Helpers
// =============================================================================

function createExpenseCard(exp) {
    const catCfg = CATEGORY_CONFIG[exp.category] || {
        icon: "fa-solid fa-tag",
        bg: "bg-slate-100",
        text: "text-slate-700",
        color: "#64748b"
    };

    const payBadge = PAYMENT_BADGES[exp.payment_mode] || {
        bg: "bg-slate-100",
        text: "text-slate-700",
        border: "border-slate-200",
        icon: "fa-solid fa-receipt"
    };

    return `
        <div class="bg-white border border-slate-200/90 rounded-xl p-3.5 hover:shadow-sm hover:border-slate-300 transition-all">
            <div class="flex items-start justify-between">
                <div class="flex items-center space-x-3">
                    <div class="h-9 w-9 rounded-xl ${catCfg.bg} ${catCfg.text} flex items-center justify-center text-sm shadow-sm flex-shrink-0">
                        <i class="${catCfg.icon}"></i>
                    </div>
                    <div>
                        <h4 class="text-xs font-bold text-slate-900 leading-tight">${escapeHtml(exp.item)}</h4>
                        <span class="text-[11px] text-slate-400 font-medium">${escapeHtml(exp.category)}</span>
                    </div>
                </div>
                <div class="text-right flex-shrink-0 ml-2">
                    <span class="text-sm font-extrabold text-slate-900 block">${formatCurrency(exp.amount)}</span>
                </div>
            </div>

            <div class="flex items-center justify-between text-[10px] text-slate-400 pt-2.5 mt-2.5 border-t border-slate-100">
                <div class="flex items-center space-x-2">
                    <span class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full border ${payBadge.bg} ${payBadge.text} ${payBadge.border} font-semibold">
                        <i class="${payBadge.icon} text-[9px]"></i>
                        <span>${escapeHtml(exp.payment_mode)}</span>
                    </span>
                    ${exp.time ? `<span><i class="fa-regular fa-clock mr-0.5"></i>${escapeHtml(exp.time.slice(0, 5))}</span>` : ''}
                </div>
                ${exp.notes ? `<span class="italic text-slate-500 max-w-[130px] truncate" title="${escapeHtml(exp.notes)}">${escapeHtml(exp.notes)}</span>` : ''}
            </div>
        </div>
    `;
}

function updateCategoryCards(breakdown, percentages) {
    if (!breakdown) return;
    Object.keys(CATEGORY_CONFIG).forEach(cat => {
        const cfg = CATEGORY_CONFIG[cat];
        const amt = breakdown[cat] || 0.0;
        const pct = percentages ? (percentages[cat] || 0.0) : 0.0;

        const amtEl = document.getElementById(cfg.amtId);
        const pctEl = document.getElementById(cfg.pctId);
        const barEl = document.getElementById(cfg.barId);

        if (amtEl) amtEl.textContent = formatCurrency(amt);
        if (pctEl) pctEl.textContent = `${pct}% of month`;
        if (barEl) barEl.style.width = `${Math.min(pct, 100)}%`;
    });
}

function updateMonthBadge(label) {
    const badge = document.getElementById('current-month-badge');
    if (badge) badge.textContent = label;
}

// =============================================================================
// Analytics Charts (Chart.js)
// =============================================================================

function renderCharts(data) {
    renderCategoryDoughnut(data.category_breakdown);
    renderDailyBarChart(data.daily_totals, state.currentYear, state.currentMonth);
}

function renderCategoryDoughnut(breakdown) {
    const ctx = document.getElementById('chart-category-doughnut');
    if (!ctx) return;

    const labels = Object.keys(CATEGORY_CONFIG);
    const amounts = labels.map(l => breakdown ? (breakdown[l] || 0.0) : 0.0);
    const colors = labels.map(l => CATEGORY_CONFIG[l].color);

    const total = amounts.reduce((a, b) => a + b, 0);
    const chartData = total > 0 ? amounts : [1];
    const chartColors = total > 0 ? colors : ['#e2e8f0'];

    if (state.categoryChart) {
        state.categoryChart.destroy();
    }

    state.categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: total > 0 ? labels : ['No Data'],
            datasets: [{
                data: chartData,
                backgroundColor: chartColors,
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '72%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (total === 0) return ' No expenses yet';
                            const val = context.parsed;
                            const pct = ((val / total) * 100).toFixed(1);
                            return ` ${context.label}: ₹${val.toFixed(2)} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

function renderDailyBarChart(dailyTotals, year, month) {
    const ctx = document.getElementById('chart-daily-bars');
    if (!ctx) return;

    const daysInMonth = new Date(year, month, 0).getDate();
    const dailyMap = {};
    if (Array.isArray(dailyTotals)) {
        dailyTotals.forEach(item => {
            const dayNum = parseInt(item.date.split('-')[2], 10);
            dailyMap[dayNum] = item.total;
        });
    }

    const labels = [];
    const values = [];
    for (let day = 1; day <= daysInMonth; day++) {
        labels.push(day);
        values.push(dailyMap[day] || 0.0);
    }

    if (state.dailyChart) {
        state.dailyChart.destroy();
    }

    state.dailyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Spent (₹)',
                data: values,
                backgroundColor: '#6366f1',
                borderRadius: 4,
                hoverBackgroundColor: '#4f46e5'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function(items) {
                            return `Day ${items[0].label} (${state.monthlyData ? state.monthlyData.month_label : ''})`;
                        },
                        label: function(item) {
                            return ` Total: ₹${item.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        font: { size: 9 },
                        maxTicksLimit: 16
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        font: { size: 9 },
                        callback: value => '₹' + value
                    }
                }
            }
        }
    });
}

// =============================================================================
// Quick Expense Form & Modal Handlers (Manual Entry)
// =============================================================================

function openAddModal(dateToSelect = null) {
    const modal = document.getElementById('modal-add-expense');
    const inputDate = document.getElementById('input-date');
    const inputTime = document.getElementById('input-time');

    inputDate.value = dateToSelect || formatDate(new Date());

    const now = new Date();
    inputTime.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

    modal.classList.remove('hidden');
    document.getElementById('input-item').focus();
}

function closeAddModal() {
    const modal = document.getElementById('modal-add-expense');
    modal.classList.add('hidden');
    document.getElementById('form-add-expense').reset();
}

async function handleExpenseSubmit(e) {
    e.preventDefault();

    const submitBtn = document.getElementById('btn-submit-expense');
    const originalText = submitBtn.innerHTML;

    const payload = {
        date: document.getElementById('input-date').value,
        time: document.getElementById('input-time').value ? `${document.getElementById('input-time').value}:00` : '',
        category: document.getElementById('input-category').value,
        item: document.getElementById('input-item').value.trim(),
        amount: parseFloat(document.getElementById('input-amount').value),
        payment_mode: document.getElementById('input-payment-mode').value,
        notes: document.getElementById('input-notes').value.trim()
    };

    try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Saving...</span>`;

        const response = await fetch('/api/expenses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || 'Failed to record expense');
        }

        playSuccessChime();
        showToast('Expense recorded successfully!', 'success');
        closeAddModal();

        // Refresh state
        state.selectedDate = payload.date;
        await loadDashboardData();
    } catch (error) {
        console.error('Submission error:', error);
        showToast(error.message || 'Error recording expense', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// =============================================================================
// Toast Notifications
// =============================================================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const isSuccess = type === 'success';
    const isError = type === 'error';

    toast.className = `pointer-events-auto flex items-center space-x-2.5 px-4 py-3 rounded-xl shadow-lg border text-xs font-semibold animate-scale-up ${
        isSuccess ? 'bg-emerald-600 text-white border-emerald-700' :
        isError ? 'bg-rose-600 text-white border-rose-700' :
        'bg-slate-900 text-white border-slate-800'
    }`;

    toast.innerHTML = `
        <i class="${isSuccess ? 'fa-solid fa-circle-check' : isError ? 'fa-solid fa-circle-exclamation' : 'fa-solid fa-circle-info'} text-sm"></i>
        <span>${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(8px)';
        toast.style.transition = 'all 0.25s ease';
        setTimeout(() => toast.remove(), 250);
    }, 3200);
}

// =============================================================================
// Formatting Utilities
// =============================================================================

function formatDate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function formatCurrency(amount) {
    const num = parseFloat(amount) || 0.0;
    return '₹' + num.toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatCurrencyCompact(amount) {
    const num = parseFloat(amount) || 0.0;
    if (num >= 100000) return '₹' + (num / 100000).toFixed(1) + 'L';
    if (num >= 1000) return '₹' + (num / 1000).toFixed(1) + 'k';
    return '₹' + Math.round(num);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
