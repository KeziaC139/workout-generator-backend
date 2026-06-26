/**
 * Name: Kezia Chacko
 * Program: Frontend App Pipeline (app.js)
 * Manages UI selections, exercise switching dropdowns, backend communication, and rendering histories.
 */

let selections = { physique: null, equipment: null };
let masterExercisesPool = [];

// Triggers immediately when index.html loads up in the browser
function initializePage() {
    fetchMasterExercisePool();
    fetchWorkoutHistory();
}

// Caches the list of all master movements to populate alternative exercise filters
async function fetchMasterExercisePool() {
    try {
        const response = await fetch("http://127.0.0.1:8000/exercises/");
        masterExercisesPool = await response.json();
    } catch (err) {
        console.error("Failed to load master exercises:", err);
    }
}

// Manages card selection styles and saves chosen values
function selectOption(category, value, element) {
    const container = element.parentElement;
    const buttons = container.querySelectorAll('.card-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    element.classList.add('active');
    selections[category] = value;
}

// Packages payload values and requests a matching template from FastAPI
async function generateWorkout() {
    if (!selections.physique || !selections.equipment) {
        alert("Please select both a Physique Archetype and Environmental Availability first!");
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

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Server matching system failure.");
        }

        const data = await response.json();
        renderTrackerGrid(data.exercises);
    } catch (err) {
        alert(`Configuration Exception: ${err.message}`);
    }
}

// Builds the dynamic tracker data spreadsheet markup layout
function renderTrackerGrid(exercises) {
    const target = document.getElementById("exercise-cards-target");
    target.innerHTML = "";

    exercises.forEach((ex, exIndex) => {
        let cardHtml = `
            <div class="exercise-log-block" data-exercise-name="${ex.name}" style="background: #1e1e1e; border: 1px solid #333; border-radius: 8px; padding: 20px; margin-bottom: 15px; text-align: left;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; border-bottom:1px solid #2b2b2b; padding-bottom:10px;">
                    <h3 style="margin:0; color:#fff;">${ex.name} <span style="font-size:0.8rem; color:#888; font-weight:normal;">(${ex.category})</span></h3>
                    <select onchange="updateExerciseName(this, ${exIndex})" style="padding:6px; background:#111; color:#aaa; border:1px solid #444; border-radius:4px;">
                        <option value="">Alternative Movements...</option>
        `;

        masterExercisesPool.forEach(poolEx => {
            cardHtml += `<option value="${poolEx.name}">${poolEx.name}</option>`;
        });

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

// Swaps out workout headers dynamically if an alternative selection dropdown is fired
function updateExerciseName(selectElement, index) {
    if(selectElement.value !== "") {
        const header = selectElement.parentElement.querySelector('h3');
        const block = selectElement.closest('.exercise-log-block');
        header.innerHTML = `${selectElement.value} <span style="font-size:0.8rem; color:#888; font-weight:normal;">(Substituted)</span>`;
        block.setAttribute('data-exercise-name', selectElement.value);
    }
}

// Scrapes input row metric values and posts them straight to SQLite via /submit-log
async function saveActiveLog() {
    const blocks = document.querySelectorAll(".exercise-log-block");
    const logPayload = [];

    blocks.forEach(block => {
        const name = block.getAttribute("data-exercise-name");
        const rows = block.querySelectorAll(".set-row");

        rows.forEach(row => {
            logPayload.push({
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
            alert("Workout session written into history successfully! 🏆");
            fetchWorkoutHistory(); // Refreshes the display table layout automatically
        }
    } catch (err) {
        alert("Failed to communicate tracking inputs to server.");
    }
}

// Hits /workout-history and builds the historical training ledger view
async function fetchWorkoutHistory() {
    const target = document.getElementById("history-log-target");
    try {
        const response = await fetch("http://127.0.0.1:8000/workout-history/");
        const data = await response.json();

        if (data.status !== "success" || !data.history || data.history.length === 0) {
            target.innerHTML = `<p style="color: #666;">No logged sessions found in the system yet.</p>`;
            return;
        }

        let htmlTable = `
            <div style="overflow-x: auto; width: 100%;">
                <table style="width: 100%; border-collapse: collapse; text-align: left; margin-top: 10px; background: #1a1a1a; border-radius: 8px; overflow: hidden;">
                    <thead>
                        <tr style="background: #262626; color: #bc13fe; border-bottom: 2px solid #333;">
                            <th style="padding: 12px;">Timestamp</th>
                            <th style="padding: 12px;">Exercise Movement</th>
                            <th style="padding: 12px; text-align:center;">Set</th>
                            <th style="padding: 12px; text-align:center;">Load</th>
                            <th style="padding: 12px; text-align:center;">Reps</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        data.history.forEach(row => {
            const cleanDate = new Date(row.date).toLocaleString();
            htmlTable += `
                <tr style="border-bottom: 1px solid #262626; transition: background 0.2s;" onmouseover="this.style.background='#222'" onmouseout="this.style.background='none'">
                    <td style="padding: 12px; color: #777; font-size:0.9rem;">${cleanDate}</td>
                    <td style="padding: 12px; font-weight: bold; color: #fff;">${row.exercise_name}</td>
                    <td style="padding: 12px; color: #bc13fe; text-align:center; font-weight:bold;">${row.set_number}</td>
                    <td style="padding: 12px; color: #00ff87; text-align:center;">${row.weight_lbs} lbs</td>
                    <td style="padding: 12px; color: #00e5ff; text-align:center;">${row.reps_performed}</td>
                </tr>
            `;
        });

        htmlTable += `</tbody></table></div>`;
        target.innerHTML = htmlTable;
    } catch (error) {
        console.error("Error fetching history:", error);
        target.innerHTML = `<p style="color: #ff4a4a;">Failed to load training database logs.</p>`;
    }
}