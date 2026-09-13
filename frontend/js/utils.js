/**
 * Shared utility functions.
 */

/** Format a date string or Date object to a readable format. */
function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function formatDateTime(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatTimeAgo(dateStr) {
    if (!dateStr) return '';
    const now = new Date();
    const d = new Date(dateStr);
    const diffMs = now - d;
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHrs = Math.floor(diffMins / 60);
    if (diffHrs < 24) return `${diffHrs}h ago`;
    const diffDays = Math.floor(diffHrs / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    return formatDate(dateStr);
}

/** Show/hide a loading spinner overlay. */
function showLoading() {
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<div class="spinner spinner-lg"></div>';
        document.body.appendChild(overlay);
    }
    overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = 'none';
}

/** Check auth and redirect if needed. */
function requireAuth(role = null) {
    if (!api.isLoggedIn()) {
        window.location.href = '/login.html';
        return false;
    }
    if (role && api.getRole() !== role) {
        const userRole = api.getRole();
        if (userRole === 'doctor') {
            window.location.href = '/doctor-dashboard.html';
        } else if (userRole === 'assistant' || userRole === 'nurse') {
            window.location.href = '/assistant-dashboard.html';
        } else {
            window.location.href = '/patient-dashboard.html';
        }
        return false;
    }
    return true;
}

/** Escape HTML to prevent XSS. */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/** Get priority badge HTML. */
function priorityBadge(priority) {
    const map = {
        'HIGH': '<span class="badge badge-danger">🔴 High Priority</span>',
        'MEDIUM': '<span class="badge badge-warning">🟡 Medium</span>',
        'NORMAL': '<span class="badge badge-success">🟢 Normal</span>',
    };
    return map[priority] || map['NORMAL'];
}

/** Get status badge HTML. */
function statusBadge(status) {
    const map = {
        'in_progress': '<span class="badge badge-info">In Progress</span>',
        'completed': '<span class="badge badge-primary">Completed</span>',
        'reviewed': '<span class="badge badge-warning">Under Review</span>',
        'approved': '<span class="badge badge-success">✓ Clinician Verified</span>',
        'generated': '<span class="badge badge-primary">AI Generated</span>',
        'pending': '<span class="badge badge-neutral">Pending</span>',
        'rejected': '<span class="badge badge-danger">Rejected</span>',
    };
    return map[status] || `<span class="badge badge-neutral">${escapeHtml(status)}</span>`;
}

/** Simple tab switching. */
function initTabs(containerSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    const tabs = container.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.dataset.tab;
            // Deactivate all
            container.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            // Activate clicked
            tab.classList.add('active');
            const target = document.getElementById(targetId);
            if (target) target.classList.add('active');
        });
    });
}
