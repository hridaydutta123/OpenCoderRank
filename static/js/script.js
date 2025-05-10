// coding_platform_flask/static/js/script.js

// Function to attempt entering full-screen mode
function enterFullScreen() {
    const elem = document.documentElement; 
    if (elem.requestFullscreen) {
        elem.requestFullscreen().catch(err => {
            console.warn(`Warning: Could not enter full-screen mode: ${err.message}. Some browsers require a direct user interaction on the page (e.g., a click) for this to work automatically.`);
        });
    } else if (elem.mozRequestFullScreen) { /* Firefox */
        elem.mozRequestFullScreen().catch(err => { console.warn(`Warning (Firefox): Could not enter full-screen mode: ${err.message}.`); });
    } else if (elem.webkitRequestFullscreen) { /* Chrome, Safari & Opera */
        elem.webkitRequestFullscreen().catch(err => { console.warn(`Warning (WebKit): Could not enter full-screen mode: ${err.message}.`); });
    } else if (elem.msRequestFullscreen) { /* IE/Edge */
        elem.msRequestFullscreen().catch(err => { console.warn(`Warning (IE/Edge): Could not enter full-screen mode: ${err.message}.`); });
    }
}


document.addEventListener('DOMContentLoaded', function() {
    const codeEditorElement = document.getElementById('code-editor');
    let editor; 
    let currentQuestion = null;
    let questionTimerInterval;

    if (document.getElementById('test-container')) { 
        enterFullScreen(); 

        const testContainer = document.getElementById('test-container');
        const fullscreenNote = document.createElement('div');
        fullscreenNote.id = 'fullscreen-note';
        fullscreenNote.className = 'alert alert-primary alert-dismissible fade show mt-2'; 
        fullscreenNote.style.position = 'fixed'; 
        fullscreenNote.style.top = '60px'; 
        fullscreenNote.style.left = '50%';
        fullscreenNote.style.transform = 'translateX(-50%)';
        fullscreenNote.style.zIndex = '2000'; 
        fullscreenNote.style.maxWidth = '80%';
        fullscreenNote.setAttribute('role', 'alert');
        fullscreenNote.innerHTML = `
            You are in full-screen mode. Press <strong>Esc</strong> key to exit.
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.insertBefore(fullscreenNote, document.body.firstChild);
        
        if (codeEditorElement) {
            editor = CodeMirror.fromTextArea(codeEditorElement, {
                mode: "python", 
                theme: "material-darker",
                lineNumbers: true,
                autoCloseBrackets: true,
                matchBrackets: true,
            });

            editor.on('paste', function(instance, event) {
                event.preventDefault(); 

                let pasteWarning = document.getElementById('paste-warning-message');
                if (!pasteWarning) {
                    pasteWarning = document.createElement('div');
                    pasteWarning.id = 'paste-warning-message';
                    pasteWarning.className = 'text-danger small mb-1'; 
                    pasteWarning.style.textAlign = 'center';
                    pasteWarning.style.fontWeight = 'bold';
                    editor.getWrapperElement().parentNode.insertBefore(pasteWarning, editor.getWrapperElement());
                }
                pasteWarning.textContent = 'Pasting code is disabled for this test.';
                setTimeout(() => {
                    if (pasteWarning) pasteWarning.textContent = ''; 
                }, 3000);
            });
        }
        
        loadQuestion();

        document.getElementById('run-code-btn').addEventListener('click', () => {
            if (!editor) {
                console.error("Editor not initialized.");
                return;
            }
            const userCode = editor.getValue();
            if (!currentQuestion) return;

            document.getElementById('output-area').innerHTML = '<p class="text-info">Evaluating your code...</p>';
            document.getElementById('run-code-btn').disabled = true;

            fetch('/api/evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: userCode, question_id: currentQuestion.id })
            })
            .then(response => response.json())
            .then(result => {
                document.getElementById('output-area').innerHTML = result.output || '<p class="text-danger">No output received.</p>';
                if (result.status === 'already_correct' || result.passed_all_tests) {
                    document.getElementById('next-question-btn').style.display = 'inline-block';
                     if (currentQuestion.current_q_num === currentQuestion.total_questions) {
                        document.getElementById('next-question-btn').style.display = 'none';
                        document.getElementById('finish-test-btn').style.display = 'inline-block';
                    }
                }
                if (result.new_score !== undefined) {
                     document.getElementById('nav-score').textContent = `Score: ${result.new_score}`;
                }
            })
            .catch(error => {
                console.error('Error evaluating code:', error);
                document.getElementById('output-area').innerHTML = '<p class="text-danger">Error during evaluation. Please try again.</p>';
            })
            .finally(() => {
                 document.getElementById('run-code-btn').disabled = false;
            });
        });

        document.getElementById('next-question-btn').addEventListener('click', () => {
            fetch('/api/next_question', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.test_completed) {
                        displayTestCompleted(data);
                    } else if (data.next_question_loaded) {
                        loadQuestion(); 
                    } else if (data.error) {
                        alert("Error: " + data.error);
                         window.location.href = "/"; 
                    }
                })
                .catch(error => {
                    console.error('Error moving to next question:', error);
                    alert('Failed to load next question. Please check your connection or try restarting.');
                });
        });
        
        document.getElementById('finish-test-btn').addEventListener('click', () => {
             fetch('/api/next_question', { method: 'POST' }) 
                .then(response => response.json())
                .then(data => {
                    if (data.test_completed) {
                        displayTestCompleted(data);
                    } else {
                        console.warn("Finish button clicked, but test not completed by API.");
                        if (data.next_question_loaded) loadQuestion();
                    }
                })
                .catch(error => console.error('Error finishing test:', error));
        });

    } 

    function updateProgressBar(current, total) {
        const percentage = total > 0 ? (current / total) * 100 : 0;
        const progressBar = document.getElementById('test-progress-bar');
        if (progressBar) {
            progressBar.style.width = percentage + '%';
            progressBar.setAttribute('aria-valuenow', percentage);
        }
        const questionProgressDisplay = document.getElementById('question-progress');
        if(questionProgressDisplay) {
            questionProgressDisplay.textContent = `${current} / ${total}`;
        }
    }
    
    function startQuestionTimer(durationSeconds) { 
        clearInterval(questionTimerInterval);
        let elapsedSeconds = 0; 
        const timerDisplay = document.getElementById('question-timer');

        if (!timerDisplay) return;
        
        timerDisplay.textContent = "00:00"; 

        questionTimerInterval = setInterval(() => {
            elapsedSeconds++;
            const minutes = Math.floor(elapsedSeconds / 60);
            const seconds = elapsedSeconds % 60;
            timerDisplay.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }, 1000);
    }

    function loadQuestion() {
        fetch('/api/question')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}, message: ${response.statusText}`);
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    alert("Error loading question: " + data.error);
                     window.location.href = "/"; 
                    return;
                }
                if (data.test_completed) {
                    displayTestCompleted(data); // API will return current score if test was already done
                    return;
                }

                currentQuestion = data; 

                document.getElementById('question-title').textContent = data.title;
                const challengeNameEl = document.getElementById('current-challenge-name');
                if(challengeNameEl) challengeNameEl.textContent = data.challenge_name || 'N/A';
                
                document.getElementById('question-level').textContent = data.level;
                document.getElementById('question-language').textContent = data.language.toUpperCase();
                document.getElementById('question-description').innerHTML = data.description; 
                
                updateProgressBar(data.current_q_num, data.total_questions);
                const navScoreEl = document.getElementById('nav-score');
                if(navScoreEl) navScoreEl.textContent = `Score: ${data.user_score}`;

                if (editor) { 
                    if (data.language === 'sql') {
                        editor.setOption("mode", "text/x-sql");
                        document.getElementById('sql-schema-container').style.display = 'block';
                        document.getElementById('schema-details').textContent = data.schema || "No schema provided.";
                    } else { 
                        editor.setOption("mode", "python");
                        document.getElementById('sql-schema-container').style.display = 'none';
                    }
                    editor.setValue(data.starter_code || '');
                    editor.focus(); 
                }
                
                document.getElementById('output-area').innerHTML = '<p class="text-muted">Run your code to see the output here.</p>';
                document.getElementById('run-code-btn').disabled = false;
                document.getElementById('next-question-btn').style.display = 'none';
                document.getElementById('finish-test-btn').style.display = 'none';

                startQuestionTimer(data.time_limit_seconds); 
            })
            .catch(error => {
                console.error('Fatal error loading question:', error);
                const qTitle = document.getElementById('question-title');
                if(qTitle) qTitle.textContent = "Error loading question. Please try refreshing.";
                const testContainer = document.getElementById('test-container');
                if(testContainer) testContainer.innerHTML = `<div class="alert alert-danger">Could not load question data. ${error.message}. Please <a href="/">restart the test</a>.</div>`;
            });
    }

    function displayTestCompleted(data) {
        clearInterval(questionTimerInterval); 
        
        const fsNote = document.getElementById('fullscreen-note');
        if (fsNote) fsNote.remove();

        document.getElementById('test-container').style.display = 'none';
        const completedMsgEl = document.getElementById('test-completed-message');
        if (completedMsgEl) {
            completedMsgEl.style.display = 'block';
            document.getElementById('final-score').textContent = data.score;
            document.getElementById('total-time-taken').textContent = data.total_time + 's';
            
            const completedChallengeNameElem = document.getElementById('completed-challenge-name');
            let cName = "N/A";
            if (data.challenge_name) { 
                cName = data.challenge_name;
            } else if (currentQuestion && currentQuestion.challenge_name) { // Fallback if API didn't send it on completion
                cName = currentQuestion.challenge_name;
            }
            if (completedChallengeNameElem) completedChallengeNameElem.textContent = cName;

            const scoreboardLink = document.getElementById('view-challenge-scoreboard-link');
            if (scoreboardLink && data.challenge_id) {
                scoreboardLink.href = `/scoreboard/${data.challenge_id}`; 
            } else if (scoreboardLink) {
                 scoreboardLink.href = (typeof SCOREBOARD_BASE_URL !== 'undefined' ? SCOREBOARD_BASE_URL : "/scoreboards");
            }
        }
    }

});