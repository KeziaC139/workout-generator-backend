let selections = { physique: null, equipment: null };
let masterExercisesPool = [];
let currentUser = null;

// Handle user authentications (Sign up / Log in)
async function handleAuth(type) {
    const userField = document.getElementById("auth-user").value.trim();
    const passField = document.getElementById("auth-pass").value.trim();

    if (!userField || !passField) {
        alert("Please complete both username and password security inputs.");
        return;
    }

    const endpoint = `http://127.0.0.1:8000/${type}`;
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
            document.getElementById("welcome-username").innerText = currentUser;
            document.getElementById("auth-screen").style.display = "none";
            document.getElementById("app-content").style.display = "block";
            initializePage();
        }
    } catch (err) {
        alert(`Authentication Failure: ${err.message}`);
    }
}

function logout() {
    currentUser = null;
    document.getElementById("auth-user").value = "";
    document.getElementById("auth-pass").value = "";
    document.getElementById("auth-screen").style.display = "flex";
    document.getElementById("app-content").style.display = "none";
    document.getElementById("tracker-container").style.display = "none";
}

function initializePage() {
    fetchMasterExercisePool();
    fetchWorkoutHistory();
}

async function fetchMasterExercisePool() {
    try {
        const response = await fetch("http://127.0.0.1:8000/exercises/");
        masterExercisesPool = await response.json();
    } catch (err) {
        console.error("Failed to fetch exercises:", err);
    }
}

function selectOption(category, value, element) {
    const container = element.parentElement;
    const buttons = container.querySelectorAll('.card-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    element.classList.add('active');
    selections[category] = value;
}

async function generateWorkout() {
    if (!selections.physique || !selections.equipment) {
        alert("Select choices first!");
        return;
    }

    const payload = {
        physique: selections.physique,
        equipment: selections.equipment,
        days_per_week: parseInt(document.getElementById("input-days").value),
        duration_mins: parseInt(document.getElementById("input-duration").value)
    };

    try {
        const response = await fetch("http://127.0.0.1:8000/recommend-workout/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error("Matching failure.");
        const data = await response.json();
        renderTrackerGrid(data.exercises);
    } catch (err) {
        alert(err.message);
    }
}

function renderTrackerGrid(exercises) {
    const target = document.getElementById("exercise-cards-target");
    target.innerHTML = "";

    exercises.forEach((ex, exIndex) => {
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
        for (let s = 1; s <= ex.default_sets; s++) {
            cardHtml += `
                <div class="set-row" data-set-number="${s}" style="display: grid; grid-template-columns: 1fr 2fr 2fr; gap: 10px; margin-bottom: 8px; align-items: center;">
                    <div style="text-align: center; color: #bc13fe; font-weight: bold;">${s}</div>
                    <div><input type="number" class="input-weight" value="0" style="width:100%; padding:8px; background:#111; color:#00ff87; border:1px solid #333; border-radius:4px; text-align:center;"></div>
                    <div><input type="number" class="input-reps" value="${ex.default_reps}" style="width:100%; padding:8px; background:#111; color:#00e5ff; border:1px solid #333; border-radius:4px; text-align:center;"></div>
                </div>
            `;
        }
        cardHtml += `</div>`;
        target.insertAdjacentHTML("beforeend", cardHtml);
    });

    document.getElementById("tracker-container").style.display = "block";
    document.getElementById("tracker-container").scrollIntoView({ behavior: 'smooth' });
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
                username: currentUser, // Appends current user name to workout entry
                exercise_name: name,
                set_number: parseInt(row.getAttribute("data-set-number")),
                weight_lbs: parseFloat(row.querySelector(".input-weight").value) || 0,
                reps_performed: parseInt(row.querySelector(".input-reps").value) || 0
            });
        });
    });

    try {
        const response = await fetch("http://127.0.0.1:8000/submit-log/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(logPayload)
        });
        const data = await response.json();
        if (data.status === "success") {
            alert("Workout written to your history record! 🏆");
            fetchWorkoutHistory();
        }
    } catch (err) {
        alert("Failed to save log data.");
    }
}

async function fetchWorkoutHistory() {
    if(!currentUser) return;
    const target = document.getElementById("history-log-target");
    try {
        const response = await fetch(`http://127.0.0.1:8000/workout-history/${currentUser}/`);
        const data = await response.json();

        if (data.status !== "success" || !data.history || data.history.length === 0) {
            target.innerHTML = `<p style="color: #666;">No logged sessions found for account: ${currentUser}.</p>`;
            return;
        }

        let htmlTable = `<div style="overflow-x: auto; width: 100%;"><table style="width: 100%; border-collapse: collapse; text-align: left; background: #1a1a1a; border-radius: 8px; overflow: hidden;">
            <thead><tr style="background: #262626; color: #bc13fe; border-bottom: 2px solid #333;"><th style="padding: 12px;">Timestamp</th><th style="padding: 12px;">Exercise</th><th style="padding: 12px; text-align:center;">Set</th><th style="padding: 12px; text-align:center;">Load</th><th style="padding: 12px; text-align:center;">Reps</th></tr></thead><tbody>`;

        data.history.forEach(row => {
            const cleanDate = new Date(row.date).toLocaleString();
            htmlTable += `<tr style="border-bottom: 1px solid #262626;"><td style="padding: 12px; color: #777; font-size:0.9rem;">${cleanDate}</td><td style="padding: 12px; font-weight: bold; color: #fff;">${row.exercise_name}</td><td style="padding: 12px; color: #bc13fe; text-align:center; font-weight:bold;">${row.set_number}</td><td style="padding: 12px; color: #00ff87; text-align:center;">${row.weight_lbs} lbs</td><td style="padding: 12px; color: #00e5ff; text-align:center;">${row.reps_performed}</td></tr>`;
        });
        target.innerHTML = htmlTable + "</tbody></table></div>";
    } catch (error) {
        target.innerHTML = `<p style="color: #ff4a4a;">Failed to load logs.</p>`;
    }
}