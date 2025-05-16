// OpenCoderRank/static/js/script.js

// CodeMirror editor instance
let codeMirrorEditor;
// Current question index (0-based) in the session's question_ids list
let currentQuestionIndex = 0;
// Timer interval ID for question timer
let questionTimerInterval;
// Start time for the current question (Unix timestamp in seconds)
let currentQuestionStartTime;
// Total questions in the current challenge
let totalQuestionsInChallenge = 0;
// Store current question's full data
let currentQuestionData = null;
// Store all question IDs and their statuses for QNP
let questionPanelData = [];


// --- Initialization ---
document.addEventListener('DOMContentLoaded', function() {
    // Initialize CodeMirror if the editor element exists
    const editorElement = document.getElementById('code-editor');
    if (editorElement) {
        codeMirrorEditor = CodeMirror.fromTextArea(editorElement, {
            lineNumbers: true,
            mode: "python", // Default mode, will be updated based on question
            theme: "material-darker",
            matchBrackets: true,
            autoCloseBrackets: true,
            extraKeys: {"Ctrl-Space": "autocomplete"},
            // Disable pasting by default
            onbeforepaste: function(cm, e) { e.preventDefault(); alert("Pasting code is disabled for this assessment."); }
        });
    }
    
    // Attach event listeners to buttons
    const runCodeBtn = document.getElementById('run-code-btn');
    if (runCodeBtn) runCodeBtn.addEventListener('click', runCode);

    const nextQuestionBtn = document.getElementById('next-question-btn');
    if (nextQuestionBtn) nextQuestionBtn.addEventListener('click', nextQuestion);
    
    const prevQuestionBtn = document.getElementById('prev-question-btn');
    if (prevQuestionBtn) prevQuestionBtn.addEventListener('click', previousQuestion);

    const finishTestBtn = document.getElementById('finish-test-btn');
    if (finishTestBtn) finishTestBtn.addEventListener('click', finishTest);

    const enterFullscreenBtn = document.getElementById('enter-fullscreen-btn');
    if(enterFullscreenBtn) enterFullscreenBtn.addEventListener('click', setupFullscreen);

    // Initial fetch of the first question if on test page
    if (document.getElementById('test-container')) {
        // The test container is initially hidden until fullscreen is entered
        // fetchQuestion(); // Moved to setupFullscreen
    }
    
    // Fullscreen change listener
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);
});

function setupFullscreen() {
    const elem = document.documentElement; // Fullscreen the whole page
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    } else if (elem.mozRequestFullScreen) { /* Firefox */
        elem.mozRequestFullScreen();
    } else if (elem.webkitRequestFullscreen) { /* Chrome, Safari & Opera */
        elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) { /* IE/Edge */
        elem.msRequestFullscreen();
    }
    document.getElementById('fullscreen-prompt').style.display = 'none';
    document.getElementById('test-container').style.display = 'block';
    fetchQuestion(); // Load the first question after entering fullscreen
}

function handleFullscreenChange() {
    if (!document.fullscreenElement && !document.webkitIsFullScreen && !document.mozFullScreen && !document.msFullscreenElement) {
        // Exited fullscreen
        if (document.getElementById('test-container').style.display === 'block' && 
            !document.getElementById('test-completed-message').style.display === 'block') {
            // If test is ongoing and not completed
            document.getElementById('test-container').style.display = 'none';
            document.getElementById('fullscreen-prompt').style.display = 'flex';
            alert("You have exited full-screen mode. Please re-enter to continue the test.");
            // Optionally pause timers or log this event
        }
    }
}


// --- Question Timer ---
function startQuestionTimer(timeLimitSeconds) {
    clearInterval(questionTimerInterval); // Clear any existing timer
    currentQuestionStartTime = Math.floor(Date.now() / 1000);
    const timerDisplay = document.getElementById('question-timer');
    const timeLimitDisplay = document.getElementById('time-limit');

    // Format and display time limit
    const limitMinutes = Math.floor(timeLimitSeconds / 60);
    const limitSeconds = timeLimitSeconds % 60;
    timeLimitDisplay.textContent = `${String(limitMinutes).padStart(2, '0')}:${String(limitSeconds).padStart(2, '0')}`;

    questionTimerInterval = setInterval(() => {
        const now = Math.floor(Date.now() / 1000);
        const elapsedSeconds = now - currentQuestionStartTime;
        
        const minutes = Math.floor(elapsedSeconds / 60);
        const seconds = elapsedSeconds % 60;
        if (timerDisplay) timerDisplay.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

        if (elapsedSeconds >= timeLimitSeconds) {
            // Optional: Auto-submit or show warning if time limit enforced by backend
            // For now, just visual
            timerDisplay.classList.add('text-danger');
        } else {
            timerDisplay.classList.remove('text-danger');
        }
    }, 1000);
}

// --- API Communication ---
function fetchQuestion() {
    fetch('/api/question')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error: ${data.error}`);
                if (data.error.includes("authenticated")) window.location.href = "/"; // Redirect if session issue
                return;
            }
            if (data.test_completed) {
                handleTestCompletion(data);
            } else {
                currentQuestionData = data; // Store the full question data
                updateQuestionDisplay(data);
                questionPanelData = data.qnp_data || [];
                updateQuestionNavigationPanel();
                totalQuestionsInChallenge = data.total_questions;
                currentQuestionIndex = data.current_q_num -1; // Server sends 1-based, JS uses 0-based
            }
        })
        .catch(error => {
            console.error('Error fetching question:', error);
            document.getElementById('question-title').textContent = 'Error loading question.';
        });
}

function runCode() {
    const runCodeBtn = document.getElementById('run-code-btn');
    runCodeBtn.disabled = true; // Disable button during processing
    runCodeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Evaluating...';

    let submissionData;
    if (currentQuestionData.language === 'mcq') {
        const selectedOption = document.querySelector('input[name="mcq_option"]:checked');
        if (!selectedOption) {
            alert("Please select an answer.");
            runCodeBtn.disabled = false;
            runCodeBtn.textContent = currentQuestionData.language === 'mcq' ? 'Submit Answer' : 'Run Code';
            return;
        }
        submissionData = selectedOption.value; // This is the index
    } else {
        submissionData = codeMirrorEditor.getValue();
    }

    fetch('/api/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: submissionData, question_id: currentQuestionData.id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Evaluation Error: ${data.error}`);
            document.getElementById('output-area').innerHTML = `<p class="text-danger">${data.error}</p>`;
        } else {
            document.getElementById('output-area').innerHTML = data.output || '<p class="text-muted">No output received.</p>';
            if (data.new_score !== undefined) {
                document.getElementById('nav-score').textContent = `Score: ${data.new_score}`;
            }
            // Update QNP with data from evaluation response
            if (data.qnp_data) {
                questionPanelData = data.qnp_data;
                updateQuestionNavigationPanel();
            }
        }
    })
    .catch(error => {
        console.error('Error evaluating code:', error);
        document.getElementById('output-area').innerHTML = '<p class="text-danger">An unexpected error occurred during evaluation.</p>';
    })
    .finally(() => {
        runCodeBtn.disabled = false;
        runCodeBtn.textContent = currentQuestionData.language === 'mcq' ? 'Submit Answer' : 'Run Code';
    });
}

function navigateViaApi(endpoint, successCallback) {
    fetch(endpoint, { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else if (data.test_completed) {
            handleTestCompletion(data);
        } else if (data.navigated || data.next_question_loaded || data.jumped) {
            currentQuestionIndex = data.new_idx; // Server returns new index
            fetchQuestion(); // Fetch the new current question
            if(successCallback) successCallback();
        } else {
            alert(data.message || "Could not navigate.");
        }
    })
    .catch(error => console.error('Navigation error:', error));
}

function previousQuestion() {
    if (currentQuestionIndex > 0) { // Client-side check before API call
        navigateViaApi('/api/previous_question');
    } else {
        alert("Already at the first question.");
    }
}

function nextQuestion() {
    // No client-side check for last question here, server handles completion
    navigateViaApi('/api/next_question');
}

function jumpToQuestion(qSessionIndex) {
    fetch('/api/jump_to_question', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ index: qSessionIndex })
    })
    .then(response => response.json())
    .then(data => {
        if (data.jumped) {
            currentQuestionIndex = data.new_idx;
            fetchQuestion();
        } else {
            alert(data.message || "Failed to jump to question.");
        }
    })
    .catch(error => console.error('Error jumping to question:', error));
}

function finishTest() {
    if (confirm("Are you sure you want to finish the test?")) {
        // The 'nextQuestion' API handles finalization if it's effectively the last question or beyond
        // A dedicated '/api/finish_test' could be made, but for now, let's use next logic.
        // To force finish, we could set currentQuestionIndex to totalQuestions and call nextQuestion.
        // Or, better, current `next_question_api` when called and idx >= len(ids) correctly finishes.
        // So we need a way to tell it to go past the last question.
        // Simpler: just use nextQuestion. If it's the last, it'll complete.
        // If not last, user chose to finish early.
        // To *actually* submit the score as is:
        fetch('/api/next_question', { // Call next_question to force submission even if not last
             method: 'POST',
             // Send a flag to indicate forced finish, or have server treat any call to next_question beyond last as finish
             // For simplicity, let's assume the current next_question logic for `current_idx >= len(question_ids)`
             // will be triggered if we artificially set currentQuestionIndex to be len(question_ids)
             // This requires sending the current state and forcing session update.
             // The existing POST to /api/next_question relies on session's current_question_idx.
             // A more direct way:
        })
        .then(res => res.json())
        .then(data => {
            if (data.test_completed) {
                handleTestCompletion(data);
            } else {
                // This scenario (not completed after finish click) should ideally not happen if server is robust.
                // Potentially show an error or force redirect.
                alert("Finishing... If not redirected, please wait or refresh.");
                // To force submission, an actual /api/finalize_test would be cleaner.
                // For now, let's make it call nextQuestion until it is completed.
                // This is a bit of a hack. A dedicated API endpoint would be better.
                // Let's assume the existing "Next Question" handles test completion properly.
                // If user clicks Finish when on Q3 of 10, they forfeit remaining.
                // The current /api/next_question, if it knows it's the *last* action:
                // Server's /api/next_question, if current_idx +=1 results in current_idx >= len(question_ids), then it finalizes.
                // This will work.
                handleTestCompletion(data); // Assuming it comes back with test_completed details
            }
        })
        .catch(error => console.error('Error finishing test:', error));
    }
}


// --- UI Updates ---
function updateQuestionDisplay(data) {
    document.getElementById('question-title').textContent = data.title || "No Title";
    document.getElementById('question-progress').textContent = `${data.current_q_num} / ${data.total_questions}`;
    document.getElementById('question-level').textContent = data.level || "N/A";
    document.getElementById('question-language').textContent = data.language.toUpperCase() || "N/A";
    document.getElementById('question-description').innerHTML = data.description || "No description available."; // Use innerHTML if description contains HTML

    // Remarks display
    const remarksContainer = document.getElementById('question-remarks-container');
    const remarksElement = document.getElementById('question-remarks');
    if (data.remarks) {
        remarksElement.textContent = data.remarks;
        remarksContainer.style.display = 'block';
    } else {
        remarksContainer.style.display = 'none';
    }
    
    // Adjust UI for question type
    const codeEditorDiv = document.getElementById('code-editor-container');
    const mcqOptionsDiv = document.getElementById('mcq-options-container');
    const sqlSchemaDiv = document.getElementById('sql-schema-container');
    const runCodeBtn = document.getElementById('run-code-btn');

    // Hide all optional sections first
    if (codeEditorDiv) codeEditorDiv.style.display = 'none';
    if (mcqOptionsDiv) mcqOptionsDiv.style.display = 'none';
    if (sqlSchemaDiv) sqlSchemaDiv.style.display = 'none';

    if (data.language === 'sql') {
        if (codeEditorDiv && codeMirrorEditor) {
            codeEditorDiv.style.display = 'block';
            codeMirrorEditor.setOption("mode", "text/x-sql");
            codeMirrorEditor.setValue(data.starter_query || ""); // Use starter_query if available
        }
        if (sqlSchemaDiv && data.schema) {
            document.getElementById('schema-details').textContent = data.schema;
            sqlSchemaDiv.style.display = 'block';
        }
        runCodeBtn.textContent = 'Run Query';
    } else if (data.language === 'python') {
        if (codeEditorDiv && codeMirrorEditor) {
            codeEditorDiv.style.display = 'block';
            codeMirrorEditor.setOption("mode", "python");
            codeMirrorEditor.setValue(data.starter_code || "");
        }
        runCodeBtn.textContent = 'Run Code';
    } else if (data.language === 'mcq') {
        if (mcqOptionsDiv) {
            mcqOptionsDiv.style.display = 'block';
            mcqOptionsDiv.innerHTML = '<h5>Select your answer:</h5>'; // Reset previous options
            data.options.forEach((option, index) => {
                const optionId = `mcq_option_${index}`;
                const div = document.createElement('div');
                div.className = 'mcq-option form-check'; // Bootstrap styling for check
                div.innerHTML = `
                    <input class="form-check-input" type="radio" name="mcq_option" id="${optionId}" value="${index}">
                    <label class="form-check-label" for="${optionId}">${option}</label>
                `;
                mcqOptionsDiv.appendChild(div);
            });
        }
        runCodeBtn.textContent = 'Submit Answer';
    }
    
    if (codeMirrorEditor) codeMirrorEditor.refresh(); // Refresh editor in case its container was hidden/shown

    // Update progress bar
    const progressBar = document.getElementById('test-progress-bar');
    const progressPercent = (data.current_q_num / data.total_questions) * 100;
    progressBar.style.width = `${progressPercent}%`;
    progressBar.setAttribute('aria-valuenow', progressPercent);
    
    // Timer
    startQuestionTimer(data.time_limit_seconds);
    document.getElementById('output-area').innerHTML = '<p class="text-muted">Output will appear here.</p>'; // Clear previous output

    // Button visibility
    document.getElementById('prev-question-btn').style.display = (data.current_q_num > 1) ? 'inline-block' : 'none';
    // 'Next Question' changes to 'Finish Test' on the last question IF we want that behavior.
    // For now, Next always Next, Finish is separate.
    // The finish button could appear on the last question, or be always available (after 1st q?).
    const finishBtn = document.getElementById('finish-test-btn');
    if (data.current_q_num >= data.total_questions) { // Show finish on last question.
         document.getElementById('next-question-btn').style.display = 'none'; // Hide next on last q
         finishBtn.style.display = 'inline-block';
    } else {
         document.getElementById('next-question-btn').style.display = 'inline-block';
         finishBtn.style.display = 'none'; // Hide finish unless on last q
    }
    // Or, always show finish test button:
    // finishBtn.style.display = 'inline-block';

    updateQuestionNavigationPanel(); // Update highlights for current question
}

function updateQuestionNavigationPanel() {
    const panel = document.getElementById('question-navigation-panel');
    if (!panel || !questionPanelData) return;
    
    panel.innerHTML = ''; // Clear previous items

    if (questionPanelData.length === 0) {
        panel.innerHTML = '<p class="text-muted">No questions loaded for panel.</p>';
        return;
    }

    questionPanelData.forEach((q_status_item, index) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = index + 1;
        btn.classList.add('qnp-item', `qnp-${q_status_item.status.toLowerCase()}`);
        if (index === currentQuestionIndex) {
            btn.classList.add('qnp-current');
        }
        btn.setAttribute('data-qindex', index); // Store 0-based session index
        btn.addEventListener('click', () => jumpToQuestion(index));
        panel.appendChild(btn);
    });
}


function handleTestCompletion(data) {
    clearInterval(questionTimerInterval); // Stop any running timers
    document.getElementById('test-container').style.display = 'none';
    const completionMessageDiv = document.getElementById('test-completed-message');
    completionMessageDiv.style.display = 'block';

    document.getElementById('completed-challenge-name').textContent = currentQuestionData ? currentQuestionData.challenge_name : "N/A";
    document.getElementById('final-score').textContent = data.score;
    document.getElementById('total-time-taken').textContent = `${data.total_time} seconds`;

    const scoreboardLink = document.getElementById('view-challenge-scoreboard-link');
    if (data.challenge_id) {
        // SCOREBOARD_BASE_URL should come from test.html template global JS var.
        // It's the URL for the list page, we need to append the specific challenge ID.
        scoreboardLink.href = `${SCOREBOARD_BASE_URL.replace('/scoreboards', '')}/scoreboard/${data.challenge_id}`;
    } else {
        scoreboardLink.href = SCOREBOARD_BASE_URL; // Fallback to generic scoreboards list
    }

    // Optional: Display final QNP summary on completion page
    if (data.qnp_data) {
        questionPanelData = data.qnp_data; // Update with final status
        const finalQnpContainer = document.getElementById('final-qnp-summary');
        if (finalQnpContainer) {
            finalQnpContainer.innerHTML = '<h5>Test Summary:</h5><div id="final-qnp-items" class="question-navigation-panel"></div>';
            const finalQnpItemsDiv = document.getElementById('final-qnp-items');
            questionPanelData.forEach((q_status_item, index) => {
                const span = document.createElement('span');
                span.textContent = index + 1;
                span.classList.add('qnp-item', `qnp-${q_status_item.status.toLowerCase()}`);
                finalQnpItemsDiv.appendChild(span);
            });
        }
    }
}