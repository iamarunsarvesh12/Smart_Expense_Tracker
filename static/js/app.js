/**
 * Smart Home Expense Tracker - Client-side Application Logic
 * Phase 4.5: 7-Category Architecture, Budget Planner, Remaining Balances,
 * Net Savings Engine, and Interactive Analytics.
 */

// Application State
const state = {
    currentYear: new Date().getFullYear(),
    currentMonth: new Date().getMonth() + 1, // 1-12
    selectedDate: formatDate(new Date()),
    selectedCategory: null, // Active category filter
    monthlyData: null,
    budgetConfig: null,
    trendChart: null,
    rankingChart: null,
    isRecording: false,
    recognition: null,
    lastTranscript: ""
};

// 7 Granular Category Configuration & Theme Accents
const CATEGORY_CONFIG = {
    "Food": {
        icon: "fa-solid fa-utensils",
        bg: "bg-amber-100",
        text: "text-amber-700",
        border: "border-amber-200",
        color: "#f59e0b"
    },
    "Groceries": {
        icon: "fa-solid fa-basket-shopping",
        bg: "bg-emerald-100",
        text: "text-emerald-700",
        border: "border-emerald-200",
        color: "#10b981"
    },
    "Bike & Car": {
        icon: "fa-solid fa-motorcycle",
        bg: "bg-blue-100",
        text: "text-blue-700",
        border: "border-blue-200",
        color: "#3b82f6"
    },
    "Bills & Utilities": {
        icon: "fa-solid fa-bolt",
        bg: "bg-purple-100",
        text: "text-purple-700",
        border: "border-purple-200",
        color: "#8b5cf6"
    },
    "Stationery & Office": {
        icon: "fa-solid fa-pen-ruler",
        bg: "bg-cyan-100",
        text: "text-cyan-700",
        border: "border-cyan-200",
        color: "#06b6d4"
    },
    "Medical & Healthcare": {
        icon: "fa-solid fa-heart-pulse",
        bg: "bg-rose-100",
        text: "text-rose-700",
        border: "border-rose-200",
        color: "#f43f5e"
    },
    "General & Others": {
        icon: "fa-solid fa-coins",
        bg: "bg-slate-100",
        text: "text-slate-700",
        border: "border-slate-200",
        color: "#64748b"
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

    // Budget Planner Modal Triggers
    const budgetModal = document.getElementById('modal-budget-settings');
    document.getElementById('btn-open-budget-modal').addEventListener('click', openBudgetModal);
    document.getElementById('btn-close-budget-modal').addEventListener('click', closeBudgetModal);
    document.getElementById('btn-cancel-budget-modal').addEventListener('click', closeBudgetModal);
    document.getElementById('form-budget-settings').addEventListener('submit', handleBudgetSubmit);
    initBudgetLiveCalculator();

    // Manual Modal Triggers
    const addModal = document.getElementById('modal-add-expense');
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

    // Clear Category Filter
    document.getElementById('btn-clear-category-filter').addEventListener('click', clearCategoryFilter);

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
            closeBudgetModal();
            cancelVoiceRecognition();
        }
    });
    addModal.addEventListener('click', (e) => {
        if (e.target === addModal) closeAddModal();
    });
    confirmModal.addEventListener('click', (e) => {
        if (e.target === confirmModal) closeVoiceConfirmModal();
    });
    budgetModal.addEventListener('click', (e) => {
        if (e.target === budgetModal) closeBudgetModal();
    });
}

// =============================================================================
// Core Dashboard Data Orchestrator
// =============================================================================

async function loadDashboardData() {
    await Promise.all([
        fetchMonthlySummary(state.currentYear, state.currentMonth),
        fetchTodayExpense(),
        fetchExpensesList()
    ]);
}

async function fetchMonthlySummary(year, month) {
    try {
        const response = await fetch(`/api/summary/monthly?year=${year}&month=${month}`);
        if (!response.ok) throw new Error('Failed to load monthly summary');
        const data = await response.json();
        state.monthlyData = data;

        // Header & Calendar labels
        updateMonthBadge(data.month_label);
        document.getElementById('calendar-title').textContent = data.month_label;

        // 1. Top Stat Cards
        renderTopStatCards(data);

        // 2. Category Highlights & Remaining Balances
        renderCategoryCards(data.category_budgets);

        // 3. Calendar Grid
        renderCalendar(year, month, data.daily_totals);

        // 4. Analytics Visualizations (Burn rate & Category ranking)
        renderAnalyticsCharts(data);
    } catch (error) {
        console.error('Error fetching monthly summary:', error);
        showToast('Error loading monthly summary', 'error');
    }
}

async function fetchTodayExpense() {
    try {
        const todayStr = formatDate(new Date());
        const response = await fetch(`/api/expenses?date=${todayStr}`);
        if (!response.ok) return;
        const data = await response.json();
        document.getElementById('stat-today-total').textContent = formatCurrency(data.daily_total);
    } catch (error) {
        console.error('Error fetching today expense:', error);
    }
}

async function fetchExpensesList() {
    const titleEl = document.getElementById('selected-date-title');
    const totalEl = document.getElementById('selected-date-total');
    const countEl = document.getElementById('selected-date-count');
    const listContainer = document.getElementById('daily-expenses-list');
    const emptyState = document.getElementById('daily-empty-state');
    const filterBadge = document.getElementById('category-filter-badge');
    const filterName = document.getElementById('category-filter-name');
    const clearBtn = document.getElementById('btn-clear-category-filter');
    const panelBadgeTitle = document.getElementById('panel-badge-title');

    // UI Title & Filter State
    if (state.selectedCategory) {
        panelBadgeTitle.textContent = "Filtered by Category";
        filterBadge.classList.remove('hidden');
        filterName.textContent = state.selectedCategory;
        clearBtn.classList.remove('hidden');
        titleEl.textContent = `${state.selectedCategory} Expenses`;
    } else {
        panelBadgeTitle.textContent = "Selected Date";
        filterBadge.classList.add('hidden');
        clearBtn.classList.add('hidden');
        const dateObj = new Date(state.selectedDate + "T00:00:00");
        titleEl.textContent = dateObj.toLocaleDateString('default', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' });
    }

    listContainer.innerHTML = `
        <div class="py-8 text-center text-slate-400">
            <i class="fa-solid fa-circle-notch fa-spin text-xl text-brand-600 mb-2"></i>
            <p class="text-xs">Loading expenses...</p>
        </div>
    `;
    emptyState.classList.add('hidden');

    try {
        let url = '/api/expenses?';
        if (state.selectedCategory) {
            url += `category=${encodeURIComponent(state.selectedCategory)}`;
        } else {
            url += `date=${encodeURIComponent(state.selectedDate)}`;
        }

        const response = await fetch(url);
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
        console.error('Error loading expenses list:', error);
        listContainer.innerHTML = `<div class="p-4 text-xs text-rose-600 bg-rose-50 rounded-xl">Error loading expenses.</div>`;
    }
}

function clearCategoryFilter() {
    state.selectedCategory = null;
    document.querySelectorAll('.category-card').forEach(c => c.classList.remove('active-filter'));
    fetchExpensesList();
}

// =============================================================================
// Top Stat Cards & Budget Highlights Renderer
// =============================================================================

function renderTopStatCards(data) {
    // Card 1: Month Spend
    document.getElementById('stat-month-total').textContent = formatCurrency(data.total_spending);
    document.getElementById('stat-month-transactions').textContent = `${data.transaction_count} transaction${data.transaction_count === 1 ? '' : 's'}`;

    // Card 2: Income & Allocated Budget
    document.getElementById('stat-monthly-income').textContent = formatCurrency(data.monthly_income);
    document.getElementById('stat-budget-allocated').textContent = formatCurrency(data.total_budget_allocated);

    // Card 3: Net Savings & Savings Rate Meter
    const savingsEl = document.getElementById('stat-net-savings');
    const badgeEl = document.getElementById('stat-savings-rate-badge');
    const barEl = document.getElementById('stat-savings-bar');

    savingsEl.textContent = formatCurrency(data.net_savings);

    if (data.net_savings >= 0) {
        savingsEl.className = 'text-2xl font-extrabold text-emerald-600 tracking-tight';
        badgeEl.className = 'text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800';
        badgeEl.textContent = `${data.savings_rate}% Saved`;
        barEl.className = 'bg-emerald-500 h-full rounded-full transition-all duration-500';
        barEl.style.width = `${Math.min(Math.max(data.savings_rate, 0), 100)}%`;
    } else {
        savingsEl.className = 'text-2xl font-extrabold text-rose-600 tracking-tight';
        badgeEl.className = 'text-[11px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800';
        badgeEl.textContent = `Deficit!`;
        barEl.className = 'bg-rose-500 h-full rounded-full transition-all duration-500';
        barEl.style.width = '100%';
    }

    // Card 4: Daily Burn Rate vs Target
    document.getElementById('stat-daily-target').textContent = `${formatCurrency(data.daily_budget_target)} / day`;
    const burnBadge = document.getElementById('stat-daily-status-badge');
    const todayTotal = parseFloat(document.getElementById('stat-today-total').textContent.replace(/[^\d.-]/g, '')) || 0.0;

    if (todayTotal <= data.daily_budget_target) {
        burnBadge.className = 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800';
        burnBadge.textContent = 'Within Target';
    } else {
        burnBadge.className = 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800';
        burnBadge.textContent = 'High Burn';
    }
}

function renderCategoryCards(categoryBudgets) {
    const container = document.getElementById('category-cards-container');
    if (!container || !categoryBudgets) return;

    container.innerHTML = '';

    Object.keys(CATEGORY_CONFIG).forEach(cat => {
        const cfg = CATEGORY_CONFIG[cat];
        const budgetInfo = categoryBudgets[cat] || {
            spent: 0.0,
            allocated: 0.0,
            remaining: 0.0,
            pct_used: 0.0,
            is_over: false
        };

        const isOver = budgetInfo.is_over;
        const pctUsed = Math.min(budgetInfo.pct_used, 100);
        const isActive = (state.selectedCategory === cat);

        // Progress bar color based on percentage used
        let barColor = 'bg-emerald-500';
        if (pctUsed >= 90 || isOver) {
            barColor = 'bg-rose-500';
        } else if (pctUsed >= 75) {
            barColor = 'bg-amber-500';
        }

        const card = document.createElement('div');
        card.className = `category-card bg-white rounded-xl border p-3.5 shadow-sm transition-all ${
            isActive ? 'active-filter' : 'border-slate-200/90'
        }`;
        card.id = `cat-card-${cat}`;

        card.innerHTML = `
            <div class="flex items-center space-x-2.5 mb-2">
                <div class="h-8 w-8 rounded-lg ${cfg.bg} ${cfg.text} flex items-center justify-center text-xs shadow-sm flex-shrink-0">
                    <i class="${cfg.icon}"></i>
                </div>
                <div class="truncate">
                    <h4 class="text-xs font-bold text-slate-800 truncate">${escapeHtml(cat)}</h4>
                    <span class="text-[10px] text-slate-400 block">Bud: ${formatCurrencyCompact(budgetInfo.allocated)}</span>
                </div>
            </div>

            <!-- Spent Amount -->
            <div class="flex items-baseline justify-between mt-1">
                <span class="text-base font-extrabold text-slate-900">${formatCurrency(budgetInfo.spent)}</span>
                <span class="text-[10px] font-bold ${isOver ? 'text-rose-600' : 'text-slate-500'}">
                    ${isOver ? `-${formatCurrencyCompact(Math.abs(budgetInfo.remaining))} over` : `${formatCurrencyCompact(budgetInfo.remaining)} left`}
                </span>
            </div>

            <!-- Progress Bar -->
            <div class="w-full bg-slate-100 h-1.5 rounded-full mt-2 overflow-hidden">
                <div class="${barColor} h-full rounded-full transition-all duration-500" style="width: ${pctUsed}%"></div>
            </div>

            <div class="flex items-center justify-between text-[10px] text-slate-400 mt-1">
                <span>${budgetInfo.pct_used.toFixed(0)}% used</span>
                <span class="text-[9px] hover:text-brand-600 font-medium">Filter &rarr;</span>
            </div>
        `;

        card.addEventListener('click', () => {
            if (state.selectedCategory === cat) {
                clearCategoryFilter();
            } else {
                state.selectedCategory = cat;
                document.querySelectorAll('.category-card').forEach(c => c.classList.remove('active-filter'));
                card.classList.add('active-filter');
                fetchExpensesList();
            }
        });

        container.appendChild(card);
    });
}

// =============================================================================
// Enhanced Analytics Visualizations (Chart.js)
// =============================================================================

function renderAnalyticsCharts(data) {
    renderDailyTrendChart(data.daily_totals, data.days_in_month, data.daily_budget_target, data.month_label);
    renderCategoryRankingChart(data.category_breakdown);
}

function renderDailyTrendChart(dailyTotals, daysInMonth, dailyTarget, monthLabel) {
    const ctx = document.getElementById('chart-daily-bars');
    if (!ctx) return;

    const dailyMap = {};
    if (Array.isArray(dailyTotals)) {
        dailyTotals.forEach(item => {
            const dayNum = parseInt(item.date.split('-')[2], 10);
            dailyMap[dayNum] = item.total;
        });
    }

    const labels = [];
    const spendValues = [];
    const targetValues = [];

    for (let day = 1; day <= daysInMonth; day++) {
        labels.push(day);
        spendValues.push(dailyMap[day] || 0.0);
        targetValues.push(dailyTarget);
    }

    if (state.trendChart) {
        state.trendChart.destroy();
    }

    state.trendChart = new Chart(ctx, {
        data: {
            labels: labels,
            datasets: [
                {
                    type: 'bar',
                    label: 'Spent (₹)',
                    data: spendValues,
                    backgroundColor: '#6366f1',
                    borderRadius: 4,
                    hoverBackgroundColor: '#4f46e5',
                    order: 2
                },
                {
                    type: 'line',
                    label: 'Target Burn Rate',
                    data: targetValues,
                    borderColor: '#f43f5e',
                    borderWidth: 2,
                    borderDash: [5, 4],
                    pointRadius: 0,
                    fill: false,
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => `Day ${items[0].label} (${monthLabel})`,
                        label: (item) => {
                            if (item.dataset.type === 'line') {
                                return ` Target Rate: ₹${item.parsed.y.toFixed(2)}`;
                            }
                            return ` Actual Spent: ₹${item.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 9 }, maxTicksLimit: 16 }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        font: { size: 9 },
                        callback: (v) => '₹' + v
                    }
                }
            }
        }
    });
}

function renderCategoryRankingChart(categoryBreakdown) {
    const ctx = document.getElementById('chart-category-ranking');
    if (!ctx || !categoryBreakdown) return;

    // Sort categories descending by spend amount
    const sorted = Object.keys(categoryBreakdown)
        .map(cat => ({
            category: cat,
            amount: categoryBreakdown[cat] || 0.0,
            color: CATEGORY_CONFIG[cat] ? CATEGORY_CONFIG[cat].color : '#6366f1'
        }))
        .sort((a, b) => b.amount - a.amount);

    const labels = sorted.map(s => s.category);
    const amounts = sorted.map(s => s.amount);
    const colors = sorted.map(s => s.color);

    if (state.rankingChart) {
        state.rankingChart.destroy();
    }

    state.rankingChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Spend (₹)',
                data: amounts,
                backgroundColor: colors,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y', // Horizontal bars for clean reading
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (item) => ` Total: ₹${item.parsed.x.toFixed(2)}`
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    ticks: { font: { size: 9 }, callback: (v) => '₹' + v }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { size: 10, weight: 'bold' } }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const idx = elements[0].index;
                    const clickedCategory = labels[idx];

                    state.selectedCategory = clickedCategory;
                    document.querySelectorAll('.category-card').forEach(c => c.classList.remove('active-filter'));
                    const matchingCard = document.getElementById(`cat-card-${clickedCategory}`);
                    if (matchingCard) matchingCard.classList.add('active-filter');

                    fetchExpensesList();
                    showToast(`Filtered by ${clickedCategory}`, 'info');
                }
            }
        }
    });
}

// =============================================================================
// Monthly Budget Settings Planner Handlers
// =============================================================================

async function openBudgetModal() {
    const modal = document.getElementById('modal-budget-settings');
    modal.classList.remove('hidden');

    try {
        const response = await fetch('/api/budget');
        if (!response.ok) throw new Error('Failed to load budget');
        const data = await response.json();
        const budget = data.budget;

        document.getElementById('budget-input-income').value = budget.monthly_income;

        const cats = budget.categories || {};
        document.getElementById('budget-cat-Food').value = cats["Food"] || 0;
        document.getElementById('budget-cat-Groceries').value = cats["Groceries"] || 0;
        document.getElementById('budget-cat-Bike-Car').value = cats["Bike & Car"] || 0;
        document.getElementById('budget-cat-Bills-Utilities').value = cats["Bills & Utilities"] || 0;
        document.getElementById('budget-cat-Stationery-Office').value = cats["Stationery & Office"] || 0;
        document.getElementById('budget-cat-Medical-Healthcare').value = cats["Medical & Healthcare"] || 0;
        document.getElementById('budget-cat-General-Others').value = cats["General & Others"] || 0;

        recalculateBudgetSummary();
    } catch (e) {
        console.error('Error opening budget modal:', e);
    }
}

function closeBudgetModal() {
    document.getElementById('modal-budget-settings').classList.add('hidden');
}

function initBudgetLiveCalculator() {
    const inputs = [
        'budget-input-income',
        'budget-cat-Food',
        'budget-cat-Groceries',
        'budget-cat-Bike-Car',
        'budget-cat-Bills-Utilities',
        'budget-cat-Stationery-Office',
        'budget-cat-Medical-Healthcare',
        'budget-cat-General-Others'
    ];

    inputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', recalculateBudgetSummary);
    });
}

function recalculateBudgetSummary() {
    const income = parseFloat(document.getElementById('budget-input-income').value) || 0.0;
    const catSum = [
        'budget-cat-Food',
        'budget-cat-Groceries',
        'budget-cat-Bike-Car',
        'budget-cat-Bills-Utilities',
        'budget-cat-Stationery-Office',
        'budget-cat-Medical-Healthcare',
        'budget-cat-General-Others'
    ].reduce((acc, id) => {
        return acc + (parseFloat(document.getElementById(id).value) || 0.0);
    }, 0.0);

    const buffer = income - catSum;

    document.getElementById('budget-calc-total-allocated').textContent = formatCurrency(catSum);
    const bufferEl = document.getElementById('budget-calc-savings-buffer');
    bufferEl.textContent = formatCurrency(buffer);

    if (buffer >= 0) {
        bufferEl.className = 'font-bold text-emerald-600';
    } else {
        bufferEl.className = 'font-bold text-rose-600';
    }
}

async function handleBudgetSubmit(e) {
    e.preventDefault();

    const submitBtn = document.getElementById('btn-save-budget-settings');
    const originalText = submitBtn.innerHTML;

    const payload = {
        monthly_income: parseFloat(document.getElementById('budget-input-income').value),
        categories: {
            "Food": parseFloat(document.getElementById('budget-cat-Food').value) || 0.0,
            "Groceries": parseFloat(document.getElementById('budget-cat-Groceries').value) || 0.0,
            "Bike & Car": parseFloat(document.getElementById('budget-cat-Bike-Car').value) || 0.0,
            "Bills & Utilities": parseFloat(document.getElementById('budget-cat-Bills-Utilities').value) || 0.0,
            "Stationery & Office": parseFloat(document.getElementById('budget-cat-Stationery-Office').value) || 0.0,
            "Medical & Healthcare": parseFloat(document.getElementById('budget-cat-Medical-Healthcare').value) || 0.0,
            "General & Others": parseFloat(document.getElementById('budget-cat-General-Others').value) || 0.0
        }
    };

    try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Saving...</span>`;

        const response = await fetch('/api/budget', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.message || 'Failed to update budget settings');
        }

        playSuccessChime();
        showToast('Monthly budget & income updated successfully!', 'success');
        closeBudgetModal();

        await loadDashboardData();
    } catch (err) {
        console.error('Budget save error:', err);
        showToast(err.message || 'Error updating budget', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
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
        recognition.lang = 'en-IN';

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

    document.getElementById('voice-original-text').textContent = `"${rawTranscript}"`;
    document.getElementById('voice-input-date').value = extractedData.date || formatDate(new Date());
    document.getElementById('voice-input-time').value = (extractedData.time || new Date().toTimeString()).slice(0, 5);
    document.getElementById('voice-input-category').value = extractedData.category || "Food";
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

        playSuccessChime();
        showToast(`Voice expense recorded: ${payload.item} (₹${payload.amount})`, 'success');
        closeVoiceConfirmModal();

        state.selectedDate = payload.date;
        state.selectedCategory = null;
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
// Web Audio API Synthesized Chime
// =============================================================================

function playSuccessChime() {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;

        const ctx = new AudioCtx();
        const now = ctx.currentTime;

        const osc1 = ctx.createOscillator();
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
        // Fallback
    }
}

// =============================================================================
// Interactive Calendar Component
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
        const isSelected = (dateStr === state.selectedDate && !state.selectedCategory);

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
            state.selectedDate = dateStr;
            state.selectedCategory = null;
            document.querySelectorAll('.calendar-tile').forEach(t => t.classList.remove('selected'));
            document.querySelectorAll('.category-card').forEach(c => c.classList.remove('active-filter'));
            tile.classList.add('selected');
            fetchExpensesList();
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
    state.selectedCategory = null;
    fetchMonthlySummary(state.currentYear, state.currentMonth);
    fetchExpensesList();
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
                    <span>${escapeHtml(exp.date)}</span>
                    ${exp.time ? `<span><i class="fa-regular fa-clock mr-0.5"></i>${escapeHtml(exp.time.slice(0, 5))}</span>` : ''}
                </div>
                ${exp.notes ? `<span class="italic text-slate-500 max-w-[120px] truncate" title="${escapeHtml(exp.notes)}">${escapeHtml(exp.notes)}</span>` : ''}
            </div>
        </div>
    `;
}

function updateMonthBadge(label) {
    const badge = document.getElementById('current-month-badge');
    if (badge) badge.textContent = label;
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

    if (state.selectedCategory) {
        document.getElementById('input-category').value = state.selectedCategory;
    }

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

        state.selectedDate = payload.date;
        state.selectedCategory = null;
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
