const state = {
  user: JSON.parse(localStorage.getItem("pulseboard-user") || "null"),
  calendar: {
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
  },
  goalEditId: null,
};

const $ = (selector) => document.querySelector(selector);
const formatDate = (value) => {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "Unknown date" : date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
};
const showMessage = (element, message, success = false) => {
  if (!element) return;
  element.textContent = message;
  element.style.color = success ? "#39704d" : "#b74735";
};
async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "Something went wrong. Please try again.");
  return body;
}
function renderAuth() {
  $("#auth-view").classList.toggle("hidden", Boolean(state.user));
  $("#dashboard-view").classList.toggle("hidden", !state.user);
  if (state.user) {
    $("#welcome-user").textContent = state.user.username;
    $("#heading-user").textContent = state.user.username;
    $("#last-updated").textContent = new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });
    renderTodos();
    loadDashboard();
    loadGoals();
    loadStreaks();
    renderCalendar();
  }
}
const todoKey = () => `pulseboard-todos-${state.user.id}`;
const readTodos = () => {
  try {
    return JSON.parse(localStorage.getItem(todoKey()) || "[]");
  } catch {
    return [];
  }
};
function renderTodos() {
  const list = $("#todo-list");
  const todos = readTodos();
  list.replaceChildren();
  if (!todos.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No tasks yet. Add one small step for today.";
    list.append(empty);
    return;
  }
  todos.forEach((todo) => {
    const row = document.createElement("div");
    row.className = `todo-row${todo.completed ? " completed" : ""}`;
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = todo.completed;
    checkbox.setAttribute("aria-label", `Complete ${todo.text}`);
    checkbox.addEventListener("change", () => {
      const updated = readTodos().map((item) => (item.id === todo.id ? { ...item, completed: checkbox.checked } : item));
      localStorage.setItem(todoKey(), JSON.stringify(updated));
      renderTodos();
    });
    const text = document.createElement("span");
    text.textContent = todo.text;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "icon-button";
    remove.title = "Remove task";
    remove.setAttribute("aria-label", `Remove ${todo.text}`);
    remove.textContent = "x";
    remove.addEventListener("click", () => {
      localStorage.setItem(todoKey(), JSON.stringify(readTodos().filter((item) => item.id !== todo.id)));
      renderTodos();
    });
    row.append(checkbox, text, remove);
    list.append(row);
  });
}
async function loadDashboard() {
  try {
    const entries = await request(`/dashboard/${state.user.id}`);
    renderMetrics(entries);
    renderHistory(entries);
  } catch (error) {
    showMessage($("#health-message"), error.message);
  }
}
function renderMetrics(entries) {
  const latest = entries[entries.length - 1] || {};
  $("#latest-weight").textContent = latest.weight ? Number(latest.weight).toFixed(1) : "--";
  $("#latest-water").textContent = latest.water || "--";
  $("#latest-sleep").textContent = latest.sleep ? Number(latest.sleep).toFixed(1) : "--";
  $("#entry-count").textContent = entries.length;
}
function renderHistory(entries) {
  const list = $("#history-list");
  if (!entries.length) {
    list.innerHTML = '<p class="muted">No entries yet. Your first note starts the record.</p>';
    return;
  }
  list.innerHTML = entries.slice().reverse().slice(0, 8).map((entry) => `<div class="history-row"><span class="history-date">${formatDate(entry.recorded_at)}</span><span>${entry.weight ? `${Number(entry.weight).toFixed(1)} kg` : "-"}</span><span>${entry.water || 0} glasses</span><span>${entry.sleep || 0} hrs</span><span>${entry.exercise || "Rest day"}</span></div>`).join("");
}
async function submitAuth(event, endpoint) {
  event.preventDefault();
  const form = event.currentTarget;
  const message = $("#auth-message");
  const payload = Object.fromEntries(new FormData(form));
  try {
    const result = await request(endpoint, { method: "POST", body: JSON.stringify(payload) });
    if (endpoint === "/signup") {
      showMessage(message, "Account created. You can sign in now.", true);
      form.reset();
      $("[data-auth-tab='login']").click();
    } else {
      state.user = result.user;
      localStorage.setItem("pulseboard-user", JSON.stringify(state.user));
      form.reset();
      renderAuth();
    }
  } catch (error) {
    showMessage(message, error.message);
  }
}
function getGoalTypeDisplay(type) {
  return {
    water: "Water",
    sleep: "Sleep",
    exercise: "Exercise",
    weight: "Weight",
    custom: "Custom",
  }[type] || "Goal";
}
function renderGoals(goals) {
  const list = $("#goals-list");
  if (!goals.length) {
    list.innerHTML = '<p class="muted">No goals yet. Create a goal that matches your daily rhythm.</p>';
    return;
  }
  list.innerHTML = goals.map((goal) => {
    const progress = goal.progress || {};
    const percent = Math.min(100, Math.max(0, Number(progress.percent || 0)));
    const completeClass = progress.completed ? " completed" : "";
    const title = goal.title || getGoalTypeDisplay(goal.goal_type);
    return `
      <div class="goal-item${completeClass}">
        <div class="goal-header">
          <div>
            <p class="goal-title">${title}</p>
            <div class="goal-meta">${getGoalTypeDisplay(goal.goal_type)} · ${goal.target_value} ${goal.unit} · ${goal.frequency}</div>
          </div>
          <span class="goal-chip">${progress.completed ? "Done" : `${Math.round(percent)}%`}</span>
        </div>
        <div class="progress-bar"><div class="progress-fill" style="width:${percent}%"></div></div>
        <div class="goal-actions-row">
          <div class="goal-status">${progress.current_value || 0} / ${goal.target_value} ${goal.unit}</div>
          <div>
            <button type="button" class="text-button small-button" data-goal-edit="${goal.id}">Edit</button>
            <button type="button" class="text-button small-button danger" data-goal-delete="${goal.id}">Delete</button>
          </div>
        </div>
      </div>
    `;
  }).join("");

  document.querySelectorAll("[data-goal-edit]").forEach((button) => {
    button.addEventListener("click", () => startGoalEdit(Number(button.dataset.goalEdit)));
  });
  document.querySelectorAll("[data-goal-delete]").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = Number(button.dataset.goalDelete);
      try {
        await request(`/goals/${id}?user_id=${state.user.id}`, { method: "DELETE" });
        showMessage($("#goal-message"), "Goal deleted.", true);
        loadGoals();
      } catch (error) {
        showMessage($("#goal-message"), error.message);
      }
    });
  });
}
async function loadGoals() {
  if (!state.user) return;
  try {
    const goals = await request(`/goals?user_id=${state.user.id}`);
    renderGoals(goals);
  } catch (error) {
    showMessage($("#goal-message"), error.message);
  }
}
function startGoalEdit(goalId) {
  const goal = (state.goalList || []).find((item) => item.id === goalId);
  if (!goal) return;
  state.goalEditId = goalId;
  $("#goal-form").goal_type.value = goal.goal_type;
  $("#goal-form").title.value = goal.title;
  $("#goal-form").target_value.value = goal.target_value;
  $("#goal-form").unit.value = goal.unit;
  $("#goal-form").frequency.value = goal.frequency || "daily";
  $("#goal-form").end_date.value = goal.end_date || "";
  $("#cancel-goal-edit").classList.remove("hidden");
  $("#goal-form .primary-button").innerHTML = "Update Goal <span>✓</span>";
}
async function submitGoalForm(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form));
  const body = {
    user_id: state.user.id,
    goal_type: payload.goal_type,
    title: payload.title,
    target_value: Number(payload.target_value),
    unit: payload.unit,
    frequency: payload.frequency,
    end_date: payload.end_date || null,
    is_active: true,
  };

  try {
    if (state.goalEditId) {
      await request(`/goals/${state.goalEditId}?user_id=${state.user.id}`, {
        method: "PUT",
        body: JSON.stringify({ ...body, goal_type: payload.goal_type, title: payload.title, target_value: Number(payload.target_value), unit: payload.unit, frequency: payload.frequency, end_date: payload.end_date || null }),
      });
      showMessage($("#goal-message"), "Goal updated.", true);
    } else {
      await request("/goals", { method: "POST", body: JSON.stringify(body) });
      showMessage($("#goal-message"), "Goal added.", true);
    }
    form.reset();
    state.goalEditId = null;
    $("#cancel-goal-edit").classList.add("hidden");
    $("#goal-form .primary-button").innerHTML = "Add Goal <span>+</span>";
    loadGoals();
  } catch (error) {
    showMessage($("#goal-message"), error.message);
  }
}
async function loadStreaks() {
  if (!state.user) return;
  try {
    const streak = await request(`/streaks?user_id=${state.user.id}`);
    const value = Number(streak.current_streak || 0);
    $("#streak-value").textContent = `${value} DAY STREAK`;
    $("#best-streak").textContent = `${streak.longest_streak || 0} days`;
    $("#last-completion").textContent = streak.last_completed_date ? formatDate(streak.last_completed_date) : "-";
    $("#streak-message").textContent = value > 0 ? "Keep going!" : "Start with one small win.";
  } catch (error) {
    $("#streak-message").textContent = error.message;
  }
}
async function renderCalendar() {
  if (!state.user) return;
  const { year, month } = state.calendar;
  $("#calendar-label").textContent = new Date(year, month - 1, 1).toLocaleDateString(undefined, { month: "long", year: "numeric" });
  try {
    const monthData = await request(`/calendar?year=${year}&month=${month}&user_id=${state.user.id}`);
    const days = monthData.days || [];
    const grid = $("#calendar-grid");
    const firstDay = new Date(year, month - 1, 1);
    const offset = (firstDay.getDay() + 6) % 7;
    const cells = [];
    for (let index = 0; index < offset; index += 1) {
      cells.push('<div class="calendar-day muted"></div>');
    }
    days.forEach((day) => {
      const entry = day;
      const statusClass = entry.status === "completed" ? "completed" : entry.status === "partial" ? "partial" : entry.status === "missed" ? "missed" : "";
      const symbol = entry.status === "completed" ? "🟢" : entry.status === "partial" ? "🟡" : entry.status === "missed" ? "🔴" : "⚪";
      const selectedClass = entry.date === state.selectedDate ? " selected" : "";
      cells.push(`<button type="button" class="calendar-day ${statusClass}${selectedClass}" data-calendar-date="${entry.date}"><span class="day-number">${new Date(entry.date).getDate()}</span><span class="day-status">${symbol}</span></button>`);
    });
    grid.innerHTML = cells.join("");
    document.querySelectorAll("[data-calendar-date]").forEach((button) => {
      button.addEventListener("click", async () => {
        state.selectedDate = button.dataset.calendarDate;
        await loadCalendarDetail(button.dataset.calendarDate);
        renderCalendar();
      });
    });
    if (!state.selectedDate) {
      const today = new Date();
      const currentDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
      if (currentDate.startsWith(`${year}-${String(month).padStart(2, "0")}`)) {
        state.selectedDate = currentDate;
        loadCalendarDetail(currentDate);
      }
    } else if (state.selectedDate.startsWith(`${year}-${String(month).padStart(2, "0")}`)) {
      loadCalendarDetail(state.selectedDate);
    }
  } catch (error) {
    $("#calendar-detail").innerHTML = `<p class="muted">${error.message}</p>`;
  }
}
async function loadCalendarDetail(dateValue) {
  if (!state.user) return;
  try {
    const detail = await request(`/calendar/${dateValue}?user_id=${state.user.id}`);
    const dateText = formatDate(detail.date);
    const goals = detail.goals && detail.goals.length ? detail.goals.map((goal) => `<li>${goal.title}: ${goal.completed ? "completed" : "in progress"} (${goal.percent}% / ${goal.target_value} ${goal.unit})</li>`).join("") : "<li>No goals scheduled for this day.</li>";
    $("#calendar-detail").classList.remove("empty");
    $("#calendar-detail").innerHTML = `
      <strong>${dateText}</strong>
      <ul>
        <li>💧 Water: ${detail.water || 0} glasses</li>
        <li>😴 Sleep: ${detail.sleep || 0} hours</li>
        <li>🏃 Exercise: ${detail.exercise || "No exercise logged"}</li>
        <li>🎯 Goals: ${detail.goals_completed || 0} / ${detail.total_goals || 0} completed</li>
        <li>🔥 Streak: ${Number((await request(`/streaks?user_id=${state.user.id}`)).current_streak || 0)} days</li>
      </ul>
      <div class="calendar-goal-list">${goals}</div>
    `;
  } catch (error) {
    $("#calendar-detail").classList.remove("empty");
    $("#calendar-detail").innerHTML = `<p class="muted">${error.message}</p>`;
  }
}
async function submitGoal(event) {
  return submitGoalForm(event);
}
$('[data-auth-tab="login"]').addEventListener("click", () => {
  $('[data-auth-tab="login"]').classList.add("active");
  $('[data-auth-tab="signup"]').classList.remove("active");
  $("#login-form").classList.remove("hidden");
  $("#signup-form").classList.add("hidden");
});
$('[data-auth-tab="signup"]').addEventListener("click", () => {
  $('[data-auth-tab="signup"]').classList.add("active");
  $('[data-auth-tab="login"]').classList.remove("active");
  $("#signup-form").classList.remove("hidden");
  $("#login-form").classList.add("hidden");
});
$("#login-form").addEventListener("submit", (event) => submitAuth(event, "/login"));
$("#signup-form").addEventListener("submit", (event) => submitAuth(event, "/signup"));
$("#logout-button").addEventListener("click", () => {
  state.user = null;
  state.goalEditId = null;
  localStorage.removeItem("pulseboard-user");
  renderAuth();
});
$("#todo-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const task = new FormData(form).get("task").trim();
  if (!task) return;
  const id = window.crypto?.randomUUID?.() || String(Date.now());
  localStorage.setItem(todoKey(), JSON.stringify([{ id, text: task, completed: false }, ...readTodos()]));
  form.reset();
  renderTodos();
});
$("#health-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form));
  payload.user_id = state.user.id;
  ["weight", "water", "sleep"].forEach((key) => { payload[key] = Number(payload[key] || 0); });
  try {
    await request("/health", { method: "POST", body: JSON.stringify(payload) });
    showMessage($("#health-message"), "Saved to your record.", true);
    form.reset();
    await loadDashboard();
    await loadGoals();
    await loadStreaks();
    await renderCalendar();
  } catch (error) {
    showMessage($("#health-message"), error.message);
  }
});
$("#bmi-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(event.currentTarget));
  try {
    const result = await request(`/bmi?weight=${encodeURIComponent(values.weight)}&height_cm=${encodeURIComponent(values.height)}`);
    $("#bmi-result").classList.remove("hidden");
    $("#bmi-result").innerHTML = `<strong>${result.bmi}</strong><div>${result.category} · ideal range ${result.ideal_weight_range.min_kg}-${result.ideal_weight_range.max_kg} kg</div><p class="bmi-tip">${result.health_tips[0] || "Keep listening to your body."}</p>`;
  } catch (error) {
    $("#bmi-result").textContent = error.message;
    $("#bmi-result").classList.remove("hidden");
  }
});
$("#goal-form").addEventListener("submit", submitGoal);
$("#cancel-goal-edit").addEventListener("click", () => {
  state.goalEditId = null;
  $("#goal-form").reset();
  $("#cancel-goal-edit").classList.add("hidden");
  $("#goal-form .primary-button").innerHTML = "Add Goal <span>+</span>";
  showMessage($("#goal-message"), "", false);
});
$("#calendar-prev").addEventListener("click", () => {
  const { year, month } = state.calendar;
  const previousMonth = month === 1 ? { year: year - 1, month: 12 } : { year, month: month - 1 };
  state.calendar = previousMonth;
  renderCalendar();
});
$("#calendar-next").addEventListener("click", () => {
  const { year, month } = state.calendar;
  const nextMonth = month === 12 ? { year: year + 1, month: 1 } : { year, month: month + 1 };
  state.calendar = nextMonth;
  renderCalendar();
});
$("#calendar-today").addEventListener("click", () => {
  const today = new Date();
  state.calendar = { year: today.getFullYear(), month: today.getMonth() + 1 };
  state.selectedDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  renderCalendar();
});
renderAuth();
