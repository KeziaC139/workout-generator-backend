// ==========================================
// CONFIGURATION & GLOBAL STATE
// ==========================================
const BACKEND_URL = "https://workout-generator-backend.onrender.com";

let selectedSelections = {
    physique: null,
    equipment: null
};

let timerInterval = null;

// ==========================================
// REST TIMER MODULE
// ==========================================
function startTimer(seconds) {
    clearInterval(timerInterval);
    let remaining = seconds;
    const display = document.getElementById("timer-display");

    if (!display) return;

    function updateDisplay() {
        let mins = Math.floor(remaining / 60);
        let secs = remaining % 60;
        display.innerText = `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }

    updateDisplay();

    timerInterval = setInterval(() => {
        remaining--;
        if (remaining <= 0) {
            clearInterval(timerInterval);
            display.innerText = "TIME'S UP! 🔥";
            playTimerBeep();
        } else {
            updateDisplay();
        }
    }, 1000);
}

function stopTimer() {
    clearInterval(timerInterval);
    const display = document.getElementById("timer-display");
    if (display) display.innerText = "00:00";
}

function playTimerBeep() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = "sine";
        osc.frequency.setValueAtTime(587.33, ctx.currentTime);
        osc.frequency.setValueAtTime(880, ctx.currentTime + 0.12);

        gain.gain.setValueAtTime(0.1, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.00001, ctx.currentTime + 0.35);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start();
        osc.stop(ctx.currentTime + 0.35);
    } catch (e) {
        console.warn("AudioContext playback prevented:", e);
    }
}

// ==========================================
// INITIALIZATION & AUTHENTICATION
// ==========================================
function initializePage() {
    const activeUser = sessionStorage.getItem("workout_app_user");
    const authScreen = document.getElementById("auth-screen");
    const appContent = document.getElementById("app-content");
    const welcomeUser = document.getElementById("welcome-username");

    if (activeUser) {
        authScreen.style.display = "none";
        appContent.style.display = "block";
        if (welcomeUser) welcomeUser.innerText = activeUser;
        fetchStreak(activeUser);
        fetchWorkoutHistory();
    } else {
        authScreen.style.display = "flex";
        appContent.style.display = "none";
    }
}

async function handleAuth(type) {
    const usernameInput = document.getElementById("auth-user").value.trim();
    const passwordInput = document.getElementById("auth-pass").value.trim();

    if (!usernameInput || !passwordInput) {
        alert("Please enter both a username and password.");
        return;
    }

    const endpoint = type === 'signup' ? '/signup' : '/login';

    try {
        const response = await fetch(`${BACKEND_URL}${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: usernameInput, password: passwordInput })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Authentication failed.");
        }

        alert(data.message || "Success!");
        sessionStorage.setItem("workout_app_user", data.username);
        initializePage();

    } catch (error) {
        alert(`Authentication Error: ${error.message}`);
    }
}

function logout() {
    sessionStorage.removeItem("workout_app_user");
    location.reload();
}

// ==========================================
// UI SELECTION HELPERS
// ==========================================
function selectOption(category, value, element) {
    selectedSelections[category] = value;

    // Remove active styling from siblings
    const parentContainer = element.parentElement;
    const buttons = parentContainer.querySelectorAll('.card-btn');
    buttons.forEach(btn => btn.style.border = "1px solid #222");

    // Highlight selected card
    element.style.border = "2px solid #bc13fe";
}

// ==========================================
// WORKOUT GENERATION ENGINE
// ==========================================
async function generateWorkout() {
    const days = document.getElementById("input-days").value;
    const duration = document.getElementById("input-duration").value;
    const currentUser = sessionStorage.getItem("workout_app_user");

    if (!selectedSelections.physique || !selectedSelections.equipment) {
        alert("Please select both a Physique Archetype (Step 1) and Environmental Availability (Step 2).");
        return;
    }

    const payload = {
        username: currentUser,
        physique: selectedSelections.physique,
        equipment: selectedSelections.equipment,
        days: parseInt(days),
        duration: parseInt(duration)
    };

    try {
        const response = await fetch(`${BACKEND_URL}/generate-workout`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `Server returned HTTP ${response.status}`);
        }

        const data = await response.json();
        renderExerciseCards(data.exercises);

    } catch (error) {
        console.error("Workout Generation Error:", error);
        alert(`Workout Generation Failure: ${error.message}`);
    }
}

function renderExerciseCards(exercises) {
    const target = document.getElementById("exercise-cards-target");
    const container = document.getElementById("tracker-container");

    if (!exercises || exercises.length === 0) {
        target.innerHTML = "<p style='color:#888;'>No exercises found for these selections.</p>";
        return;
    }

    let html = "";
    exercises.forEach((ex, index) => {
        html += `
            <div style="background:#1e1e1e; border:1px solid #333; padding:15px; border-radius:8px; margin-bottom:15px; text-align:left;">
                <h3 style="color:#00e5ff; margin-top:0;">${index + 1}. ${ex.name}</h3>
                <p style="color:#aaa; margin-bottom:10px;">Target: ${ex.sets} Sets × ${ex.target_reps} Reps</p>
                <div style="display:flex; gap:10px;">
                    <input type="number" class="log-weight" data-exercise="${ex.name}" placeholder="Weight (lbs)" style="flex:1; padding:8px; background:#141414; color:#fff; border:1px solid #444; border-radius:4px;">
                    <input type="number" class="log-reps" data-exercise="${ex.name}" placeholder="Reps Done" style="flex:1; padding:8px; background:#141414; color:#fff; border:1px solid #444; border-radius:4px;">
                </div>
            </div>
        `;
    });

    target.innerHTML = html;
    container.style.display = "block";
    container.scrollIntoView({ behavior: 'smooth' });
}

// ==========================================
// SAVE & LOG WORKOUT
// ==========================================
async function saveActiveLog() {
    const currentUser = sessionStorage.getItem("workout_app_user");
    const weightInputs = document.querySelectorAll(".log-weight");
    const repsInputs = document.querySelectorAll(".log-reps");

    let loggedSets = [];

    weightInputs.forEach((input, i) => {
        const exName = input.getAttribute("data-exercise");
        const weight = parseFloat(input.value) || 0;
        const reps = parseInt(repsInputs[i].value) || 0;

        if (reps > 0) {
            loggedSets.push({
                exercise_name: exName,
                set_number: 1,
                weight_lbs: weight,
                reps_performed: reps
            });
        }
    });

    if (loggedSets.length === 0) {
        alert("Please enter at least one completed set with reps greater than 0.");
        return;
    }

    try {
        const response = await fetch(`${BACKEND_URL}/log-workout`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: currentUser, sets: loggedSets })
        });

        const data = await response.json();

        if (!response.ok) throw new Error(data.detail || "Failed to log workout.");

        alert("🎉 Workout logged successfully!");
        fetchWorkoutHistory();
        fetchStreak(currentUser);

    } catch (error) {
        alert(`Error saving log: ${error.message}`);
    }
}

// ==========================================
// HISTORY & STREAK FETCHING
// ==========================================
async function fetchWorkoutHistory() {
    const currentUser = sessionStorage.getItem("workout_app_user");
    const target = document.getElementById("history-list-target");
    const errorBox = document.getElementById("ledger-error-box");

    if (!currentUser || !target) return;

    try {
        const response = await fetch(`${BACKEND_URL}/workout-history/${currentUser}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();

        if (errorBox) errorBox.style.display = "none";

        if (!data.history || data.history.length === 0) {
            target.innerHTML = "<p style='color:#888;'>No past workout entries cataloged yet.</p>";
            return;
        }

        let html = "<ul style='list-style:none; padding:0;'>";
        data.history.slice(0, 5).forEach(item => {
            html += `
                <li style="background:#141414; border:1px solid #222; padding:10px 15px; border-radius:6px; margin-bottom:8px; display:flex; justify-content:space-between;">
                    <span style="color:#00ff87; font-weight:bold;">${item.exercise_name}</span>
                    <span>${item.weight_lbs} lbs × ${item.reps_performed} reps <small style="color:#666;">(${item.date})</small></span>
                </li>
            `;
        });
        html += "</ul>";
        target.innerHTML = html;

    } catch (error) {
        console.error("History fetch error:", error);
        if (errorBox) errorBox.style.display = "block";
    }
}

async function fetchStreak(username) {
    const streakContainer = document.getElementById("streak-container");
    const streakVal = document.getElementById("streak-count-value");

    try {
        const response = await fetch(`${BACKEND_URL}/streak/${username}`);
        if (!response.ok) return;

        const data = await response.json();
        if (streakVal) streakVal.innerText = data.streak || 0;
        if (streakContainer) streakContainer.style.display = "block";
    } catch (e) {
        console.warn("Could not fetch streak:", e);
    }
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", initializePage);