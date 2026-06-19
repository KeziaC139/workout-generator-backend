//Global variables to store user choices temporarily
let userSelection = {
    physique: "",
    equipment: "",
    days_per_week: 3,
    duration_mins: 60
};

//Captures physique choice and moves to Step 2
function selectPhysique(type) {
    userSelection.physique = type;
    navigateToStep(1, 2);
}

//Captures equipment choice and moves to Step 3
function selectEquipment(type) {
    userSelection.equipment = type;
    navigateToStep(2, 3);
}

//Submits the complete payload to FastAPI
async function generateWorkout() {
    //Read the values from the dropdown selects
    userSelection.days_per_week = parseInt(document.getElementById('days').value);
    userSelection.duration_mins = parseInt(document.getElementById('duration').value);

    const resultBox = document.getElementById('workout-result');
    resultBox.innerHTML = "⏳ Scanning database for routines...";
    navigateToStep(3, 4);

    try {
        //Send a POST request to local FastAPI server
        const response = await fetch('http://127.0.0.1:8000/recommend-workout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userSelection)
        });

        const data = await response.json();

        if (response.ok) {
            //Success: Display the workout routine text
            resultBox.innerText = data.routine;
        } else {
            //Handled Error (e.g. 404 No workout found)
            resultBox.innerHTML = `⚠️ <strong>Error:</strong> ${data.detail}`;
        }
    } catch (error) {
        //Server is offline error
        resultBox.innerHTML = "❌ Could not connect to the backend server. Make sure your FastAPI terminal is running!";
    }
}

//Simple layout switcher utility
function navigateToStep(currentStep, nextStep) {
    document.getElementById(`step-${currentStep}`).classList.remove('active');
    document.getElementById(`step-${nextStep}`).classList.add('active');
}

//Resets form back to step 1
function resetApp() {
    userSelection = { physique: "", equipment: "", days_per_week: 3, duration_mins: 60 };
    document.getElementById('step-4').classList.remove('active');
    document.getElementById('step-1').classList.add('active');
}