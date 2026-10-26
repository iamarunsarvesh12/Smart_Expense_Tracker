/* Phase 3 Compatibility */
const CATEGORY_CONFIG = {};
/**
 * Smart Home Expense Tracker - 50:20:20:10 Budget Engine
 * Linear & Stripe inspired interactive UI/UX architecture.
 */

(function () {
  'use strict';

  // Application State
  const state = {
    currentMonth: getInitialMonth(), // 'YYYY-MM'
    selectedDate: null,              // 'YYYY-MM-DD' or null
    activeCategory: 'all',           // filter category
    searchQuery: '',                 // search term
    budgetConfig: null,              // from /api/budget
    monthlyMetrics: null,            // from /api/summary/monthly
    chartInstance: null,             // Chart.js instance
    isListening: false,              // Speech recognition status
    speechRecognition: null          // Web Speech API
  };

  function getInitialMonth() {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, '0');
    return `${y}-${m}`;
  }

  function formatCurrency(val) {
    const num = parseFloat(val) || 0.0;
    return '₹' + num.toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function formatShortCurrency(val) {
    const num = parseFloat(val) || 0.0;
    if (num >= 100000) {
      return '₹' + (num / 100000).toFixed(1) + 'L';
    }
    if (num >= 1000) {
      return '₹' + (num / 1000).toFixed(1) + 'k';
    }
    return '₹' + num.toFixed(0);
  }

  // ==========================================
  // INITIALIZATION
  // ==========================================
  document.addEventListener('DOMContentLoaded', () => {
    initDOMReferences();
    initSpeechRecognition();
    setupEventListeners();
    
    // Set default form date to today
    const todayStr = new Date().toISOString().split('T')[0];
    const dateInput = document.getElementById('exp-date');
    if (dateInput) dateInput.value = todayStr;

    // Load initial budget and data
    loadAllData();
  });

  // DOM Elements Cache
  const dom = {};
  function initDOMReferences() {
    dom.currentMonthDisplay = document.getElementById('current-month-display');
    dom.prevMonthBtn = document.getElementById('prev-month-btn');
    dom.nextMonthBtn = document.getElementById('next-month-btn');
    dom.todayBtn = document.getElementById('today-btn');

    // Ribbon Elements
    dom.dispIncomeVal = document.getElementById('disp-income-val');
    dom.dispTotalSpent = document.getElementById('disp-total-spent');
    dom.meterTotalOutflow = document.getElementById('meter-total-outflow');

    dom.needsSpentVal = document.getElementById('needs-spent-val');
    dom.needsLimitVal = document.getElementById('needs-limit-val');
    dom.meterNeeds = document.getElementById('meter-needs');
    dom.needsRemainingVal = document.getElementById('needs-remaining-val');
    dom.needsStatusDesc = document.getElementById('needs-status-desc');

    dom.lifestyleSpentVal = document.getElementById('lifestyle-spent-val');
    dom.lifestyleLimitVal = document.getElementById('lifestyle-limit-val');
    dom.meterLifestyle = document.getElementById('meter-lifestyle');
    dom.lifestyleRemainingVal = document.getElementById('lifestyle-remaining-val');
    dom.lifestyleStatusDesc = document.getElementById('lifestyle-status-desc');

    dom.investmentsAllocatedVal = document.getElementById('investments-allocated-val');
    dom.investmentsTargetVal = document.getElementById('investments-target-val');
    dom.meterInvestments = document.getElementById('meter-investments');
    dom.investmentsPctVal = document.getElementById('investments-pct-val');
    dom.investmentsStatusBadge = document.getElementById('investments-status-badge');

    dom.emergencyAllocatedVal = document.getElementById('emergency-allocated-val');
    dom.emergencyTargetVal = document.getElementById('emergency-target-val');
    dom.meterEmergency = document.getElementById('meter-emergency');
    dom.emergencyBufferSummary = document.getElementById('emergency-buffer-summary');
    dom.emergencyStatusBadge = document.getElementById('emergency-status-badge');

    // Form
    dom.expenseForm = document.getElementById('expense-form');
    dom.expDate = document.getElementById('exp-date');
    dom.expCategory = document.getElementById('exp-category');
    dom.expItem = document.getElementById('exp-item');
    dom.expAmount = document.getElementById('exp-amount');
    dom.expPaymentMode = document.getElementById('exp-payment-mode');
    dom.expNotes = document.getElementById('exp-notes');

    // Calendar
    dom.calDaysGrid = document.getElementById('cal-days-grid');
    dom.calendarActiveFilter = document.getElementById('calendar-active-filter');
    dom.calendarFilterText = document.getElementById('calendar-filter-text');
    dom.calendarClearFilterBtn = document.getElementById('calendar-clear-filter-btn');

    // Ledger
    dom.ledgerFeedContainer = document.getElementById('ledger-feed-container');
    dom.ledgerCountBadge = document.getElementById('ledger-count-badge');
    dom.ledgerSearchInput = document.getElementById('ledger-search-input');
    dom.clearSearchBtn = document.getElementById('clear-search-btn');
    dom.ledgerCategoryFilter = document.getElementById('ledger-category-filter');

    // Chart & Stats
    dom.chartCanvas = document.getElementById('macro-budget-chart');
    dom.chipNeedsSpent = document.getElementById('chip-needs-spent');
    dom.chipLifestyleSpent = document.getElementById('chip-lifestyle-spent');
    dom.chipInvestSpent = document.getElementById('chip-invest-spent');
    dom.chipEmergencySpent = document.getElementById('chip-emergency-spent');

    // Voice Elements
    dom.voiceToggleBtn = document.getElementById('voice-toggle-btn');
    dom.voiceFormBtn = document.getElementById('voice-form-btn');
    dom.voiceTickerBanner = document.getElementById('voice-ticker-banner');
    dom.voiceTranscriptText = document.getElementById('voice-transcript-text');
    dom.voiceStopBtn = document.getElementById('voice-stop-btn');

    // Nav Actions & Settings Dropdown
    dom.settingsMenuBtn = document.getElementById('settings-menu-btn');
    dom.settingsDropdown = document.getElementById('settings-dropdown');
    dom.openSalaryModalBtn = document.getElementById('open-salary-modal-btn');
    dom.editIncomeQuickBtn = document.getElementById('edit-income-quick-btn');
    dom.exportCsvBtn = document.getElementById('export-csv-btn');
    dom.resetSystemBtn = document.getElementById('reset-system-btn');
    dom.emailReportBtn = document.getElementById('email-report-btn');

    // Salary Modal
    dom.salaryModal = document.getElementById('salary-modal');
    dom.closeSalaryModalBtn = document.getElementById('close-salary-modal-btn');
    dom.cancelSalaryModalBtn = document.getElementById('cancel-salary-modal-btn');
    dom.salaryConfigForm = document.getElementById('salary-config-form');
    dom.modalSalaryInput = document.getElementById('modal-salary-input');
    dom.modalEmergencyAccumulated = document.getElementById('modal-emergency-accumulated');
    dom.prevNeedsTarget = document.getElementById('prev-needs-target');
    dom.prevLifeTarget = document.getElementById('prev-life-target');
    dom.prevInvTarget = document.getElementById('prev-inv-target');
    dom.prevEmgTarget = document.getElementById('prev-emg-target');

    // Toast Container
    dom.toastStack = document.getElementById('toast-stack');
  }

  // ==========================================
  // DATA FETCHING & SYNCHRONIZATION
  // ==========================================
  async function loadAllData() {
    updateMonthDisplay();
    try {
      // 1. Fetch Budget Config
      const budgetRes = await fetch('/api/budget');
      if (budgetRes.ok) {
        state.budgetConfig = await budgetRes.json();
      }

      // 2. Fetch Monthly Summary & Metrics
      const summaryRes = await fetch(`/api/summary/monthly?month=${state.currentMonth}`);
      if (summaryRes.ok) {
        const json = await summaryRes.json();
        state.monthlyMetrics = json.data;
      }

      // 3. Render all UI modules
      renderBudgetRibbon();
      renderMiniCalendar();
      renderChart();
      await fetchAndRenderLedger();

    } catch (err) {
      console.error('Error loading tracker data:', err);
      showToast('Error syncing with backend server', 'error');
    }
  }

  // Month Display Formatter (e.g., "October 2026")
  function updateMonthDisplay() {
    if (!dom.currentMonthDisplay) return;
    const [year, month] = state.currentMonth.split('-');
    const dateObj = new Date(parseInt(year, 10), parseInt(month, 10) - 1, 1);
    dom.currentMonthDisplay.textContent = dateObj.toLocaleDateString('en-US', {
      month: 'long',
      year: 'numeric'
    });
  }

  // ==========================================
  // 50:20:20:10 BUDGET RIBBON RENDERING
  // ==========================================
  function renderBudgetRibbon() {
    const m = state.monthlyMetrics;
    if (!m) return;

    const pNeeds = m.pillars.needs;
    const pLife = m.pillars.lifestyle;
    const pInv = m.pillars.investments;
    const pEmg = m.pillars.emergency;

    // 1. Total Salary Pillar
    dom.dispIncomeVal.textContent = formatCurrency(m.income);
    dom.dispTotalSpent.textContent = formatCurrency(m.total_spent);
    const totalOutflowPct = Math.min(100, Math.round((m.total_spent / m.income) * 100) || 0);
    dom.meterTotalOutflow.style.width = `${totalOutflowPct}%`;

    // 2. 50% Household Needs Pillar
    dom.needsSpentVal.textContent = formatCurrency(pNeeds.spent);
    dom.needsLimitVal.textContent = formatCurrency(pNeeds.limit);
    dom.meterNeeds.style.width = `${Math.min(100, pNeeds.pct_used)}%`;
    setHairlineColor(dom.meterNeeds, pNeeds.status);

    if (pNeeds.remaining >= 0) {
      dom.needsStatusDesc.textContent = 'Remaining:';
      dom.needsRemainingVal.textContent = `${formatCurrency(pNeeds.remaining)} (${pNeeds.pct_used}%)`;
    } else {
      dom.needsStatusDesc.textContent = 'Overspent:';
      dom.needsRemainingVal.textContent = `+${formatCurrency(Math.abs(pNeeds.remaining))} (${pNeeds.pct_used}%)`;
    }

    // 3. 20% Lifestyle & Wants Pillar
    dom.lifestyleSpentVal.textContent = formatCurrency(pLife.spent);
    dom.lifestyleLimitVal.textContent = formatCurrency(pLife.limit);
    dom.meterLifestyle.style.width = `${Math.min(100, pLife.pct_used)}%`;
    setHairlineColor(dom.meterLifestyle, pLife.status);

    if (pLife.remaining >= 0) {
      dom.lifestyleStatusDesc.textContent = 'Remaining:';
      dom.lifestyleRemainingVal.textContent = `${formatCurrency(pLife.remaining)} (${pLife.pct_used}%)`;
    } else {
      dom.lifestyleStatusDesc.textContent = 'Overspent:';
      dom.lifestyleRemainingVal.textContent = `+${formatCurrency(Math.abs(pLife.remaining))} (${pLife.pct_used}%)`;
    }

    // 4. 20% Investments & SIP Pillar
    dom.investmentsAllocatedVal.textContent = formatCurrency(pInv.allocated);
    dom.investmentsTargetVal.textContent = formatCurrency(pInv.target);
    dom.meterInvestments.style.width = `${Math.min(100, pInv.pct_achieved)}%`;
    dom.investmentsPctVal.textContent = `${pInv.pct_achieved}%`;
    dom.investmentsStatusBadge.textContent = pInv.pct_achieved >= 100 ? 'Target Met ✓' : `Target ${formatShortCurrency(pInv.target)}`;

    // 5. 10% Emergency Fund Pillar
    dom.emergencyAllocatedVal.textContent = formatCurrency(pEmg.allocated);
    dom.emergencyTargetVal.textContent = formatCurrency(pEmg.target);
    dom.meterEmergency.style.width = `${Math.min(100, pEmg.pct_achieved)}%`;
    dom.emergencyBufferSummary.textContent = `${formatShortCurrency(pEmg.accumulated_total)} / ${formatShortCurrency(pEmg.goal_6_months)} (${pEmg.goal_progress_pct}%)`;
    dom.emergencyStatusBadge.textContent = pEmg.pct_achieved >= 100 ? 'Buffer Added ✓' : `Target ${formatShortCurrency(pEmg.target)}`;

    // Quick stats chips
    dom.chipNeedsSpent.textContent = formatCurrency(pNeeds.spent);
    dom.chipLifestyleSpent.textContent = formatCurrency(pLife.spent);
    dom.chipInvestSpent.textContent = formatCurrency(pInv.allocated);
    dom.chipEmergencySpent.textContent = formatCurrency(pEmg.allocated);
  }

  function setHairlineColor(meterElem, status) {
    meterElem.classList.remove('status-normal', 'status-warning', 'status-danger');
    if (status === 'danger') {
      meterElem.classList.add('status-danger');
    } else if (status === 'warning') {
      meterElem.classList.add('status-warning');
    } else {
      meterElem.classList.add('status-normal');
    }
  }

  // ==========================================
  // CHART.JS MACRO COMPARISON BAR CHART
  // ==========================================
  function renderChart() {
    if (!dom.chartCanvas || typeof Chart === 'undefined') return;

    const m = state.monthlyMetrics;
    if (!m) return;

    const pNeeds = m.pillars.needs;
    const pLife = m.pillars.lifestyle;
    const pInv = m.pillars.investments;
    const pEmg = m.pillars.emergency;

    const labels = [
      '50% Needs',
      '20% Lifestyle',
      '20% Investments',
      '10% Emergency'
    ];

    const targetData = [
      pNeeds.limit,
      pLife.limit,
      pInv.target,
      pEmg.target
    ];

    const actualData = [
      pNeeds.spent,
      pLife.spent,
      pInv.allocated,
      pEmg.allocated
    ];

    // Colors matching Linear palette
    const actualColors = [
      pNeeds.status === 'danger' ? '#f43f5e' : (pNeeds.status === 'warning' ? '#f59e0b' : '#10b981'),
      pLife.status === 'danger' ? '#f43f5e' : (pLife.status === 'warning' ? '#f59e0b' : '#10b981'),
      '#6366f1',
      '#0ea5e9'
    ];

    if (state.chartInstance) {
      state.chartInstance.data.datasets[0].data = targetData;
      state.chartInstance.data.datasets[1].data = actualData;
      state.chartInstance.data.datasets[1].backgroundColor = actualColors;
      state.chartInstance.update();
      return;
    }

    const ctx = dom.chartCanvas.getContext('2d');
    state.chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Rule Target Limit',
            data: targetData,
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
            borderColor: 'rgba(255, 255, 255, 0.2)',
            borderWidth: 1,
            borderRadius: 4,
            barPercentage: 0.65,
            categoryPercentage: 0.7
          },
          {
            label: 'Actual Spend / Inflow',
            data: actualData,
            backgroundColor: actualColors,
            borderColor: 'transparent',
            borderWidth: 0,
            borderRadius: 4,
            barPercentage: 0.65,
            categoryPercentage: 0.7
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
            align: 'end',
            labels: {
              boxWidth: 10,
              boxHeight: 10,
              color: '#9ca3af',
              font: { family: "'Geist Mono', monospace", size: 10.5 }
            }
          },
          tooltip: {
            backgroundColor: '#16181b',
            titleColor: '#ffffff',
            bodyColor: '#e5e7eb',
            borderColor: '#26292d',
            borderWidth: 1,
            padding: 8,
            boxPadding: 4,
            usePointStyle: true,
            callbacks: {
              label: function (ctx) {
                return ` ${ctx.dataset.label}: ₹${ctx.parsed.y.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              color: '#9ca3af',
              font: { family: "'Geist', sans-serif", size: 11.5, weight: '500' }
            }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: {
              color: '#6b7280',
              font: { family: "'Geist Mono', monospace", size: 10.5 },
              callback: function (val) {
                return '₹' + val.toLocaleString('en-IN');
              }
            }
          }
        }
      }
    });
  }

  // ==========================================
  // MINIMALIST MINI-CALENDAR
  // ==========================================
  function renderMiniCalendar() {
    if (!dom.calDaysGrid) return;
    dom.calDaysGrid.innerHTML = '';

    const [yearStr, monthStr] = state.currentMonth.split('-');
    const year = parseInt(yearStr, 10);
    const month = parseInt(monthStr, 10) - 1; // 0-indexed

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const totalDays = lastDay.getDate();

    // Monday is index 0 in our grid (Mo Tu We Th Fr Sa Su)
    // JS getDay(): 0 is Sunday, 1 is Monday...
    let startingDayOfWeek = firstDay.getDay() - 1;
    if (startingDayOfWeek === -1) startingDayOfWeek = 6;

    // Active spend days map
    const dailySpend = (state.monthlyMetrics && state.monthlyMetrics.daily_spending) || {};

    // Today string
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

    // Blank cells before first day
    for (let i = 0; i < startingDayOfWeek; i++) {
      const emptyCell = document.createElement('div');
      emptyCell.className = 'cal-day-cell empty-day';
      dom.calDaysGrid.appendChild(emptyCell);
    }

    // Days 1..totalDays
    for (let day = 1; day <= totalDays; day++) {
      const dateKey = `${yearStr}-${monthStr}-${String(day).padStart(2, '0')}`;
      const cell = document.createElement('div');
      cell.className = 'cal-day-cell';
      cell.textContent = day;
      cell.dataset.date = dateKey;

      if (dateKey === todayStr) {
        cell.classList.add('is-today');
      }

      if (dateKey === state.selectedDate) {
        cell.classList.add('is-selected');
      }

      if (dailySpend[dateKey] !== undefined) {
        cell.classList.add('has-spend');
        cell.title = `${dateKey}: Outflow ₹${dailySpend[dateKey].toLocaleString('en-IN')}`;
      }

      cell.addEventListener('click', () => {
        handleDateClick(dateKey);
      });

      dom.calDaysGrid.appendChild(cell);
    }

    updateCalendarFilterPill();
  }

  function handleDateClick(dateKey) {
    if (state.selectedDate === dateKey) {
      // Toggle off
      state.selectedDate = null;
    } else {
      state.selectedDate = dateKey;
      // Pre-fill form date
      if (dom.expDate) dom.expDate.value = dateKey;
    }

    renderMiniCalendar();
    fetchAndRenderLedger();
  }

  function updateCalendarFilterPill() {
    if (!dom.calendarActiveFilter) return;
    if (state.selectedDate) {
      const parts = state.selectedDate.split('-');
      const d = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
      dom.calendarFilterText.textContent = d.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });
      dom.calendarActiveFilter.style.display = 'inline-flex';
    } else {
      dom.calendarActiveFilter.style.display = 'none';
    }
  }

  // ==========================================
  // TRANSACTION FEED / LEDGER
  // ==========================================
  async function fetchAndRenderLedger() {
    if (!dom.ledgerFeedContainer) return;

    let url = `/api/expenses?month=${state.currentMonth}`;
    if (state.selectedDate) {
      url += `&date=${state.selectedDate}`;
    }
    if (state.activeCategory && state.activeCategory !== 'all') {
      url += `&category=${encodeURIComponent(state.activeCategory)}`;
    }
    if (state.searchQuery) {
      url += `&search=${encodeURIComponent(state.searchQuery)}`;
    }

    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch expenses');
      const data = await res.json();
      const expenses = data.expenses || [];

      // Update counter badge
      dom.ledgerCountBadge.textContent = `${expenses.length} transaction${expenses.length === 1 ? '' : 's'}`;

      if (expenses.length === 0) {
        dom.ledgerFeedContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="2" y="5" width="20" height="14" rx="2"/>
                <line x1="2" y1="10" x2="22" y2="10"/>
              </svg>
            </div>
            <div>No transactions found</div>
            <div style="font-size: 11px; margin-top: 4px; color: var(--text-subtle);">
              ${state.selectedDate ? 'No spend recorded on selected date.' : 'Log an expense or use voice dictation to get started.'}
            </div>
          </div>
        `;
        return;
      }

      // Group expenses by Date
      const groups = {};
      for (const exp of expenses) {
        if (!groups[exp.date]) {
          groups[exp.date] = [];
        }
        groups[exp.date].push(exp);
      }

      const todayStr = new Date().toISOString().split('T')[0];
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yesterdayStr = yesterday.toISOString().split('T')[0];

      let html = '';
      const sortedDates = Object.keys(groups).sort().reverse();

      for (const dateStr of sortedDates) {
        const items = groups[dateStr];
        const dayTotal = items.reduce((acc, cur) => acc + cur.amount, 0);

        let dateLabel = dateStr;
        if (dateStr === todayStr) {
          dateLabel = 'Today · ' + formatDateLabel(dateStr);
        } else if (dateStr === yesterdayStr) {
          dateLabel = 'Yesterday · ' + formatDateLabel(dateStr);
        } else {
          dateLabel = formatDateLabel(dateStr);
        }

        html += `
          <div class="ledger-date-group">
            <div class="ledger-date-header">
              <span>${dateLabel}</span>
              <span class="date-group-total">${formatCurrency(dayTotal)}</span>
            </div>
        `;

        for (const exp of items) {
          const badgeClass = `badge-${exp.bucket || 'lifestyle'}`;
          html += `
            <div class="ledger-row" id="row-${exp.id}">
              <span class="badge-cat ${badgeClass}">${escapeHtml(exp.category)}</span>
              <div class="ledger-item-info">
                <span class="item-name" title="${escapeHtml(exp.item)}">${escapeHtml(exp.item)}</span>
                ${exp.notes ? `<span class="item-notes" title="${escapeHtml(exp.notes)}">${escapeHtml(exp.notes)}</span>` : ''}
              </div>
              <span class="badge-mode">${escapeHtml(exp.payment_mode || 'UPI')}</span>
              <span class="ledger-amount">${formatCurrency(exp.amount)}</span>
              <button class="delete-row-btn" data-id="${exp.id}" title="Delete expense" aria-label="Delete ${escapeHtml(exp.item)}">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          `;
        }

        html += `</div>`;
      }

      dom.ledgerFeedContainer.innerHTML = html;

      // Attach Delete Handlers
      dom.ledgerFeedContainer.querySelectorAll('.delete-row-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const expenseId = btn.dataset.id;
          handleDeleteExpense(expenseId);
        });
      });

    } catch (err) {
      console.error('Error rendering ledger:', err);
      dom.ledgerFeedContainer.innerHTML = `<div class="empty-state">Failed to load transactions</div>`;
    }
  }

  function formatDateLabel(dateStr) {
    const parts = dateStr.split('-');
    const d = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
    return d.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
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

  async function handleDeleteExpense(expenseId) {
    if (!confirm('Delete this transaction?')) return;

    try {
      const res = await fetch(`/api/expenses/${expenseId}`, { method: 'DELETE' });
      if (res.ok) {
        showToast('Transaction deleted', 'success');
        // Refresh all data
        await loadAllData();
      } else {
        showToast('Failed to delete transaction', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Network error while deleting', 'error');
    }
  }

  // ==========================================
  // COMPACT EXPENSE FORM SUBMISSION
  // ==========================================
  async function handleExpenseFormSubmit(e) {
    e.preventDefault();

    const payload = {
      date: dom.expDate.value,
      category: dom.expCategory.value,
      item: dom.expItem.value.trim(),
      amount: parseFloat(dom.expAmount.value) || 0,
      payment_mode: dom.expPaymentMode.value,
      notes: dom.expNotes.value.trim()
    };

    if (!payload.item) {
      showToast('Please enter item or merchant name', 'error');
      dom.expItem.focus();
      return;
    }

    if (payload.amount <= 0) {
      showToast('Amount must be greater than zero', 'error');
      dom.expAmount.focus();
      return;
    }

    try {
      const res = await fetch('/api/expenses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        showToast(`Logged ₹${payload.amount.toFixed(2)} for ${payload.item}`, 'success');
        
        // Reset form inputs (preserve date)
        dom.expItem.value = '';
        dom.expAmount.value = '';
        dom.expNotes.value = '';
        dom.expItem.focus();

        // Refresh entire tracker state
        await loadAllData();
      } else {
        const errJson = await res.json();
        showToast(errJson.message || 'Error recording outflow', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to connect to backend', 'error');
    }
  }

  // ==========================================
  // TANGLISH VOICE RECOGNITION (Web Speech API)
  // ==========================================
  function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('SpeechRecognition API not available in this browser.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-IN'; // Highly tuned for Tanglish accents

      recognition.onstart = () => {
        state.isListening = true;
        updateVoiceUI(true);
      };

      recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        if (dom.voiceTranscriptText) {
          dom.voiceTranscriptText.textContent = `"${transcript}"`;
        }

        // Final result received
        if (event.results[0].isFinal) {
          processVoiceTranscript(transcript);
        }
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        state.isListening = false;
        updateVoiceUI(false);
        showToast(`Voice error: ${event.error}`, 'warning');
      };

      recognition.onend = () => {
        state.isListening = false;
        updateVoiceUI(false);
      };

      state.speechRecognition = recognition;
    } catch (err) {
      console.warn('Could not initialize SpeechRecognition:', err);
    }
  }

  function toggleVoiceRecognition() {
    if (!state.speechRecognition) {
      // Simulate/mock prompt for environments without native audio hardware
      const simulatedVoice = prompt(
        "Tanglish Voice Input Simulation:\nEnter your expense spoken phrase (e.g., 'Iniku petrol 300 rupees bike UPI' or 'Food swiggy 450 card'):",
        "Petrol 300 rupees bike UPI"
      );
      if (simulatedVoice) {
        processVoiceTranscript(simulatedVoice);
      }
      return;
    }

    if (state.isListening) {
      state.speechRecognition.stop();
      state.isListening = false;
      updateVoiceUI(false);
    } else {
      try {
        state.speechRecognition.start();
      } catch (e) {
        state.speechRecognition.stop();
      }
    }
  }

  function updateVoiceUI(isListening) {
    if (dom.voiceToggleBtn) {
      dom.voiceToggleBtn.classList.toggle('is-active', isListening);
    }
    if (dom.voiceTickerBanner) {
      dom.voiceTickerBanner.style.display = isListening ? 'flex' : 'none';
    }
  }

  async function processVoiceTranscript(transcript) {
    try {
      showToast('Processing Tanglish voice command...', 'normal');
      const res = await fetch('/api/voice-parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript })
      });

      if (!res.ok) throw new Error('Voice parsing failed');
      const data = await res.json();
      const parsed = data.parsed;

      // Populate form fields
      if (dom.expDate && parsed.date) dom.expDate.value = parsed.date;
      if (dom.expCategory && parsed.category) dom.expCategory.value = parsed.category;
      if (dom.expItem && parsed.item) dom.expItem.value = parsed.item;
      if (dom.expAmount && parsed.amount) dom.expAmount.value = parsed.amount;
      if (dom.expPaymentMode && parsed.payment_mode) dom.expPaymentMode.value = parsed.payment_mode;
      if (dom.expNotes && parsed.notes) dom.expNotes.value = parsed.notes;

      // Highlight form visually
      if (dom.expenseForm) {
        dom.expenseForm.style.transition = 'box-shadow 300ms ease';
        dom.expenseForm.style.boxShadow = '0 0 12px rgba(99, 102, 241, 0.4)';
        setTimeout(() => { dom.expenseForm.style.boxShadow = ''; }, 1200);
      }

      showToast(`Extracted: ${parsed.item} (₹${parsed.amount}) · [${parsed.category}]`, 'success');
      dom.expAmount.focus();

    } catch (err) {
      console.error(err);
      showToast('Could not parse voice command', 'error');
    }
  }

  // ==========================================
  // EMAIL REPORT DISPATCH
  // ==========================================
  async function handleEmailReport() {
    const targetEmail = 'sarveshsantosh2007s@gmail.com';
    const ok = confirm(`Dispatch monthly financial statement (${state.currentMonth}) to ${targetEmail}?`);
    if (!ok) return;

    showToast(`Compiling and dispatching report to ${targetEmail}...`, 'normal');
    try {
      const res = await fetch(`/api/email-report?month=${state.currentMonth}`, { method: 'POST' });
      if (res.ok) {
        const json = await res.json();
        showToast(`Report successfully dispatched to ${targetEmail}`, 'success');
      } else {
        showToast('Error sending email report', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Network error while dispatching email', 'error');
    }
  }

  // ==========================================
  // SALARY & BUDGET ALLOCATION SETTINGS MODAL
  // ==========================================
  function openSalaryModal() {
    if (!dom.salaryModal) return;
    const cfg = state.budgetConfig || {};
    const income = cfg.monthly_income || 20000;
    dom.modalSalaryInput.value = income;
    dom.modalEmergencyAccumulated.value = cfg.emergency_fund_accumulated || 36000;
    updateModalPreviews(income);
    dom.salaryModal.style.display = 'flex';
    dom.modalSalaryInput.focus();
  }

  function closeSalaryModal() {
    if (dom.salaryModal) dom.salaryModal.style.display = 'none';
  }

  function updateModalPreviews(incomeVal) {
    const inc = parseFloat(incomeVal) || 0;
    dom.prevNeedsTarget.textContent = formatCurrency(inc * 0.50);
    dom.prevLifeTarget.textContent = formatCurrency(inc * 0.20);
    dom.prevInvTarget.textContent = formatCurrency(inc * 0.20);
    dom.prevEmgTarget.textContent = formatCurrency(inc * 0.10);
  }

  async function handleSalaryFormSubmit(e) {
    e.preventDefault();
    const newIncome = parseFloat(dom.modalSalaryInput.value) || 20000;
    const accumulated = parseFloat(dom.modalEmergencyAccumulated.value) || 36000;

    try {
      const res = await fetch('/api/budget', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          monthly_income: newIncome,
          emergency_fund_accumulated: accumulated
        })
      });

      if (res.ok) {
        closeSalaryModal();
        showToast('50:20:20:10 Salary rules recalculated', 'success');
        await loadAllData();
      } else {
        showToast('Failed to update salary config', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Network error while updating salary', 'error');
    }
  }

  // ==========================================
  // EVENT LISTENERS BINDING
  // ==========================================
  function setupEventListeners() {
    // Month Stepper
    dom.prevMonthBtn.addEventListener('click', () => {
      shiftMonth(-1);
    });

    dom.nextMonthBtn.addEventListener('click', () => {
      shiftMonth(1);
    });

    dom.todayBtn.addEventListener('click', () => {
      state.currentMonth = getInitialMonth();
      state.selectedDate = null;
      loadAllData();
    });

    // Form
    dom.expenseForm.addEventListener('submit', handleExpenseFormSubmit);

    // Keyboard Shortcuts (Ctrl + Enter to submit form)
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        if (document.activeElement && dom.expenseForm.contains(document.activeElement)) {
          e.preventDefault();
          dom.expenseForm.requestSubmit();
        }
      }
      if (e.key === 'Escape') {
        closeSalaryModal();
        closeSettingsDropdown();
      }
    });

    // Voice triggers
    dom.voiceToggleBtn.addEventListener('click', toggleVoiceRecognition);
    dom.voiceFormBtn.addEventListener('click', toggleVoiceRecognition);
    dom.voiceStopBtn.addEventListener('click', () => {
      if (state.speechRecognition) state.speechRecognition.stop();
      state.isListening = false;
      updateVoiceUI(false);
    });

    // Email Report
    dom.emailReportBtn.addEventListener('click', handleEmailReport);

    // Clear calendar filter
    dom.calendarClearFilterBtn.addEventListener('click', () => {
      state.selectedDate = null;
      renderMiniCalendar();
      fetchAndRenderLedger();
    });

    // Ledger Search & Filters
    dom.ledgerSearchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value.trim();
      dom.clearSearchBtn.style.display = state.searchQuery ? 'block' : 'none';
      debounce(fetchAndRenderLedger, 250)();
    });

    dom.clearSearchBtn.addEventListener('click', () => {
      dom.ledgerSearchInput.value = '';
      state.searchQuery = '';
      dom.clearSearchBtn.style.display = 'none';
      fetchAndRenderLedger();
    });

    dom.ledgerCategoryFilter.addEventListener('change', (e) => {
      state.activeCategory = e.target.value;
      fetchAndRenderLedger();
    });

    // Settings Dropdown
    dom.settingsMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      dom.settingsDropdown.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (!dom.settingsDropdown.contains(e.target) && e.target !== dom.settingsMenuBtn) {
        closeSettingsDropdown();
      }
    });

    // Salary Modal Triggers
    dom.openSalaryModalBtn.addEventListener('click', () => {
      closeSettingsDropdown();
      openSalaryModal();
    });

    dom.editIncomeQuickBtn.addEventListener('click', openSalaryModal);
    dom.closeSalaryModalBtn.addEventListener('click', closeSalaryModal);
    dom.cancelSalaryModalBtn.addEventListener('click', closeSalaryModal);
    dom.salaryConfigForm.addEventListener('submit', handleSalaryFormSubmit);

    dom.modalSalaryInput.addEventListener('input', (e) => {
      updateModalPreviews(e.target.value);
    });

    // Export CSV
    dom.exportCsvBtn.addEventListener('click', () => {
      closeSettingsDropdown();
      window.location.href = '/api/export';
    });

    // Reset System Data
    dom.resetSystemBtn.addEventListener('click', async () => {
      closeSettingsDropdown();
      if (!confirm('Warning: This will reset budget rules to default and clear transaction records. Proceed?')) {
        return;
      }
      try {
        const res = await fetch('/api/reset', { method: 'POST' });
        if (res.ok) {
          showToast('System reset to default', 'warning');
          await loadAllData();
        }
      } catch (err) {
        console.error(err);
      }
    });
  }

  function closeSettingsDropdown() {
    if (dom.settingsDropdown) dom.settingsDropdown.classList.remove('show');
  }

  function shiftMonth(delta) {
    const [year, month] = state.currentMonth.split('-').map(Number);
    const date = new Date(year, month - 1 + delta, 1);
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    state.currentMonth = `${y}-${m}`;
    state.selectedDate = null; // Reset single day selection
    loadAllData();
  }

  // ==========================================
  // TOAST NOTIFICATIONS
  // ==========================================
  function showToast(message, type = 'normal') {
    if (!dom.toastStack) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    dom.toastStack.appendChild(toast);

    setTimeout(() => {
      toast.style.transition = 'opacity 200ms ease, transform 200ms ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 200);
    }, 3200);
  }

  // Debounce helper
  function debounce(func, wait) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    };
  }

})();
