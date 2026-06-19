//Holds the user's choices as they click through
let userSelection = {
    physique: "",
    equipment: "",
    days_per_week: 4,
    duration_mins: 60
};

let currentExercises = []; // Holds the exercises currently on the screen
let masterExercisesList = []; // Holds all alternative exercises for swapping

// Captures physique choice and moves to Step 2
function selectPhysique(type) {
    userSelection.physique = type;
    navigateToStep(1, 2);
}

// Captures equipment choice and moves to Step 3
function selectEquipment(type) {
    userSelection.equipment = type;
    navigateToStep(2, 3);
    fetchAllExercises(); // Prefetch the swap alternatives in the background
}

// Fetch all alternative exercises for the mix-and-match feature
async function fetchAllExercises() {
    try {
        const response = await fetch('http://127.0.0.1:8000/exercises');
        masterExercisesList = await response.json();
    } catch (err) {
        console.error("Failed to load alternative exercises for swapping", err);
    }
}

// STEP 3 -> STEP 4: Request data and dynamically build the tracking spreadsheet
async function generateWorkout() {
    userSelection.days_per_week = parseInt(document.getElementById('days').value);
    userSelection.duration_mins = parseInt(document.getElementById('duration').value);

    const trackerContainer = document.getElementById('tracker-container');
    trackerContainer.innerHTML = "<h3>⏳ Organizing your training room...</h3>";
    navigateToStep(3, 4);

    try {
        const response = await fetch('http://127.0.0.1:8000/recommend-workout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userSelection)
        });

        const data = await response.json();

        if (response.ok) {
            currentExercises = data.exercises;
            renderTrackerDashboard();
        } else {
            trackerContainer.innerHTML = `<h3>⚠️ Error</h3><p>${data.detail}</p>`;
        }
    } catch (error) {
        trackerContainer.innerHTML = "<h3>❌ Connection error to your Python backend. Check your terminal!</h3>";
    }
}

// Draw the editable input tables dynamically
function renderTrackerDashboard() {
    const container = document.getElementById('tracker-container');
    container.innerHTML = ""; // Clear loader text

    currentExercises.forEach((exercise, exIndex) => {
        // Create a card for each individual exercise
        const card = document.createElement('div');
        card.className = 'exercise-card';

        // Header containing Title and the Swap Dropdown selector
        let swapOptionsHtml = masterExercisesList.map(item =>
            `<option value="${item.name}" ${item.name === exercise.name ? 'selected' : ''}>${item.name}</option>`
        ).join('');

        card.innerHTML = `
            <div class="exercise-header">
                <h3>${exercise.name} <span class="tag">${exercise.category}</span></h3>
                <select class="swap-select" onchange="swapExercise(${exIndex}, this.value)">
                    ${swapOptionsHtml}
                </select>
            </div>
            <div class="sets-grid" id="sets-ex-${exIndex}"></div>
        `;

        container.appendChild(card);

        // Populate rows inside the card for every set requested by the blueprint
        const setsGrid = document.getElementById(`sets-ex-${exIndex}`);
        for (let i = 1; i <= exercise.default_sets; i++) {
            const setRow = document.createElement('div');
            setRow.className = 'set-row';
            setRow.innerHTML = `
                <span class="set-num">Set ${i}</span>
                <input type="number" placeholder="lbs" class="tracker-input weight" id="weight-${exIndex}-${i}">
                <input type="number" placeholder="reps" value="${exercise.default_reps}" class="tracker-input reps" id="reps-${exIndex}-${i}">
                <label class="check-container">
                    <input type="checkbox">
                    <span class="checkmark"></span>
                </label>
            `;
            setsGrid.appendChild(setRow);
        }
    });
}

// "Mix-and-Match" mechanism: swaps an item in our array and redraws the UI
function swapExercise(index, newName) {
    const alternative = masterExercisesList.find(e => e.name === newName);
    if (alternative) {
        currentExercises[index].name = alternative.name;
        currentExercises[index].category = alternative.category;
        renderTrackerDashboard(); // Re-render to show updated settings
    }
}

// Scrape values out of inputs and ship it over to the SQLite logs database
async function saveActiveLog() {
    let completePayload = [];

    currentExercises.forEach((exercise, exIndex) => {
        for (let i = 1; i <= exercise.default_sets; i++) {
            const weightVal = document.getElementById(`weight-${exIndex}-${i}`).value;
            const repsVal = document.getElementById(`reps-${exIndex}-${i}`).value;

            completePayload.push({
                exercise_name: exercise.name,
                set_number: i,
                weight_lbs: weightVal ? parseFloat(weightVal) : 0,
                reps_performed: repsVal ? parseInt(repsVal) : 0
            });
        }
    });

    try {
        const response = await fetch('http://127.0.0.1:8000/submit-log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(completePayload)
        });

        const data = await response.json();
        if (response.ok) {
            alert("🔥 Workout saved to history successfully!");
            resetApp();
        } else {
            alert("Error saving workout: " + data.detail);
        }
    } catch (err) {
        alert("Could not reach backend database to log weights.");
    }
}

// Simple layout switcher utility
function navigateToStep(currentStep, nextStep) {
    document.getElementById(`step-${currentStep}`).classList.remove('active');
    document.getElementById(`step-${nextStep}`).classList.add('active');
}

// Resets form back to step 1
function resetApp() {
    userSelection = { physique: "", equipment: "", days_per_week: 4, duration_mins: 60 };
    document.getElementById('step-4').classList.remove('active');
    document.getElementById('step-1').classList.add('active');
}