/**
 * Smart Home Expense Tracker - Frontend Engine
 * Features:
 * - 7-Category Budgeting & Savings Tracker (Allocated, Spent, Remaining)
 * - Strict Date-Only Expense Management (No time field)
 * - Month-End Email Report Dispatch to sarveshsantosh2007s@gmail.com
 * - Password-Protected Database Reset
 * - Chart.js Spending Analytics (Daily Burn Rate & Category Ranking)
 * - Interactive Monthly Calendar
 * - Browser-Native Web Speech API with Tanglish & English Extraction
 */

// Global Configuration for the 7 Granular Expense Buckets
const CATEGORY_CONFIG = {
    "Food": {
        color: "#f59e0b",
        bgClass: "bg-amber-500",
        lightBgClass: "bg-amber-50",
        borderClass: "border-amber-200",
        textColor: "text-amber-700",
        icon: "fa-utensils",
        desc: "Restaurant, Tea, Swiggy"
    },
    "Groceries": {
        color: "#10b981",
        bgClass: "bg-emerald-500",
        lightBgClass: "bg-emerald-50",
        borderClass: "border-emerald-200",
        textColor: "text-emerald-700",
        icon: "fa-basket-shopping",
        desc: "Provisions, Veggies, Milk"
    },
    "Bike & Car": {
        color: "#3b82f6",
        bgClass: "bg-blue-500",
        lightBgClass: "bg-blue-50",
        borderClass: "border-blue-200",
        textColor: "text-blue-700",
        icon: "fa-motorcycle",
        desc: "Petrol, Service, Puncture"
    },
    "Bills & Utilities": {
        color: "#8b5cf6",
        bgClass: "bg-purple-500",
        lightBgClass: "bg-purple-50",
        borderClass: "border-purple-200",
        textColor: "text-purple-700",
        icon: "fa-bolt",
        desc: "EB Bill, Wi-Fi, Recharge"
    },
    "Stationery & Office": {
        color: "#06b6d4",
        bgClass: "bg-cyan-500",
        lightBgClass: "bg-cyan-50",
        borderClass: "border-cyan-200",
        textColor: "text-cyan-700",
        icon: "fa-print",
        desc: "Printout, Xerox, Books"
    },
    "Medical & Healthcare": {
        color: "#ef4444",
        bgClass: "bg-rose-500",
        lightBgClass: "bg-rose-50",
        borderClass: "border-rose-200",
        textColor: "text-rose-700",
        icon: "fa-heart-pulse",
        desc: "Medicines, Consultation"
    },
    "General & Others": {
        color: "#64748b",
        bgClass: "bg-slate-500",
        lightBgClass: "bg-slate-50",
        borderClass: "border-slate-200",
        textColor: "text-slate-700",
        icon: "fa-coins",
        desc: "Lending, Cash, Misc"
    }
};

const MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
];

// Application State
const state = {
    currentYear: new Date().getFullYear(),
    currentMonth: new Date().getMonth() + 1,
    selectedDate: new Date().toISOString().split("T")[0],
    categoryFilter: null,
    monthlySummary: null,
    budgetConfig: null,
    chartDaily: null,
    chartCategoryRanking: null,
    speechRecognition: null,
    isListening: false,
    audioCtx: null
};

// Utilities
const formatCurrency = (amount) => "₹" + Number(amount || 0).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
});

const formatCompactCurrency = (amount) => {
    const val = Number(amount || 0);
    if (val >= 1000) return `₹${(val / 1000).toFixed(1)}k`;
    return `₹${Math.round(val)}`;
};

const formatDateReadable = (dateStr) => {
    if (!dateStr) return "";
    const [y, m, d] = dateStr.split("-").map(Number);
    const dObj = new Date(y, m - 1, d);
    return dObj.toLocaleDateString("en-IN", {
        weekday: "long",
        day: "numeric",
        month: "short",
        year: "numeric"
    });
};

function playAudioChime(freq = 600, duration = 0.15) {
    try {
        if (!state.audioCtx) {
            state.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (state.audioCtx.state === "suspended") {
            state.audioCtx.resume();
        }
        const osc = state.audioCtx.createOscillator();
        const gain = state.audioCtx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, state.audioCtx.currentTime);
        gain.gain.setValueAtTime(0.12, state.audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, state.audioCtx.currentTime + duration);
        osc.connect(gain);
        gain.connect(state.audioCtx.destination);
        osc.start();
        osc.stop(state.audioCtx.currentTime + duration);
    } catch (e) {
        // AudioContext fallback
    }
}

// ---------------------------------------------------------------------------
// Core Data Fetching
// ---------------------------------------------------------------------------

async function fetchMonthlySummary() {
    try {
        const res = await fetch(`/api/summary/monthly?year=${state.currentYear}&month=${state.currentMonth}`);
        const data = await res.json();
        if (data.status === "success") {
            state.monthlySummary = data;
            renderTopStatCards(data);
            renderCategoryBudgetCards(data.category_budgets || {});
            renderCalendar(data.daily_totals || []);
            renderEnhancedCharts(data);
        }
    } catch (err) {
        console.error("Error loading monthly summary:", err);
    }
}

async function fetchSelectedExpenses() {
    try {
        let url = `/api/expenses?`;
        if (state.categoryFilter) {
            url += `category=${encodeURIComponent(state.categoryFilter)}`;
        } else if (state.selectedDate) {
            url += `date=${encodeURIComponent(state.selectedDate)}`;
        }

        const res = await fetch(url);
        const data = await res.json();
        if (data.status === "success") {
            renderExpensesList(data.expenses || [], data.daily_total || 0, data.count || 0);
        }
    } catch (err) {
        console.error("Error fetching filtered expenses:", err);
    }
}

// ---------------------------------------------------------------------------
// Render Dashboard Cards & Progress Meters
// ---------------------------------------------------------------------------

function renderTopStatCards(summary) {
    const monthBadge = document.getElementById("current-month-badge");
    if (monthBadge) {
        monthBadge.textContent = `${MONTH_NAMES[state.currentMonth - 1].slice(0, 3)} ${state.currentYear}`;
    }

    // 1. Total Spend
    document.getElementById("stat-month-total").textContent = formatCurrency(summary.total_spending);
    document.getElementById("stat-month-transactions").textContent = `${summary.transaction_count} transactions`;

    // 2. Monthly Income & Allocation
    const income = summary.monthly_income || 0;
    document.getElementById("stat-monthly-income").textContent = formatCurrency(income);
    document.getElementById("stat-budget-allocated").textContent = formatCurrency(summary.total_budget_allocated || 0);

    // 3. Net Savings & Meter
    const netSavings = summary.net_savings ?? (income - summary.total_spending);
    const savingsEl = document.getElementById("stat-net-savings");
    savingsEl.textContent = formatCurrency(netSavings);

    const savingsRate = summary.savings_rate ?? (income > 0 ? (netSavings / income) * 100 : 0);
    const savingsRateBadge = document.getElementById("stat-savings-rate-badge");
    const savingsBar = document.getElementById("stat-savings-bar");

    if (netSavings >= 0) {
        savingsEl.className = "text-2xl font-bold tracking-tight text-emerald-600 tabular-nums";
        savingsRateBadge.className = "text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/80";
        savingsRateBadge.textContent = `${Math.max(0, savingsRate).toFixed(1)}% Saved`;
        savingsBar.className = "bg-emerald-500 h-full rounded-full transition-all duration-500";
        savingsBar.style.width = `${Math.min(100, Math.max(0, savingsRate))}%`;
    } else {
        savingsEl.className = "text-2xl font-bold tracking-tight text-rose-600 tabular-nums";
        savingsRateBadge.className = "text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200/80";
        savingsRateBadge.textContent = `Overspent by ${formatCurrency(Math.abs(netSavings))}`;
        savingsBar.className = "bg-rose-500 h-full rounded-full transition-all duration-500";
        savingsBar.style.width = "100%";
    }

    // 4. Daily Burn Rate vs Target
    const todayStr = new Date().toISOString().split("T")[0];
    const todayEntry = (summary.daily_totals || []).find(d => d.date === todayStr);
    const todaySpent = todayEntry ? todayEntry.total : 0;
    const dailyTarget = summary.daily_budget_target || (income / (summary.days_in_month || 30));

    document.getElementById("stat-today-total").textContent = formatCurrency(todaySpent);
    document.getElementById("stat-daily-target").textContent = `${formatCurrency(dailyTarget)} / day`;

    const dailyBadge = document.getElementById("stat-daily-status-badge");
    if (todaySpent > dailyTarget && dailyTarget > 0) {
        dailyBadge.className = "text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200";
        dailyBadge.textContent = "Over Target";
    } else {
        dailyBadge.className = "text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200";
        dailyBadge.textContent = "Within Target";
    }
}

function renderCategoryBudgetCards(categoryBudgets) {
    const container = document.getElementById("category-cards-container");
    container.innerHTML = "";

    const categories = Object.keys(CATEGORY_CONFIG);

    categories.forEach(catName => {
        const cfg = CATEGORY_CONFIG[catName];
        const data = categoryBudgets[catName] || { spent: 0, allocated: 0, remaining: 0, pct_used: 0, is_over: false };

        const card = document.createElement("div");
        const isActive = state.categoryFilter === catName;
        card.className = `category-card bg-white rounded-xl border p-3 shadow-2xs hover:shadow-xs transition-all cursor-pointer relative overflow-hidden ${
            isActive ? "border-neutral-900 ring-1 ring-neutral-900 bg-neutral-50/60" : "border-black/[0.07] hover:border-black/20"
        }`;

        let progressColor = "bg-neutral-900";
        let statusBadge = "";
        if (data.is_over) {
            progressColor = "bg-rose-500";
            statusBadge = `<span class="text-[9px] font-bold text-rose-600 uppercase tracking-wider">Over</span>`;
        } else if (data.pct_used >= 75) {
            progressColor = "bg-amber-500";
        }

        const cappedPct = Math.min(100, Math.max(0, data.pct_used));

        card.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <div class="h-6 w-6 rounded-md bg-neutral-100 text-neutral-700 flex items-center justify-center text-[11px]">
                    <i class="fa-solid ${cfg.icon}"></i>
                </div>
                ${statusBadge}
            </div>
            <div class="space-y-0.5">
                <h4 class="text-xs font-bold text-neutral-900 truncate tracking-tight">${catName}</h4>
                <div class="text-[11px] text-neutral-400 font-medium truncate tabular-nums">
                    Bud: ${formatCompactCurrency(data.allocated)}
                </div>
            </div>
            <div class="mt-2.5 flex items-baseline justify-between">
                <span class="text-sm font-bold text-neutral-950 tabular-nums">${formatCurrency(data.spent)}</span>
                <span class="text-[10px] tabular-nums ${data.remaining < 0 ? 'text-rose-600 font-semibold' : 'text-neutral-500'}">
                    ${data.remaining >= 0 ? `${formatCompactCurrency(data.remaining)} left` : `-${formatCompactCurrency(Math.abs(data.remaining))}`}
                </span>
            </div>
            <div class="w-full bg-neutral-100 h-1 rounded-full mt-2 overflow-hidden">
                <div class="${progressColor} h-full rounded-full transition-all duration-300" style="width: ${cappedPct}%"></div>
            </div>
            <div class="mt-1.5 flex items-center justify-between text-[10px] text-neutral-400">
                <span class="tabular-nums">${data.pct_used.toFixed(0)}% used</span>
                <span class="text-neutral-700 font-semibold hover:underline">${isActive ? 'Active' : 'Filter →'}</span>
            </div>
        `;

        card.addEventListener("click", () => {
            if (state.categoryFilter === catName) {
                clearCategoryFilter();
            } else {
                setCategoryFilter(catName);
            }
        });

        container.appendChild(card);
    });
}

// ---------------------------------------------------------------------------
// Enhanced Chart.js Spending Analytics
// ---------------------------------------------------------------------------

function renderEnhancedCharts(summary) {
    const dailyTotals = summary.daily_totals || [];
    const daysInMonth = summary.days_in_month || 31;
    const dailyBurnTarget = summary.daily_budget_target || 0;

    // 1. Interactive Daily Spend vs Recommended Burn Rate Line
    const dailyLabels = [];
    const dailyValues = [];
    const dailyTargetLine = [];

    const dateMap = {};
    dailyTotals.forEach(d => { dateMap[d.date] = d.total; });

    for (let day = 1; day <= daysInMonth; day++) {
        dailyLabels.push(day);
        const dayStr = `${state.currentYear}-${String(state.currentMonth).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
        dailyValues.push(dateMap[dayStr] || 0);
        dailyTargetLine.push(dailyBurnTarget);
    }

    const ctxDaily = document.getElementById("chart-daily-bars");
    if (ctxDaily) {
        if (state.chartDaily) state.chartDaily.destroy();

        state.chartDaily = new Chart(ctxDaily.getContext("2d"), {
            type: "bar",
            data: {
                labels: dailyLabels,
                datasets: [
                    {
                        label: "Daily Spend",
                        data: dailyValues,
                        backgroundColor: "#18181b",
                        hoverBackgroundColor: "#27272a",
                        borderRadius: 3,
                        barPercentage: 0.6,
                        order: 2
                    },
                    {
                        type: "line",
                        label: "Daily Target Burn Rate",
                        data: dailyTargetLine,
                        borderColor: "#e11d48",
                        borderWidth: 1.5,
                        borderDash: [3, 3],
                        pointRadius: 0,
                        fill: false,
                        order: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: "index", intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#18181b",
                        titleColor: "#ffffff",
                        bodyColor: "#f4f4f5",
                        borderColor: "rgba(255,255,255,0.1)",
                        borderWidth: 1,
                        padding: 8,
                        cornerRadius: 8,
                        titleFont: { size: 11, weight: "bold" },
                        bodyFont: { size: 11 },
                        callbacks: {
                            title: (items) => `${items[0].label} ${summary.month_label || ""}`,
                            label: (ctx) => ` ${ctx.dataset.label}: ${formatCurrency(ctx.parsed.y)}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 10 }, color: "#a1a1aa", maxTicksLimit: 16 }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (val) => `₹${val}`,
                            font: { size: 10 },
                            color: "#a1a1aa"
                        },
                        grid: { color: "rgba(0, 0, 0, 0.04)" }
                    }
                }
            }
        });
    }

    // 2. Category Breakdown Chart Sorted Descending by Spend
    const catBreakdown = summary.category_breakdown || {};
    const sortedCategories = Object.keys(catBreakdown)
        .map(cat => ({ category: cat, total: catBreakdown[cat] }))
        .sort((a, b) => b.total - a.total);

    const rankingLabels = sortedCategories.map(c => c.category);
    const rankingData = sortedCategories.map(c => c.total);
    const rankingColors = sortedCategories.map(c => (CATEGORY_CONFIG[c.category] ? CATEGORY_CONFIG[c.category].color : "#18181b"));

    const ctxRanking = document.getElementById("chart-category-ranking");
    if (ctxRanking) {
        if (state.chartCategoryRanking) state.chartCategoryRanking.destroy();

        state.chartCategoryRanking = new Chart(ctxRanking.getContext("2d"), {
            type: "bar",
            data: {
                labels: rankingLabels,
                datasets: [{
                    label: "Spend",
                    data: rankingData,
                    backgroundColor: rankingColors,
                    borderRadius: 3,
                    barThickness: 14
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                onClick: (evt, elements) => {
                    if (elements && elements.length > 0) {
                        const index = elements[0].index;
                        const selectedCategory = rankingLabels[index];
                        setCategoryFilter(selectedCategory);
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#18181b",
                        titleColor: "#ffffff",
                        bodyColor: "#f4f4f5",
                        borderColor: "rgba(255,255,255,0.1)",
                        borderWidth: 1,
                        padding: 8,
                        cornerRadius: 8,
                        titleFont: { size: 11, weight: "bold" },
                        bodyFont: { size: 11 },
                        callbacks: {
                            label: (ctx) => ` Spend: ${formatCurrency(ctx.parsed.x)}`
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: (val) => `₹${val}`,
                            font: { size: 10 },
                            color: "#a1a1aa"
                        },
                        grid: { color: "rgba(0, 0, 0, 0.04)" }
                    },
                    y: {
                        ticks: { font: { size: 10, weight: "600" }, color: "#52525b" },
                        grid: { display: false }
                    }
                }
            }
        });
    }
}

// ---------------------------------------------------------------------------
// Filtering & List Display (Date Only, No Time)
// ---------------------------------------------------------------------------

function setCategoryFilter(category) {
    state.categoryFilter = category;
    document.getElementById("category-filter-badge").classList.remove("hidden");
    document.getElementById("category-filter-name").textContent = category;
    document.getElementById("btn-clear-category-filter").classList.remove("hidden");
    document.getElementById("panel-badge-title").textContent = "Filtered Category";
    document.getElementById("selected-date-title").textContent = `Category: ${category}`;

    renderCategoryBudgetCards(state.monthlySummary ? state.monthlySummary.category_budgets || {} : {});
    fetchSelectedExpenses();
}

function clearCategoryFilter() {
    state.categoryFilter = null;
    document.getElementById("category-filter-badge").classList.add("hidden");
    document.getElementById("btn-clear-category-filter").classList.add("hidden");
    document.getElementById("panel-badge-title").textContent = "Selected Date";
    document.getElementById("selected-date-title").textContent = formatDateReadable(state.selectedDate);

    renderCategoryBudgetCards(state.monthlySummary ? state.monthlySummary.category_budgets || {} : {});
    fetchSelectedExpenses();
}

function renderExpensesList(expenses, total, count) {
    const listEl = document.getElementById("daily-expenses-list");
    const emptyEl = document.getElementById("daily-empty-state");
    const totalEl = document.getElementById("selected-date-total");
    const countEl = document.getElementById("selected-date-count");

    totalEl.textContent = formatCurrency(total);
    countEl.textContent = `(${count} item${count === 1 ? "" : "s"})`;

    if (!expenses || expenses.length === 0) {
        listEl.innerHTML = "";
        emptyEl.classList.remove("hidden");
        return;
    }

    emptyEl.classList.add("hidden");
    listEl.innerHTML = expenses.map(item => {
        const catCfg = CATEGORY_CONFIG[item.category] || CATEGORY_CONFIG["General & Others"];
        return `
            <div class="group py-2.5 px-3 rounded-lg hover:bg-neutral-50/80 border border-transparent hover:border-black/[0.05] transition-all flex items-center justify-between">
                <div class="flex items-center space-x-3 min-w-0">
                    <div class="h-7 w-7 rounded-md bg-neutral-100 text-neutral-700 flex items-center justify-center text-xs shrink-0">
                        <i class="fa-solid ${catCfg.icon}"></i>
                    </div>
                    <div class="min-w-0">
                        <div class="flex items-center space-x-2">
                            <h4 class="text-xs font-semibold text-neutral-900 truncate">${item.item}</h4>
                            <span class="text-[10px] text-neutral-300">•</span>
                            <span class="text-[10px] text-neutral-500 font-medium">${item.category}</span>
                        </div>
                        <div class="flex items-center space-x-2 text-[10px] text-neutral-400 mt-0.5">
                            <span class="font-mono">${item.date}</span>
                            <span>•</span>
                            <span class="inline-flex items-center px-1.5 py-0.2 rounded bg-neutral-100 text-neutral-600 font-medium">
                                ${item.payment_mode || "UPI"}
                            </span>
                            ${item.notes ? `<span>•</span><span class="truncate max-w-[140px] italic">${item.notes}</span>` : ""}
                        </div>
                    </div>
                </div>
                <div class="text-right shrink-0 ml-3">
                    <span class="text-xs sm:text-sm font-bold text-neutral-950 tabular-nums">${formatCurrency(item.amount)}</span>
                </div>
            </div>
        `;
    }).join("");
}

// ---------------------------------------------------------------------------
// Interactive Calendar Grid
// ---------------------------------------------------------------------------

function renderCalendar(dailyTotals) {
    const calendarGrid = document.getElementById("calendar-grid");
    const calendarTitle = document.getElementById("calendar-title");
    calendarGrid.innerHTML = "";

    calendarTitle.textContent = `${MONTH_NAMES[state.currentMonth - 1]} ${state.currentYear}`;

    const dateSpendMap = {};
    dailyTotals.forEach(d => { dateSpendMap[d.date] = d.total; });

    const firstDayIndex = new Date(state.currentYear, state.currentMonth - 1, 1).getDay();
    const daysInMonth = new Date(state.currentYear, state.currentMonth, 0).getDate();

    for (let i = 0; i < firstDayIndex; i++) {
        const blank = document.createElement("div");
        blank.className = "h-11 sm:h-12 rounded-lg bg-neutral-50/40 border border-transparent";
        calendarGrid.appendChild(blank);
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${state.currentYear}-${String(state.currentMonth).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
        const hasSpend = Boolean(dateSpendMap[dateStr]);
        const isSelected = state.selectedDate === dateStr && !state.categoryFilter;

        const tile = document.createElement("button");
        tile.type = "button";
        tile.className = `calendar-tile h-11 sm:h-12 rounded-lg border p-1 sm:p-1.5 flex flex-col justify-between text-left transition-all ${
            isSelected
                ? "border-neutral-900 bg-neutral-100/80 shadow-2xs"
                : hasSpend
                ? "border-emerald-200/90 bg-white hover:border-black/20"
                : "border-black/[0.05] bg-white hover:bg-neutral-50"
        }`;

        tile.innerHTML = `
            <div class="flex items-center justify-between">
                <span class="text-[11px] font-bold ${isSelected ? 'text-neutral-950' : 'text-neutral-600'}">${day}</span>
                ${hasSpend ? '<span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>' : ''}
            </div>
            <div class="text-right">
                ${hasSpend ? `<span class="text-[10px] font-bold text-emerald-600 block tabular-nums">${formatCompactCurrency(dateSpendMap[dateStr])}</span>` : '<span class="text-[9px] text-neutral-300">-</span>'}
            </div>
        `;

        tile.addEventListener("click", () => {
            state.selectedDate = dateStr;
            clearCategoryFilter();
            renderCalendar(dailyTotals);
        });

        calendarGrid.appendChild(tile);
    }
}

// ---------------------------------------------------------------------------
// Budget Settings Modal
// ---------------------------------------------------------------------------

async function openBudgetModal() {
    try {
        const res = await fetch("/api/budget");
        const data = await res.json();
        const budget = data.budget || {};
        state.budgetConfig = budget;

        document.getElementById("input-monthly-income").value = budget.monthly_income || 25000;

        const catContainer = document.getElementById("budget-category-inputs-container");
        catContainer.innerHTML = "";

        const cats = Object.keys(CATEGORY_CONFIG);
        cats.forEach(cat => {
            const cfg = CATEGORY_CONFIG[cat];
            const currentVal = (budget.categories && budget.categories[cat]) ? budget.categories[cat] : 0;

            const row = document.createElement("div");
            row.className = "flex items-center justify-between text-xs";
            row.innerHTML = `
                <div class="flex items-center space-x-2">
                    <span class="h-2 w-2 rounded-full" style="background-color: ${cfg.color}"></span>
                    <span class="font-medium text-slate-700">${cat}</span>
                </div>
                <div class="w-32">
                    <input type="number" step="100" min="0" data-category="${cat}" value="${currentVal}"
                        class="budget-cat-input w-full px-2.5 py-1 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-brand-500 font-semibold text-right">
                </div>
            `;
            catContainer.appendChild(row);
        });

        updateBudgetBufferCalculator();

        document.querySelectorAll(".budget-cat-input, #input-monthly-income").forEach(inp => {
            inp.addEventListener("input", updateBudgetBufferCalculator);
        });

        document.getElementById("modal-budget-settings").classList.remove("hidden");
    } catch (e) {
        console.error("Failed to load budget:", e);
    }
}

function updateBudgetBufferCalculator() {
    const income = parseFloat(document.getElementById("input-monthly-income").value) || 0;
    let totalAlloc = 0;
    document.querySelectorAll(".budget-cat-input").forEach(inp => {
        totalAlloc += parseFloat(inp.value) || 0;
    });

    const unallocated = income - totalAlloc;
    document.getElementById("modal-budget-total-allocated").textContent = formatCurrency(totalAlloc);

    const unallocEl = document.getElementById("modal-budget-unallocated");
    unallocEl.textContent = formatCurrency(unallocated);
    if (unallocated < 0) {
        unallocEl.className = "font-bold text-rose-600";
    } else {
        unallocEl.className = "font-bold text-emerald-600";
    }
}

async function saveBudgetSettings(e) {
    e.preventDefault();
    const income = parseFloat(document.getElementById("input-monthly-income").value) || 0;
    const categories = {};

    document.querySelectorAll(".budget-cat-input").forEach(inp => {
        const cat = inp.getAttribute("data-category");
        categories[cat] = parseFloat(inp.value) || 0;
    });

    try {
        const res = await fetch("/api/budget", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ monthly_income: income, categories })
        });
        const data = await res.json();
        if (data.status === "success") {
            playAudioChime(750, 0.2);
            document.getElementById("modal-budget-settings").classList.add("hidden");
            fetchMonthlySummary();
        } else {
            alert(data.message || "Failed to save budget settings.");
        }
    } catch (err) {
        console.error("Error saving budget:", err);
    }
}

// ---------------------------------------------------------------------------
// Speech Recognition Flow (Web Speech API)
// ---------------------------------------------------------------------------

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return null;

    const recognizer = new SpeechRecognition();
    recognizer.continuous = false;
    recognizer.interimResults = true;
    recognizer.lang = "en-IN";

    recognizer.onstart = () => {
        state.isListening = true;
        playAudioChime(520, 0.15);
        document.getElementById("voice-listening-overlay").classList.remove("hidden");
        document.getElementById("voice-live-transcript").textContent = "Listening... speak now";
    };

    recognizer.onresult = (event) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            transcript += event.results[i][0].transcript;
        }
        document.getElementById("voice-live-transcript").textContent = transcript;
    };

    recognizer.onerror = (event) => {
        state.isListening = false;
        document.getElementById("voice-listening-overlay").classList.add("hidden");
    };

    recognizer.onend = () => {
        state.isListening = false;
        const text = document.getElementById("voice-live-transcript").textContent.trim();
        document.getElementById("voice-listening-overlay").classList.add("hidden");
        if (text && !text.startsWith("Listening...")) {
            processVoiceTranscript(text);
        }
    };

    return recognizer;
}

function startVoiceRecognition() {
    if (!state.speechRecognition) {
        state.speechRecognition = initSpeechRecognition();
    }
    if (state.speechRecognition) {
        try {
            state.speechRecognition.start();
        } catch (e) {
            state.speechRecognition.stop();
        }
    } else {
        alert("Speech Recognition is not supported by your browser. Please use Google Chrome or Microsoft Edge.");
    }
}

async function processVoiceTranscript(transcript) {
    try {
        const res = await fetch("/api/parse-voice", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: transcript })
        });
        const data = await res.json();
        if (data.status === "success") {
            const parsed = data.data;
            playAudioChime(880, 0.2);

            // Populate voice confirmation modal (Date only, no time)
            document.getElementById("voice-original-text").textContent = `"${data.transcript || transcript}"`;
            document.getElementById("voice-input-item").value = parsed.item || "";
            document.getElementById("voice-input-amount").value = parsed.amount || "";
            document.getElementById("voice-input-date").value = parsed.date || new Date().toISOString().split("T")[0];
            document.getElementById("voice-input-category").value = parsed.category || "Food";
            document.getElementById("voice-input-payment-mode").value = parsed.payment_mode || "UPI";

            document.getElementById("modal-voice-confirm").classList.remove("hidden");
        } else {
            alert(data.message || "Could not parse voice command. Please try again.");
        }
    } catch (err) {
        console.error("Error processing voice transcript:", err);
    }
}

// ---------------------------------------------------------------------------
// Month-End Email Dispatch Flow
// ---------------------------------------------------------------------------

function openEmailReportModal() {
    const monthStr = `${state.currentYear}-${String(state.currentMonth).padStart(2, "0")}`;
    document.getElementById("email-report-month-label").textContent = `${MONTH_NAMES[state.currentMonth - 1]} ${state.currentYear}`;
    document.getElementById("email-report-attachment-name").textContent = `Expenses_${monthStr}.csv`;

    const statusBanner = document.getElementById("email-status-banner");
    statusBanner.className = "hidden p-2.5 rounded-lg text-xs font-semibold";
    statusBanner.textContent = "";

    document.getElementById("modal-email-report").classList.remove("hidden");
}

async function handleSendEmailReport() {
    const monthStr = `${state.currentYear}-${String(state.currentMonth).padStart(2, "0")}`;
    const btn = document.getElementById("btn-send-email-confirm");
    const statusBanner = document.getElementById("email-status-banner");

    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1.5"></i> Sending...`;

    try {
        const res = await fetch(`/api/send-monthly-report?month=${monthStr}`, {
            method: "POST"
        });
        const data = await res.json();

        if (res.ok && data.status === "success") {
            playAudioChime(950, 0.25);
            statusBanner.className = "p-2.5 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 block";
            statusBanner.textContent = `✓ ${data.message}`;
            setTimeout(() => {
                document.getElementById("modal-email-report").classList.add("hidden");
            }, 2000);
        } else {
            statusBanner.className = "p-2.5 rounded-lg text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-200 block";
            statusBanner.textContent = `✗ ${data.message || "Failed to dispatch email."}`;
        }
    } catch (err) {
        statusBanner.className = "p-2.5 rounded-lg text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-200 block";
        statusBanner.textContent = `✗ Network error sending email.`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-envelope mr-1.5"></i> Send Report Now`;
    }
}

// ---------------------------------------------------------------------------
// Password-Protected Database Reset Flow
// ---------------------------------------------------------------------------

function openResetModal() {
    document.getElementById("input-admin-password").value = "";
    const errEl = document.getElementById("reset-error-msg");
    errEl.classList.add("hidden");
    errEl.textContent = "";
    document.getElementById("modal-reset-db").classList.remove("hidden");
    document.getElementById("input-admin-password").focus();
}

async function handleResetDatabase(e) {
    e.preventDefault();
    const password = document.getElementById("input-admin-password").value.trim();
    const errEl = document.getElementById("reset-error-msg");
    const btn = document.getElementById("btn-confirm-reset");

    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1"></i> Resetting...`;

    try {
        const res = await fetch("/api/reset-database", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password })
        });
        const data = await res.json();

        if (res.ok && data.status === "success") {
            playAudioChime(400, 0.3);
            document.getElementById("modal-reset-db").classList.add("hidden");
            alert("Database successfully reset! All expenses wiped.");
            fetchMonthlySummary();
            fetchSelectedExpenses();
        } else {
            errEl.textContent = data.message || "Invalid Password.";
            errEl.classList.remove("hidden");
        }
    } catch (err) {
        errEl.textContent = "Network error processing reset.";
        errEl.classList.remove("hidden");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-trash-can mr-1"></i> Confirm Reset`;
    }
}

// ---------------------------------------------------------------------------
// Event Listeners & Bootstrapping
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
    // Top month navigation
    document.getElementById("btn-prev-month").addEventListener("click", () => {
        state.currentMonth--;
        if (state.currentMonth < 1) {
            state.currentMonth = 12;
            state.currentYear--;
        }
        fetchMonthlySummary();
        fetchSelectedExpenses();
    });

    document.getElementById("btn-next-month").addEventListener("click", () => {
        state.currentMonth++;
        if (state.currentMonth > 12) {
            state.currentMonth = 1;
            state.currentYear++;
        }
        fetchMonthlySummary();
        fetchSelectedExpenses();
    });

    document.getElementById("btn-current-month").addEventListener("click", () => {
        const now = new Date();
        state.currentYear = now.getFullYear();
        state.currentMonth = now.getMonth() + 1;
        state.selectedDate = now.toISOString().split("T")[0];
        clearCategoryFilter();
        fetchMonthlySummary();
        fetchSelectedExpenses();
    });

    // Budget Planner modal triggers
    document.getElementById("btn-open-budget-modal").addEventListener("click", openBudgetModal);
    document.getElementById("btn-close-budget-modal").addEventListener("click", () => {
        document.getElementById("modal-budget-settings").classList.add("hidden");
    });
    document.getElementById("btn-cancel-budget-modal").addEventListener("click", () => {
        document.getElementById("modal-budget-settings").classList.add("hidden");
    });
    document.getElementById("form-budget-settings").addEventListener("submit", saveBudgetSettings);

    // Email Report Modal triggers
    document.getElementById("btn-email-report").addEventListener("click", openEmailReportModal);
    document.getElementById("btn-close-email-modal").addEventListener("click", () => {
        document.getElementById("modal-email-report").classList.add("hidden");
    });
    document.getElementById("btn-cancel-email").addEventListener("click", () => {
        document.getElementById("modal-email-report").classList.add("hidden");
    });
    document.getElementById("btn-send-email-confirm").addEventListener("click", handleSendEmailReport);

    // Reset Database Modal triggers
    document.getElementById("btn-open-reset-modal").addEventListener("click", openResetModal);
    document.getElementById("btn-close-reset-modal").addEventListener("click", () => {
        document.getElementById("modal-reset-db").classList.add("hidden");
    });
    document.getElementById("btn-cancel-reset").addEventListener("click", () => {
        document.getElementById("modal-reset-db").classList.add("hidden");
    });
    document.getElementById("form-reset-db").addEventListener("submit", handleResetDatabase);

    // Voice triggers
    document.getElementById("btn-voice-header").addEventListener("click", startVoiceRecognition);
    document.getElementById("btn-voice-fab").addEventListener("click", startVoiceRecognition);
    document.getElementById("btn-stop-voice").addEventListener("click", () => {
        if (state.speechRecognition) state.speechRecognition.stop();
    });
    document.getElementById("btn-cancel-voice").addEventListener("click", () => {
        if (state.speechRecognition) state.speechRecognition.abort();
        document.getElementById("voice-listening-overlay").classList.add("hidden");
    });

    // Voice confirmation modal triggers (Date Only, No Time)
    document.getElementById("btn-close-voice-confirm").addEventListener("click", () => {
        document.getElementById("modal-voice-confirm").classList.add("hidden");
    });
    document.getElementById("btn-cancel-voice-confirm").addEventListener("click", () => {
        document.getElementById("modal-voice-confirm").classList.add("hidden");
    });
    document.getElementById("form-voice-confirm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            item: document.getElementById("voice-input-item").value.trim(),
            amount: parseFloat(document.getElementById("voice-input-amount").value),
            date: document.getElementById("voice-input-date").value,
            category: document.getElementById("voice-input-category").value,
            payment_mode: document.getElementById("voice-input-payment-mode").value,
            notes: `Voice input: ${document.getElementById("voice-original-text").textContent}`
        };

        const res = await fetch("/api/expenses", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === "success") {
            playAudioChime(950, 0.2);
            document.getElementById("modal-voice-confirm").classList.add("hidden");
            fetchMonthlySummary();
            fetchSelectedExpenses();
        } else {
            alert(data.message || "Failed to commit expense.");
        }
    });

    // Manual Add Expense modal triggers (Date Only, No Time)
    document.getElementById("btn-open-add-modal").addEventListener("click", () => {
        document.getElementById("input-date").value = state.selectedDate || new Date().toISOString().split("T")[0];
        document.getElementById("modal-add-expense").classList.remove("hidden");
    });
    document.getElementById("btn-add-for-selected-date").addEventListener("click", () => {
        document.getElementById("input-date").value = state.selectedDate || new Date().toISOString().split("T")[0];
        document.getElementById("modal-add-expense").classList.remove("hidden");
    });
    document.getElementById("btn-close-add-modal").addEventListener("click", () => {
        document.getElementById("modal-add-expense").classList.add("hidden");
    });
    document.getElementById("btn-cancel-add-modal").addEventListener("click", () => {
        document.getElementById("modal-add-expense").classList.add("hidden");
    });
    document.getElementById("form-add-expense").addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            item: document.getElementById("input-item").value.trim(),
            amount: parseFloat(document.getElementById("input-amount").value),
            date: document.getElementById("input-date").value,
            category: document.getElementById("input-category").value,
            payment_mode: document.getElementById("input-payment-mode").value,
            notes: document.getElementById("input-notes").value.trim()
        };

        const res = await fetch("/api/expenses", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === "success") {
            playAudioChime(950, 0.2);
            document.getElementById("modal-add-expense").classList.add("hidden");
            document.getElementById("form-add-expense").reset();
            fetchMonthlySummary();
            fetchSelectedExpenses();
        } else {
            alert(data.message || "Failed to save expense.");
        }
    });

    // Clear filter button
    document.getElementById("btn-clear-category-filter").addEventListener("click", clearCategoryFilter);

    // Export dropdown
    const exportBtn = document.getElementById("btn-export-menu");
    const exportMenu = document.getElementById("export-menu");
    exportBtn.addEventListener("click", () => exportMenu.classList.toggle("hidden"));
    document.addEventListener("click", (e) => {
        if (!document.getElementById("export-dropdown-wrapper").contains(e.target)) {
            exportMenu.classList.add("hidden");
        }
    });

    // Initial Load
    fetchMonthlySummary();
    fetchSelectedExpenses();
});
