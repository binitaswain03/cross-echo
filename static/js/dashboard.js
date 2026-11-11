// CrossEcho Dashboard Interactive Client

function refreshDashboardData() {
    const tableBody = document.getElementById('recent-detections-table');
    const totalEl = document.getElementById('stat-total');
    const todayEl = document.getElementById('stat-today');
    const topEl = document.getElementById('stat-top');
    const freqListEl = document.getElementById('frequency-list');
    
    // Animate refreshing icon
    const refreshBtnIcon = document.querySelector('.panel-actions button i');
    if (refreshBtnIcon) {
        refreshBtnIcon.style.transition = 'transform 0.8s ease';
        refreshBtnIcon.style.transform = 'rotate(360deg)';
        setTimeout(() => {
            refreshBtnIcon.style.transform = 'rotate(0deg)';
        }, 800);
    }
    
    fetch('/api/stats')
        .then(response => {
            if (!response.ok) throw new Error('Network error fetching statistics');
            return response.json();
        })
        .then(data => {
            // 1. Update stats metrics cards
            if (totalEl) totalEl.textContent = data.stats.total_detections;
            if (todayEl) todayEl.textContent = data.stats.today_detections;
            if (topEl) topEl.textContent = data.stats.top_object;
            
            // 2. Repopulate Recent Detections table
            if (tableBody) {
                tableBody.innerHTML = '';
                if (data.recent && data.recent.length > 0) {
                    data.recent.forEach(row => {
                        const tr = document.createElement('tr');
                        
                        let badgeClass = 'badge-primary';
                        let badgeText = 'Medium';
                        if (row.confidence >= 0.85) {
                            badgeClass = 'badge-success';
                            badgeText = 'High';
                        } else if (row.confidence < 0.65) {
                            badgeClass = 'badge-warning';
                            badgeText = 'Low';
                        }
                        
                        tr.innerHTML = `
                            <td style="font-weight: 600; text-transform: capitalize;">
                                <i data-lucide="tag" size="12" style="margin-right: 0.25rem; color: var(--secondary); vertical-align: middle;"></i>
                                ${row.object_name}
                            </td>
                            <td>${(row.confidence * 100).toFixed(1)}%</td>
                            <td style="color: var(--text-secondary); font-family: monospace;">${row.timestamp}</td>
                            <td>
                                <span class="badge ${badgeClass}">${badgeText}</span>
                            </td>
                        `;
                        tableBody.appendChild(tr);
                    });
                    lucide.createIcons();
                } else {
                    tableBody.innerHTML = `
                        <tr id="no-detections-row">
                            <td colspan="4" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                                <i data-lucide="inbox" size="24" style="display: block; margin: 0 auto 0.5rem;"></i>
                                No detections logged yet. Start detection mode to populate data.
                            </td>
                        </tr>
                    `;
                    lucide.createIcons();
                }
            }
            
            // 3. Update Category Frequencies panel
            if (freqListEl) {
                freqListEl.innerHTML = '';
                const counts = data.stats.object_counts;
                const keys = Object.keys(counts);
                
                if (keys.length > 0) {
                    keys.forEach(name => {
                        const div = document.createElement('div');
                        div.style.display = 'flex';
                        div.style.justifyContent = 'space-between';
                        div.style.alignItems = 'center';
                        div.innerHTML = `
                            <span style="text-transform: capitalize; color: var(--text-secondary);">${name}</span>
                            <span class="badge badge-primary">${counts[name]} times</span>
                        `;
                        freqListEl.appendChild(div);
                    });
                } else {
                    freqListEl.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 1rem;">No category statistics.</p>';
                }
            }
        })
        .catch(err => {
            console.error('Error refreshing dashboard metrics: ', err);
        });
}

// Poll stats every 10 seconds to keep dashboard synced if running webcam in another tab
document.addEventListener('DOMContentLoaded', () => {
    setInterval(refreshDashboardData, 10000);
});
