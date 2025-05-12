// static/js/script.js
document.addEventListener('DOMContentLoaded', () => {
    const testContainer = document.getElementById('test-container');
    const fullscreenPrompt = document.getElementById('fullscreen-prompt');
    const enterFullscreenBtn = document.getElementById('enter-fullscreen-btn');

    const questionTitleEl = document.getElementById('question-title');
    const questionProgressEl = document.getElementById('question-progress');
    const questionTimerEl = document.getElementById('question-timer');
    const timeLimitEl = document.getElementById('time-limit');
    const currentChallengeNameEl = document.getElementById('current-challenge-name'); // Already in HTML, might not need JS update if static
    const questionLevelEl = document.getElementById('question-level');
    const questionLanguageEl = document.getElementById('question-language');
    const testProgressBar = document.getElementById('test-progress-bar');
    const questionDescriptionEl = document.getElementById('question-description');
    const sqlSchemaContainer = document.getElementById('sql-schema-container');
    const schemaDetailsEl = document.getElementById('schema-details');
    const codeEditorEl = document.getElementById('code-editor');
    const outputArea = document.getElementById('output-area');
    
    const runCodeBtn = document.getElementById('run-code-btn');
    const prevQuestionBtn = document.getElementById('prev-question-btn');
    const nextQuestionBtn = document.getElementById('next-question-btn');
    // const finishTestBtn = document.getElementById('finish-test-btn'); // For potential future use

    const testCompletedMessageEl = document.getElementById('test-completed-message');
    const completedChallengeNameEl = document.getElementById('completed-challenge-name');
    const finalScoreEl = document.getElementById('final-score');
    const totalTimeTakenEl = document.getElementById('total-time-taken');
    const viewChallengeScoreboardLink = document.getElementById('view-challenge-scoreboard-link');
    const navScoreEl = document.getElementById('nav-score');


    let codemirrorEditor;
    let currentQuestionData = null;
    let questionInterval; // For question timer

    // --- Full-Screen Management ---
    function requestFullScreen(element) {
        if (element.requestFullscreen) {
            element.requestFullscreen();
        } else if (element.mozRequestFullScreen) { /* Firefox */
            element.mozRequestFullScreen();
        } else if (element.webkitRequestFullscreen) { /* Chrome, Safari & Opera */
            element.webkitRequestFullscreen();
        } else if (element.msRequestFullscreen) { /* IE/Edge */
            element.msRequestFullscreen();
        }
    }

    function exitFullScreen() {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
    }
    
    function checkFullScreen() {
        return document.fullscreenElement || document.mozFullScreenElement || document.webkitFullscreenElement || document.msFullscreenElement;
    }

    if (enterFullscreenBtn) {
        enterFullscreenBtn.addEventListener('click', () => {
            requestFullScreen(document.documentElement);
        });
    }

    document.addEventListener('fullscreenchange', () => {
        if (checkFullScreen()) {
            if (fullscreenPrompt) fullscreenPrompt.style.display = 'none';
            if (testContainer) testContainer.style.display = 'block';
            if (!currentQuestionData) { // Load first question only after entering fullscreen
                 loadQuestion();
            }
        } else {
            // User exited full-screen. Optionally, pause test or show prompt again.
            // For simplicity, we'll just allow it for now, but a stricter system could re-prompt or end test.
            // if (fullscreenPrompt) fullscreenPrompt.style.display = 'flex';
            // if (testContainer) testContainer.style.display = 'none';
            // alert("Full-screen mode is required. Please re-enter full-screen to continue.");
        }
    });
    
    // --- CodeMirror Initialization ---
    function initializeCodeMirror(language, starterCode) {
        if (codemirrorEditor) {
            codemirrorEditor.toTextArea(); // Clean up previous instance
        }
        codeEditorEl.value = starterCode || '';
        codemirrorEditor = CodeMirror.fromTextArea(codeEditorEl, {
            lineNumbers: true,
            mode: language === 'sql' ? 'text/x-sql' : 'python',
            theme: 'material-darker',
            matchBrackets: true,
            autoCloseBrackets: true,
            // Disabling paste
            onKeyEvent: function(editor, e) { // A way to catch paste, not perfect for all scenarios
                if ((e.ctrlKey || e.metaKey) && e.keyCode == 86) { // Ctrl+V or Cmd+V
                    e.preventDefault();
                    return true; // Mark as handled
                }
            }
        });
        // More robust paste prevention
        codemirrorEditor.on('paste', function(cm, e) {
            e.preventDefault();
            alert("Pasting code is disabled for this assessment.");
        });
    }

    // --- Timer ---
    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }

    function startQuestionTimer(limitSeconds) {
        clearInterval(questionInterval);
        let timeLeft = limitSeconds;
        let timeElapsed = 0;

        function updateDisplay() {
            if (timeLimitEl) timeLimitEl.textContent = formatTime(timeLeft);
            if (questionTimerEl) questionTimerEl.textContent = formatTime(timeElapsed); // Show elapsed time
        }
        updateDisplay(); // Initial display

        questionInterval = setInterval(() => {
            timeLeft--;
            timeElapsed++;
            updateDisplay();
            if (timeLeft <= 0) {
                clearInterval(questionInterval);
                // Handle time up (e.g., auto-submit or notify)
                // For now, just stops timer visually
            }
        }, 1000);
    }


    // --- Load Question ---
    async function loadQuestion() {
        try {
            const response = await fetch('/api/question');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();

            if (data.error) {
                alert(`Error loading question: ${data.error}`);
                window.location.href = '/'; // Redirect to home
                return;
            }

            if (data.test_completed) {
                displayTestCompletion(data);
                return;
            }
            
            currentQuestionData = data;
            updateUIForNewQuestion(data);

        } catch (error) {
            console.error('Failed to load question:', error);
            alert('Failed to load question. Please try refreshing or restarting the test.');
        }
    }

    function updateUIForNewQuestion(data) {
        if (questionTitleEl) questionTitleEl.textContent = data.title;
        if (questionProgressEl) questionProgressEl.textContent = `${data.current_q_num} / ${data.total_questions}`;
        if (questionLevelEl) questionLevelEl.textContent = data.level;
        if (questionLanguageEl) questionLanguageEl.textContent = data.language.toUpperCase();
        if (questionDescriptionEl) questionDescriptionEl.innerHTML = data.description; // Use innerHTML if description can contain HTML

        if (navScoreEl) navScoreEl.textContent = `Score: ${data.user_score}`;

        if (data.language === 'sql' && data.schema) {
            if (sqlSchemaContainer) sqlSchemaContainer.style.display = 'block';
            if (schemaDetailsEl) schemaDetailsEl.textContent = data.schema;
        } else {
            if (sqlSchemaContainer) sqlSchemaContainer.style.display = 'none';
        }

        initializeCodeMirror(data.language, data.starter_code || '');
        startQuestionTimer(data.time_limit_seconds);
        clearOutputArea();

        // Update progress bar
        const progressPercent = (data.current_q_num / data.total_questions) * 100;
        if (testProgressBar) {
            testProgressBar.style.width = `${progressPercent}%`;
            testProgressBar.setAttribute('aria-valuenow', progressPercent);
        }
        
        // Manage button visibility and text
        if (prevQuestionBtn) {
            prevQuestionBtn.style.display = (data.current_q_num > 1) ? 'inline-block' : 'none';
        }

        if (nextQuestionBtn) {
            if (data.current_q_num <= data.total_questions) { // Show if not beyond last question
                nextQuestionBtn.style.display = 'inline-block';
                nextQuestionBtn.textContent = (data.current_q_num === data.total_questions) ? 'Finish Test & View Score' : 'Next Question';
            } else {
                 nextQuestionBtn.style.display = 'none'; // Should be handled by test_completed
            }
        }
         if (runCodeBtn) runCodeBtn.disabled = false;
    }

    function clearOutputArea() {
        if (outputArea) outputArea.innerHTML = '<p class="text-muted">Run your code to see the output here.</p>';
    }
    
    // --- Event Listeners for Buttons ---
    if (runCodeBtn) {
        runCodeBtn.addEventListener('click', async () => {
            if (!codemirrorEditor || !currentQuestionData) return;
            
            const code = codemirrorEditor.getValue();
            outputArea.innerHTML = '<p class="text-info">Evaluating your code...</p>';
            runCodeBtn.disabled = true;

            try {
                const response = await fetch('/api/evaluate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: code, question_id: currentQuestionData.id })
                });
                const result = await response.json();

                if (result.error) {
                    outputArea.innerHTML = `<p class="text-danger">Error: ${result.error}</p>`;
                } else {
                    outputArea.innerHTML = result.output || '<p class="text-muted">No output produced.</p>';
                    if (result.new_score !== undefined && navScoreEl) {
                         navScoreEl.textContent = `Score: ${result.new_score}`;
                    }
                     if (result.status === "already_correct" || result.passed_all_tests) {
                        // Optionally disable run button or show "Correct" persistently
                    }
                }
            } catch (error) {
                console.error('Error evaluating code:', error);
                outputArea.innerHTML = '<p class="text-danger">An error occurred during evaluation.</p>';
            } finally {
                runCodeBtn.disabled = false;
            }
        });
    }

    if (prevQuestionBtn) {
        prevQuestionBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/previous_question', { method: 'POST' });
                const data = await response.json();
                if (data.navigated) {
                    loadQuestion();
                } else if (data.message) {
                    // alert(data.message); // e.g., "Already at first question"
                    // Button should be hidden anyway by loadQuestion logic
                }
            } catch (error) {
                console.error('Error navigating to previous question:', error);
                alert('Failed to go to previous question.');
            }
        });
    }

    if (nextQuestionBtn) {
        nextQuestionBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/next_question', { method: 'POST' });
                const data = await response.json();

                if (data.test_completed) {
                    displayTestCompletion(data);
                } else if (data.next_question_loaded) {
                    loadQuestion();
                } else if (data.error){
                     alert(`Error: ${data.error}`);
                }
            } catch (error) {
                console.error('Error navigating to next question:', error);
                alert('Failed to go to next question.');
            }
        });
    }

    function displayTestCompletion(data) {
        clearInterval(questionInterval); // Stop any running timers
        if (testContainer) testContainer.style.display = 'none';
        if (testCompletedMessageEl) testCompletedMessageEl.style.display = 'block';

        if (completedChallengeNameEl && currentQuestionData) completedChallengeNameEl.textContent = currentQuestionData.challenge_name;
        else if (completedChallengeNameEl && data.challenge_id && CHALLENGES[data.challenge_id]) completedChallengeNameEl.textContent = CHALLENGES[data.challenge_id].name;


        if (finalScoreEl) finalScoreEl.textContent = data.score;
        if (totalTimeTakenEl) totalTimeTakenEl.textContent = `${data.total_time} seconds`;
        
        if (viewChallengeScoreboardLink && data.challenge_id) {
            viewChallengeScoreboardLink.href = SCOREBOARD_BASE_URL;
        } else if (viewChallengeScoreboardLink) {
            viewChallengeScoreboardLink.href = SCOREBOARD_BASE_URL; // Fallback
        }
        // Also update navbar score one last time
        if (navScoreEl) navScoreEl.textContent = `Score: ${data.score}`;
    }

    // --- Initial Load ---
    // Load first question only if testContainer is visible (i.e. after fullscreen prompt)
    // This is now handled by the fullscreenchange event listener.
    // If no fullscreen prompt, uncomment:
    // if (testContainer && testContainer.style.display !== 'none') {
    //     loadQuestion();
    // }

    // This `CHALLENGES` object would be needed if `displayTestCompletion` relied on it client-side
    // For now, it's not strictly necessary as challenge name comes from currentQuestionData or backend.
    // const CHALLENGES = { ... }; // If needed, pass from Flask template context
});