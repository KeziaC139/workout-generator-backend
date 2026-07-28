/**
 * Name: Kezia Chacko
 * Program: Frontend App Pipeline (app.js)
 * Manages UI selections, user login states, backend workout integration, and streak metrics.
 */

// Live Backend Production Base URL
const BACKEND_URL = "https://workout-generator-backend.onrender.com";

let selections = { physique: null, equipment: null };
let masterExercisesPool = [];
let currentUser = null;

// --- AUTOMATIC AUTO-LOGIN HANDSHAKE ---
// Checks immediately if a session exists in the browser when page runs
(function checkActiveSession() {
    const savedUser = sessionStorage.getItem("workout_app_user");
    if (savedUser) {
        const checkExist = setInterval(() => {
            const authScreen = document.getElementById("auth-screen");
            const appContent = document.getElementById("app-content");
            const welcomeUser = document.getElementById("welcome-username");

            if (authScreen && appContent && welcomeUser) {
                currentUser = savedUser;
                welcomeUser.innerText = currentUser;
                authScreen.style.display = "none";
                appContent.style.display = "block";

                // Initialize page data, streaks, and user history ledger
                initializePage();
                fetchUserStreak();
                fetchWorkoutHistory();

                clearInterval(checkExist);
            }
        }, 10);
    }
})();

function initializePage() {
    fetchMasterExercisePool();
}

// --- STREAK ENGINE INTEGRATION ---
// Fetches the active daily workout streak from the backend database
async function fetchUserStreak() {
    if (!currentUser) return;

    try {
        const response = await fetch(`${BACKEND_URL}/streak/${currentUser}`);
        if (!response.ok) throw new Error("Could not fetch streak data.");

        const data = await response.json();

        // Update UI streak count display if elements exist
        const streakContainer = document.getElementById("streak-container");
        const streakCountVal = document.getElementById("streak-count-value");

        const streakValue = data.streak_count ?? data.current_streak ?? 0;

        if (streakCountVal) {
            streakCountVal.innerText = streakValue;
        }
        if (streakContainer) {
            streakContainer.style.display = "block";
        }
    } catch (err) {
        console.error("Streak Engine Error:", err);
    }
}

// --- WORKOUT HISTORY LEDGER ---
// Fetches historical logs for the authenticated user
async function fetchWorkoutHistory() {
    if (!currentUser) return;

    try {
        const response = await fetch(`${BACKEND_URL}/workout-history/${currentUser}`);
        if (!response.ok) throw new Error("Failed to load workout history.");

        const data = await response.json();
        const historyTarget = document.getElementById("history-list-target");

        if (historyTarget && data.history) {
            if (data.history.length === 0) {
                historyTarget.innerHTML = "<p style='color:#888;'>No past workout history logged yet.</p>";
                return;
            }

            let historyHtml = "<ul style='list-style:none; padding:0;'>";
            data.history.forEach(item => {
                historyHtml += `
                    <li style="background:#1e1e1e; border:1px solid #333; margin-bottom:8px; padding:10px; border-radius:6px; color:#ccc;">
                        <strong style="color:#00ff87;">${item.exercise_name}</strong> - Set ${item.set_number}:
                        ${item.weight_lbs} lbs x ${item.reps_performed} reps
                        <span style="font-size:0.75rem; color:#888; float:right;">${item.date || ''}</span>
                    </li>
                `;
            });
            historyHtml += "</ul>";
            historyTarget.innerHTML = historyHtml;
        }
    } catch (err) {
        console.error("Ledger History Error:", err);
    }
}

// Handle user authentications (Sign up / Log in)
async function handleAuth(type) {
    const userField = document.getElementById("auth-user").value.trim();
    const passField = document.getElementById("auth-pass").value.trim();

    if (!userField || !passField) {
        alert("Please complete both username and password security inputs.");
        return;
    }

    const endpoint = `${BACKEND_URL}/${type}`;
    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: userField, password: passField })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Authentication broken.");

        if (type === 'signup') {
            alert("Account encrypted and built successfully! Please Log In.");
        } else {
            currentUser = data.username;
            sessionStorage.setItem("workout_app_user", data.username); // Remembers session

            document.getElementById("welcome-username").innerText = currentUser;
            document.getElementById("auth-screen").style.display = "none";
            document.getElementById("app-content").style.display = "block";

            initializePage();
            fetchUserStreak(); // Load streak count upon successful login
            fetchWorkoutHistory(); // Load workout history ledger
        }
    } catch (err) {
        alert(`Authentication Failure: ${err.message}`);
    }
}

function logout() {
    currentUser = null;
    sessionStorage.removeItem("workout_app_user"); // Clears memory

    document.getElementById("auth-user").value = "";
    document.getElementById("auth-pass").value = "";
    document.getElementById("auth-screen").style.display = "flex";
    document.getElementById("app-content").style.display = "none";

    const trackerContainer = document.getElementById("tracker-container");
    if (trackerContainer) trackerContainer.style.display = "none";

    const streakContainer = document.getElementById("streak-container");
    if (streakContainer) streakContainer.style.display = "none";
}

async function fetchMasterExercisePool() {
    try {
        const response = await fetch(`${BACKEND_URL}/exercises/`);
        masterExercisesPool = await response.json();
    } catch (err) {
        console.error("Failed to fetch exercises:", err);
    }
}

function selectOption(category, value, element) {
    if (!element) return;

    const container = element.parentElement;
    const buttons = container.querySelectorAll('.card-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    element.classList.add('active');
    selections[category] = value;
}

async function generateWorkout() {
    if (!selections.physique || !selections.equipment) {
        alert("Please select both options first!");
        return;
    }

    const daysInput = document.getElementById("input-days");
    const durationInput = document.getElementById("input-duration");

    const daysVal = daysInput ? parseInt(daysInput.value) || 3 : 3;
    const durationVal = durationInput ? parseInt(durationInput.value) || 45 : 45;

    const payload = {
        physique: selections.physique,
        equipment: selections.equipment,
        days_per_week: daysVal,
        duration_mins: durationVal
    };

    try {
        const response = await fetch(`${BACKEND_URL}/recommend-workout/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Matching failure.");

        renderTrackerGrid(data.exercises);
    } catch (err) {
        alert(`Workout Generation Failure: ${err.message}`);
    }
}

function renderTrackerGrid(exercises) {
    const target = document.getElementById("exercise-cards-target");
    if (!target) return;
    target.innerHTML = "";

    exercises.forEach((ex) => {
        let cardHtml = `
            <div class="exercise-log-block" data-exercise-name="${ex.name}" style="background: #1e1e1e; border: 1px solid #333; border-radius: 8px; padding: 20px; margin-bottom: 15px; text-align: left;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; border-bottom:1px solid #2b2b2b; padding-bottom:10px;">
                    <h3 style="margin:0; color:#fff;">${ex.name} <span style="font-size:0.8rem; color:#888; font-weight:normal;">(${ex.category})</span></h3>
                    <select onchange="updateExerciseName(this)" style="padding:6px; background:#111; color:#aaa; border:1px solid #444; border-radius:4px;">
                        <option value="">Alternative Movements...</option>
        `;
        masterExercisesPool.forEach(pEx => { cardHtml += `<option value="${pEx.name}">${pEx.name}</option>`; });
        cardHtml += `
                    </select>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 2fr 2fr; gap: 10px; font-weight: bold; color: #888; margin-bottom: 8px; text-align: center;">
                    <div>Set</div><div>Weight (lbs)</div><div>Reps Performed</div>
                </div>
        `;
        const totalSets = ex.default_sets || 3;
        const totalReps = ex.default_reps || 10;

        for (let s = 1; s <= totalSets; s++) {
            cardHtml += `
                <div class="set-row" data-set-number="${s}" style="display: grid; grid-template-columns: 1fr 2fr 2fr; gap: 10px; margin-bottom: 8px; align-items: center;">
                    <div style="text-align: center; color: #bc13fe; font-weight: bold;">${s}</div>
                    <div><input type="number" class="input-weight" value="0" style="width:100%; padding:8px; background:#111; color:#00ff87; border:1px solid #333; border-radius:4px; text-align:center;"></div>
                    <div><input type="number" class="input-reps" value="${totalReps}" style="width:100%; padding:8px; background:#111; color:#00e5ff; border:1px solid #333; border-radius:4px; text-align:center;"></div>
                </div>
            `;
        }
        cardHtml += `</div>`;
        target.insertAdjacentHTML("beforeend", cardHtml);
    });

    const trackerContainer = document.getElementById("tracker-container");
    if (trackerContainer) {
        trackerContainer.style.display = "block";
        trackerContainer.scrollIntoView({ behavior: 'smooth' });
    }
}

function updateExerciseName(selectElement) {
    if(selectElement.value !== "") {
        const header = selectElement.parentElement.querySelector('h3');
        const block = selectElement.closest('.exercise-log-block');
        header.innerHTML = `${selectElement.value} <span style="font-size:0.8rem; color:#888; font-weight:normal;">(Substituted)</span>`;
        block.setAttribute('data-exercise-name', selectElement.value);
    }
}

async function saveActiveLog() {
    const blocks = document.querySelectorAll(".exercise-log-block");
    const logPayload = [];

    blocks.forEach(block => {
        const name = block.getAttribute("data-exercise-name");
        const rows = block.querySelectorAll(".set-row");
        rows.forEach(row => {
            logPayload.push({
                username: currentUser,
                exercise_name: name,
                set_number: parseInt(row.getAttribute("data-set-number")),
                weight_lbs: parseFloat(row.querySelector(".input-weight").value) || 0,
                reps_performed: parseInt(row.querySelector(".input-reps").value) || 0
            });
        });
    });

    if (logPayload.length === 0) {
        alert("No workout items available to save.");
        return;
    }

    try {
        const response = await fetch(`${BACKEND_URL}/submit-log/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(logPayload)
        });
        const data = await response.json();

        if (response.ok && data.status === "success") {
            alert("Workout written to your history record! 🏆");

            // Refresh streak and history ledger immediately
            fetchUserStreak();
            fetchWorkoutHistory();
        } else {
            throw new Error(data.detail || "Error logging workout.");
        }
    } catch (err) {
        alert(`Failed to save log data: ${err.message}`);
    }
}

// --- GLOBAL ATTACHMENTS (Ensures inline HTML onclick bindings work) ---
window.handleAuth = handleAuth;
window.selectOption = selectOption;
window.generateWorkout = generateWorkout;
window.saveActiveLog = saveActiveLog;
window.logout = logout;
window.updateExerciseName = updateExerciseName;
window.fetchWorkoutHistory = fetchWorkoutHistory;