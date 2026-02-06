document.addEventListener('DOMContentLoaded', () => {
    // Elements for "Scrape All" flow
    const scrapeAllBtn = document.getElementById('scrape-all-btn');
    const globalProgress = document.getElementById('global-progress');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const currentSiteInfo = document.getElementById('current-site-info');
    const approveBtn = document.getElementById('approve-btn');
    const skipBtn = document.getElementById('skip-btn');
    const approveAllBtn = document.getElementById('approve-all-btn');
    const logsDiv = document.getElementById('logs');
    const sitesGrid = document.getElementById('sites-grid');
    const tableBody = document.querySelector('#results-table tbody');
    const summaryDiv = document.getElementById('results-summary');

    let currentTaskId = null;
    let pollingInterval = null;

    // Initialize: Fetch plan and render cards
    fetchPlanAndRenderCards();

    async function fetchPlanAndRenderCards() {
        try {
            const resp = await fetch('/api/scrape/plan');
            const data = await resp.json();
            renderCards(data.plan);
        } catch (e) {
            console.error("Failed to fetch plan:", e);
            sitesGrid.innerHTML = `<p class="error">Failed to load sites: ${e}</p>`;
        }
    }

    function renderCards(plan) {
        sitesGrid.innerHTML = '';
        plan.forEach((site, index) => {
            const card = document.createElement('div');
            card.className = 'site-card';
            card.innerHTML = `
                <div>
                    <span class="platform-tag">${site.platform}</span>
                    <h3>${new URL(site.url).hostname}</h3>
                    <div style="font-size: 0.8em; color: #666; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${site.url}
                    </div>
                </div>
                <div class="actions">
                    <button class="scrape-one-btn" data-url="${site.url}" data-idx="${index}">
                        Scrape This Site
                    </button>
                </div>
            `;
            sitesGrid.appendChild(card);
        });

        // Attach event listeners to new buttons
        document.querySelectorAll('.scrape-one-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const url = e.target.dataset.url;
                scrapeOne(url, e.target);
            });
        });
    }

    // --- Scrape Single Site Logic ---
    async function scrapeOne(url, btn) {
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Scraping...';
        }
        log(`Starting single scrape for: ${url}`);
        
        try {
            const resp = await fetch('/api/scrape/one', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: url })
            });
            const result = await resp.json();
            
            if (result.status === 'error') {
                log(`Error scraping ${url}: ${result.message || 'Unknown error'}`, 'error');
            } else {
                log(`Finished scraping ${url}. Found ${result.jobs ? result.jobs.length : 0} jobs.`, 'success');
                // Append results to table instead of clearing
                appendResults([result]);
                
                // Update stats card
                if (btn) updateCardStats(btn, result);
            }
        } catch (e) {
            log(`Exception scraping ${url}: ${e}`, 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Scrape This Site';
            }
        }
    }
    
    function updateCardStats(btn, result) {
        const card = btn.closest('.site-card');
        if (!card) return;
        
        let statsDiv = card.querySelector('.site-stats');
        if (!statsDiv) {
            statsDiv = document.createElement('div');
            statsDiv.className = 'site-stats';
            statsDiv.style.marginTop = '10px';
            statsDiv.style.fontSize = '0.85em';
            statsDiv.style.background = '#f5f5f5';
            statsDiv.style.padding = '8px';
            statsDiv.style.borderRadius = '4px';
            statsDiv.style.border = '1px solid #ddd';
            
            // Insert before actions div
            const actionsDiv = card.querySelector('.actions');
            card.insertBefore(statsDiv, actionsDiv);
        }
        
        const pages = (result.stats && result.stats.pages) ? result.stats.pages : 1;
        const total = result.total_found || 0;
        const kept = result.filtered_count || 0;
        const duration = (result.stats && result.stats.duration) ? `${result.stats.duration}s` : 'N/A';

        statsDiv.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px;">
                <div><strong>Pages:</strong> ${pages}</div>
                <div><strong>Found:</strong> ${total}</div>
                <div><strong>Kept:</strong> ${kept}</div>
                <div><strong>Filtered:</strong> ${total - kept}</div>
            </div>
        `;
    }

    // --- Scrape All Logic (Existing Flow) ---
    scrapeAllBtn.addEventListener('click', async () => {
        scrapeAllBtn.disabled = true;
        tableBody.innerHTML = ''; // Clear table for new run
        if (summaryDiv) summaryDiv.innerHTML = '';
        log('Starting global scraping process...');
        globalProgress.style.display = 'block';
        progressBar.style.width = '0%';
        progressText.textContent = '0%';

        try {
            const response = await fetch('/api/scrape/start', { method: 'POST' });
            const data = await response.json();
            if (data.task_id) {
                currentTaskId = data.task_id;
                log(`Task ID: ${currentTaskId}`);
                pollStatus(currentTaskId);
            } else {
                log('Failed to start task', 'error');
                scrapeAllBtn.disabled = false;
            }
        } catch (e) {
            log(`Error starting task: ${e}`, 'error');
            scrapeAllBtn.disabled = false;
        }
    });

    function pollStatus(taskId) {
        if (pollingInterval) clearInterval(pollingInterval);
        
        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/scrape/status/${taskId}`);
                const data = await response.json();

                // Update Progress UI
                const progress = data.total > 0 ? (data.progress / data.total) * 100 : 0;
                progressBar.style.width = `${progress}%`;
                progressText.textContent = `${Math.round(progress)}%`;

                // Handle Logs
                if (data.logs && data.logs.length > 0) {
                   // Just show the last few logs to avoid spam
                   const recentLogs = data.logs.slice(-3);
                   recentLogs.forEach(l => log(l)); 
                }

                // Handle Approval State
                if (data.awaiting_approval && data.next_url) {
                    currentSiteInfo.textContent = `Ready to scrape: ${data.next_url}`;
                    toggleActionButtons(true);
                } else {
                    currentSiteInfo.textContent = data.status === 'running' ? 'Processing...' : `Status: ${data.status}`;
                    toggleActionButtons(false);
                }

                // Update Results Table (Cumulative)
                // Note: The backend returns *all* results so far in data.results
                // So we should re-render the table to avoid duplicates or complex diffing
                if (data.results && data.results.length > 0) {
                    renderResultsTable(data.results);
                }

                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(pollingInterval);
                    scrapeAllBtn.disabled = false;
                    toggleActionButtons(false);
                    log(`Process finished: ${data.status}`, data.status === 'completed' ? 'success' : 'error');
                }

            } catch (e) {
                console.error(e);
            }
        }, 1000);
    }

    function toggleActionButtons(show) {
        const display = show ? 'inline-block' : 'none';
        approveBtn.style.display = display;
        skipBtn.style.display = display;
        approveAllBtn.style.display = display;
    }

    // --- Action Buttons ---
    approveBtn.addEventListener('click', () => sendAction('approve'));
    skipBtn.addEventListener('click', () => sendAction('skip'));
    approveAllBtn.addEventListener('click', () => sendAction('approve_all'));

    async function sendAction(action) {
        if (!currentTaskId) return;
        try {
            await fetch(`/api/scrape/${action}/${currentTaskId}`, { method: 'POST' });
            toggleActionButtons(false);
            log(`Action sent: ${action}`);
        } catch (e) {
            log(`Failed to send action ${action}: ${e}`, 'error');
        }
    }

    // --- Helper Functions ---
    function log(msg, type='') {
        const p = document.createElement('p');
        p.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
        if (type) p.className = type;
        logsDiv.appendChild(p);
        logsDiv.scrollTop = logsDiv.scrollHeight;
    }

    // Re-render the whole table (used by global scrape)
    function renderResultsTable(results) {
        tableBody.innerHTML = '';
        appendResults(results);
    }

    // Append results (used by single scrape or global re-render)
    function appendResults(results) {
        let totalRecent = 0;
        let totalAll = 0;

        results.forEach(result => {
            const jobs = result.jobs || [];
            if (jobs.length > 0) {
                totalAll += jobs.length;
                jobs.forEach(job => {
                    const row = tableBody.insertRow();
                    row.innerHTML = `
                        <td><a href="${result.url}" target="_blank">${new URL(result.url).hostname}</a></td>
                        <td>${result.platform || 'N/A'}</td>
                        <td>${job.company || 'N/A'}</td>
                        <td>${job.title || 'N/A'}</td>
                        <td><a href="${job.link}" target="_blank">Apply</a></td>
                        <td class="details-cell"></td>
                    `;
                    
                    // Add details button
                    const btn = document.createElement('button');
                    btn.className = 'details-btn';
                    btn.textContent = 'Details';
                    btn.onclick = () => toggleDetails(row, job.details, job.description);
                    row.querySelector('.details-cell').appendChild(btn);
                });
            }
        });
        
        if (summaryDiv) {
            summaryDiv.innerHTML = `<p>Total jobs displayed: <strong>${totalAll}</strong></p>`;
        }
    }

    function toggleDetails(row, details, description) {
        const next = row.nextElementSibling;
        if (next && next.classList.contains('details-row')) {
            next.remove();
            return;
        }
        
        const tr = document.createElement('tr');
        tr.className = 'details-row';
        const td = document.createElement('td');
        td.colSpan = 6;
        
        let content = '<div class="details-grid">';
        
        // Handle structured details if available
        if (details && typeof details === 'object') {
            for (const [key, val] of Object.entries(details)) {
                content += `
                    <div class="section">
                        <h4>${key}</h4>
                        <div>${val}</div>
                    </div>
                `;
            }
        }
        
        // Fallback or addition of description
        if ((!details || Object.keys(details).length === 0) && description) {
             content += `
                <div class="section">
                    <h4>Description</h4>
                    <div>${description}</div>
                </div>
            `;
        }
        
        content += '</div>';
        td.innerHTML = content;
        tr.appendChild(td);
        row.insertAdjacentElement('afterend', tr);
    }
});
