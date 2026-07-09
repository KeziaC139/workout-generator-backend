/**
 * Name: Kezia Chacko
 * Program: History Page Engine (history.js)
 * Sorts and groups workout logs into clean day-by-day tables with robust error tracking.
 */

function initializeHistoryPage() {
    const activeUser = sessionStorage.getItem("workout_app_user");

    if (!activeUser) {
        alert("No active secure session found. Please log in on the main dashboard portal.");
        window.location.href = "index.html";
        return;
    }

    document.getElementById("history-user-target").innerText = activeUser;
    fetchGroupedWorkoutHistory(activeUser);
}

async function fetchGroupedWorkoutHistory(username) {
    const wrapper = document.getElementById("history-days-wrapper");

    try {
        const response = await fetch(`http://127.0.0.1:8000/workout-history/${username}/`);

        // Catch server response errors (like 500 Internal Error or 404 Not Found)
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(`Server returned status ${response.status}: ${errData.detail || 'Unknown internal error'}`);
        }

        const data = await response.json();

        if (data.status !== "success" || !data.history || data.history.length === 0) {
            wrapper.innerHTML = `<p style="color: #666; text-align: center; padding: 40px;">No logged training logs found for account: <strong>${username}</strong> yet.</p>`;
            return;
        }

        const daysMap = {};

        data.history.forEach(row => {
            // Guard clause: Handle empty, missing, or malformed database dates gracefully
            let dateSource = row.date;
            if (!dateSource) {
                dateSource = new Date(); // Fallback to current time if database date is missing
            }

            const dateObj = new Date(dateSource);
            let calendarDay = dateObj.toLocaleDateString(undefined, {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            // If the date string was completely broken or unparseable
            if (calendarDay === "Invalid Date") {
                calendarDay = "Archived Unscheduled Workouts";
            }

            if (!daysMap[calendarDay]) {
                daysMap[calendarDay] = [];
            }
            daysMap[calendarDay].push(row);
        });

        // Clear loading placeholders
        wrapper.innerHTML = "";

        // Render out tables
        for (const [dayString, setsList] of Object.entries(daysMap)) {
            let dayHtml = `
                <div class="day-block">
                    <h3 class="day-header">
                        <span>📅 ${dayString}</span>
                        <span style="font-size:0.9rem; color:#888;">${setsList.length} Total Sets Logged</span>
                    </h3>
                    <div style="overflow-x: auto; width: 100%;">
                        <table style="width: 100%; border-collapse: collapse; text-align: left; background: #1a1a1a; border-radius: 8px; overflow: hidden;">
                            <thead>
                                <tr style="background: #262626; color: #bc13fe; border-bottom: 2px solid #333;">
                                    <th style="padding: 12px; width: 50%;">Exercise Movement</th>
                                    <th style="padding: 12px; text-align:center; width: 15%;">Set</th>
                                    <th style="padding: 12px; text-align:center; width: 20%;">Load</th>
                                    <th style="padding: 12px; text-align:center; width: 15%;">Reps</th>
                                </tr>
                            </thead>
                            <tbody>
            `;

            setsList.forEach(set => {
                dayHtml += `
                    <tr style="border-bottom: 1px solid #262626;">
                        <td style="padding: 12px; font-weight: bold; color: #fff;">${set.exercise_name}</td>
                        <td style="padding: 12px; color: #bc13fe; text-align:center; font-weight:bold;">${set.set_number}</td>
                        <td style="padding: 12px; color: #00ff87; text-align:center;">${set.weight_lbs} lbs</td>
                        <td style="padding: 12px; color: #00e5ff; text-align:center;">${set.reps_performed}</td>
                    </tr>
                `;
            });

            dayHtml += `</tbody></table></div></div>`;
            wrapper.insertAdjacentHTML("beforeend", dayHtml);
        }

    } catch (error) {
        console.error("Detailed diagnostic logs:", error);
        wrapper.innerHTML = `
            <div style="background: #2a1111; border: 1px solid #ff4a4a; padding: 20px; border-radius: 8px; text-align: left;">
                <h3 style="color: #ff4a4a; margin-top: 0;">Ledger Initialization Interrupted ⚠️</h3>
                <p style="color: #bbb; font-size: 0.95rem;">The app hit a wall while loading your database history records.</p>
                <code style="background: #111; color: #ff8888; display: block; padding: 10px; border-radius: 4px; font-family: monospace;">
                    Error Details: ${error.message}
                </code>
                <p style="color: #888; font-size: 0.85rem; margin-bottom: 0; margin-top: 15px;">
                    💡 Troubleshooting: Ensure your terminal says "Uvicorn running on http://127.0.0.1:8000" right now.
                </p>
            </div>
        `;
    }
}