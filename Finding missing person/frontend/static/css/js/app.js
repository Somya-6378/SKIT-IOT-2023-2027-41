
function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = "message " + type;
}

function isValidImage(file) {
    const allowedTypes = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ];

    return file && allowedTypes.includes(file.type);
}


// LOGIN PAGE
const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", function(event) {
        event.preventDefault();

        showMessage(
            "loginMessage",
            "Login API is not connected yet. Authentication will be added next.",
            "error"
        );
    });
}


// REGISTER CASE PAGE
const caseForm = document.getElementById("caseForm");

if (caseForm) {
    caseForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const button = document.getElementById("caseButton");
        const file = document.getElementById("personPhoto").files[0];

        if (!isValidImage(file)) {
            showMessage(
                "caseMessage",
                "Please upload a valid JPG, PNG or WEBP image.",
                "error"
            );
            return;
        }

        button.disabled = true;
        button.textContent = "Uploading...";

        try {
            const caseData = {
                case_number: document.getElementById("caseNumber").value.trim(),
                person_name: document.getElementById("personName").value.trim(),
                age_years: document.getElementById("age").value || null,
                gender: document.getElementById("gender").value,
                description: document.getElementById("description").value,
                last_seen_location: document.getElementById("location").value,
                last_seen_at: document.getElementById("lastSeen").value || null
            };

            const caseResponse = await fetch("/api/cases", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(caseData)
            });

            const caseResult = await caseResponse.json();

            if (!caseResponse.ok) {
                throw new Error(caseResult.error || "Case creation failed");
            }

            const formData = new FormData();
            formData.append("photo", file);

            const photoResponse = await fetch(
                `/api/cases/${caseResult.case.case_id}/photos`,
                {
                    method: "POST",
                    body: formData
                }
            );

            const photoResult = await photoResponse.json();

            if (!photoResponse.ok) {
                throw new Error(
                    photoResult.error || "Photo upload failed"
                );
            }

            showMessage(
                "caseMessage",
                "Case and photo uploaded successfully. Case ID: " +
                    caseResult.case.case_id,
                "success"
            );

            caseForm.reset();

        } catch (error) {
            showMessage("caseMessage", error.message, "error");
        } finally {
            button.disabled = false;
            button.textContent = "Submit Case";
        }
    });
}


// SEARCH PAGE
const searchForm = document.getElementById("searchForm");

if (searchForm) {
    searchForm.addEventListener("submit", function(event) {
        event.preventDefault();

        const file = document.getElementById("searchPhoto").files[0];

        if (!isValidImage(file)) {
            showMessage(
                "searchMessage",
                "Please upload a valid JPG, PNG or WEBP image.",
                "error"
            );
            return;
        }

        showMessage(
            "searchMessage",
            "Image selected successfully. Search upload API is not connected yet.",
            "error"
        );
    });
}


// REVIEW MATCHES PAGE
const loadButton = document.getElementById("loadMatchesButton");

if (loadButton) {
    loadButton.addEventListener("click", loadMatches);
}

async function loadMatches() {
    const searchId = document.getElementById("searchId").value;
    const button = document.getElementById("loadMatchesButton");
    const list = document.getElementById("matchesList");

    if (!searchId || Number(searchId) <= 0) {
        showMessage("reviewMessage", "Enter a valid Search ID.", "error");
        return;
    }

    button.disabled = true;
    button.textContent = "Loading...";
    list.innerHTML = "";

    try {
        const response = await fetch(
            `/api/searches/${encodeURIComponent(searchId)}/matches`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to load candidates");
        }

        if (!data.matches || data.matches.length === 0) {
            showMessage(
                "reviewMessage",
                "No possible match found.",
                "error"
            );
            return;
        }

        showMessage(
            "reviewMessage",
            "Possible candidates found. Reviewer verification required.",
            "success"
        );

        data.matches.forEach(match => {
            const card = document.createElement("div");
            card.className = "candidate";

            const heading = document.createElement("h3");
            heading.textContent = "Case ID: " + match.case_id;

            const score = document.createElement("p");
            score.textContent = "Demo score: " +
                (match.demo_score ?? "Not available");

            const status = document.createElement("p");
            status.textContent = "Decision: " + match.decision;

            const note = document.createElement("p");
            note.textContent =
                "Possible candidate — reviewer verification required.";

            const select = document.createElement("select");
            select.innerHTML = `
                <option value="">Select decision</option>
                <option value="potential_match">Potential Match</option>
                <option value="not_a_match">Not a Match</option>
                <option value="verified_match">Verified Match</option>
            `;

            const reviewNote = document.createElement("input");
            reviewNote.placeholder = "Review notes";

            const submit = document.createElement("button");
            submit.textContent = "Save Review";

            submit.addEventListener("click", async () => {
                const decision = select.value;

                if (!decision) {
                    alert("Please select a review decision.");
                    return;
                }

                const reviewerId = prompt(
                    "Enter demo reviewer user ID:"
                );

                if (!reviewerId || !/^\d+$/.test(reviewerId)) {
                    alert("Enter a valid reviewer ID.");
                    return;
                }

                submit.disabled = true;

                try {
                    const reviewResponse = await fetch(
                        `/api/matches/${match.review_id}/review`,
                        {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({
                                reviewer_id: Number(reviewerId),
                                decision: decision,
                                review_notes: reviewNote.value
                            })
                        }
                    );

                    const result = await reviewResponse.json();

                    if (!reviewResponse.ok) {
                        throw new Error(
                            result.error || "Review could not be saved"
                        );
                    }

                    status.textContent = "Decision: " + result.decision;
                    submit.textContent = "Review Saved";
                    select.disabled = true;
                    reviewNote.disabled = true;

                    showMessage(
                        "reviewMessage",
                        "Review saved successfully.",
                        "success"
                    );

                } catch (error) {
                    alert(error.message);
                    submit.disabled = false;
                }
            });

            card.append(heading, score, status, note,
                        select, reviewNote, submit);

            list.appendChild(card);
        });

    } catch (error) {
        showMessage("reviewMessage", error.message, "error");
    } finally {
        button.disabled = false;
        button.textContent = "Load Candidates";
    }
}
