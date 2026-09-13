/**
 * ClinAssistAI API Client - handles all backend communication.
 */
const API_BASE = (window.location.port === '8000') ? '' : 'http://127.0.0.1:8000';

class ApiClient {
    constructor() {
        this.baseUrl = API_BASE;
    }

    getToken() {
        return localStorage.getItem('clinassistai_token') || localStorage.getItem('medikiosk_token');
    }

    setAuth(data) {
        localStorage.setItem('clinassistai_token', data.access_token);
        localStorage.setItem('clinassistai_role', data.role);
        localStorage.setItem('clinassistai_name', data.name);
        localStorage.setItem('clinassistai_user_id', data.user_id);
    }

    clearAuth() {
        localStorage.removeItem('clinassistai_token');
        localStorage.removeItem('clinassistai_role');
        localStorage.removeItem('clinassistai_name');
        localStorage.removeItem('clinassistai_user_id');
        localStorage.removeItem('medikiosk_token');
        localStorage.removeItem('medikiosk_role');
        localStorage.removeItem('medikiosk_name');
        localStorage.removeItem('medikiosk_user_id');
    }

    getRole() { return localStorage.getItem('clinassistai_role') || localStorage.getItem('medikiosk_role'); }
    getName() { return localStorage.getItem('clinassistai_name') || localStorage.getItem('medikiosk_name'); }
    getUserId() { return localStorage.getItem('clinassistai_user_id') || localStorage.getItem('medikiosk_user_id'); }
    isLoggedIn() { return !!this.getToken(); }

    async request(path, options = {}) {
        const url = `${this.baseUrl}${path}`;
        const headers = options.headers || {};

        if (this.getToken()) {
            headers['Authorization'] = `Bearer ${this.getToken()}`;
        }

        if (!(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            if (response.status === 401) {
                this.clearAuth();
                window.location.href = '/login.html';
                throw new Error('Session expired. Please login again.');
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `Request failed (${response.status})`);
            }

            return data;
        } catch (error) {
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                throw new Error('Unable to connect to server. Please check if the backend is running.');
            }
            throw error;
        }
    }

    // Auth
    async register(data) {
        const result = await this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        this.setAuth(result);
        return result;
    }

    async login(email, password) {
        const result = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        this.setAuth(result);
        return result;
    }

    async getProfile() {
        return this.request('/auth/me');
    }

    // Patient
    async getPatientProfile() {
        return this.request('/patients/me');
    }

    async updatePatientProfile(data) {
        return this.request('/patients/me', {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async getPatientSessions() {
        return this.request('/patients/me/sessions');
    }

    async getPatientDocuments() {
        return this.request('/patients/me/documents');
    }

    // Intake
    async startIntake(language, consentGiven) {
        return this.request('/intake/start', {
            method: 'POST',
            body: JSON.stringify({ language, consent_given: consentGiven }),
        });
    }

    async submitAnswer(sessionId, answerText, inputMethod = 'text', questionKey = null) {
        return this.request(`/intake/${sessionId}/answer`, {
            method: 'POST',
            body: JSON.stringify({
                answer_text: answerText,
                input_method: inputMethod,
                question_key: questionKey,
            }),
        });
    }

    async getSession(sessionId) {
        return this.request(`/intake/${sessionId}`);
    }

    async completeSession(sessionId) {
        return this.request(`/intake/${sessionId}/complete`, { method: 'POST' });
    }

    // Documents
    async uploadDocument(file, category, sessionId = null, patientId = null) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', category);
        if (sessionId) formData.append('session_id', sessionId);
        if (patientId) formData.append('patient_id', patientId);

        return this.request('/documents/upload', {
            method: 'POST',
            body: formData,
        });
    }

    async getDocuments(patientId) {
        return this.request(`/documents/patient/${patientId}`);
    }

    // AI
    async generateSummary(sessionId) {
        return this.request(`/ai/generate-summary/${sessionId}`, { method: 'POST' });
    }

    async getTimeline(patientId) {
        return this.request(`/ai/timeline/${patientId}`);
    }

    async getFhirBundle(patientId) {
        return this.request(`/ai/fhir/${patientId}`);
    }

    // Doctor
    async getDoctorPatients(scope = 'all') {
        const query = scope ? `?scope=${encodeURIComponent(scope)}` : '';
        return this.request(`/doctor/patients${query}`);
    }

    async getDoctorPatientDetail(patientId) {
        return this.request(`/doctor/patient/${patientId}`);
    }

    async approveSummary(summaryId, status, doctorNotes = null, edits = null) {
        return this.request(`/doctor/summary/${summaryId}/approve`, {
            method: 'POST',
            body: JSON.stringify({ status, doctor_notes: doctorNotes, edits }),
        });
    }

    async getSessionSummary(sessionId) {
        return this.request(`/doctor/summary/${sessionId}`);
    }

    async assignSessionDoctor(sessionId, doctorId = null) {
        return this.request(`/doctor/session/${sessionId}/assign`, {
            method: 'POST',
            body: JSON.stringify({ doctor_id: doctorId }),
        });
    }

    async resolveRedFlag(flagId) {
        return this.request(`/doctor/red-flag/${flagId}/resolve`, {
            method: 'POST',
        });
    }

    async savePrescription(data) {
        return this.request('/doctor/prescription', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async addTimelineEvent(patientId, data) {
        return this.request(`/doctor/patient/${patientId}/timeline`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // Assistant / Nurse Triage
    async getAssistantStats() {
        return this.request('/assistant/stats');
    }

    async getAvailableDoctors(specialization = '') {
        const query = specialization ? `?specialization=${encodeURIComponent(specialization)}` : '';
        return this.request(`/assistant/doctors${query}`);
    }

    async searchPatients(q = '') {
        const query = q ? `?q=${encodeURIComponent(q)}` : '';
        return this.request(`/assistant/patients/search${query}`);
    }

    async registerPatient(data) {
        return this.request('/assistant/patients/register', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async aiExtractNotes(data) {
        return this.request('/assistant/ai-extract', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async submitTriageIntake(data) {
        return this.request('/assistant/triage-intake', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getRecentTriages() {
        return this.request('/assistant/recent-triages');
    }

    async configureGeminiKey(apiKey) {
        return this.request('/ai/configure-key', {
            method: 'POST',
            body: JSON.stringify({ api_key: apiKey }),
        });
    }
}

// Global instance
const api = new ApiClient();
