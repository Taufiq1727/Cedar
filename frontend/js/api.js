/**
 * MediKiosk API Client - handles all backend communication.
 */
const API_BASE = (window.location.port === '8000') ? '' : 'http://127.0.0.1:8000';

class ApiClient {
    constructor() {
        this.baseUrl = API_BASE;
    }

    getToken() {
        return localStorage.getItem('medikiosk_token');
    }

    setAuth(data) {
        localStorage.setItem('medikiosk_token', data.access_token);
        localStorage.setItem('medikiosk_role', data.role);
        localStorage.setItem('medikiosk_name', data.name);
        localStorage.setItem('medikiosk_user_id', data.user_id);
    }

    clearAuth() {
        localStorage.removeItem('medikiosk_token');
        localStorage.removeItem('medikiosk_role');
        localStorage.removeItem('medikiosk_name');
        localStorage.removeItem('medikiosk_user_id');
    }

    getRole() { return localStorage.getItem('medikiosk_role'); }
    getName() { return localStorage.getItem('medikiosk_name'); }
    getUserId() { return localStorage.getItem('medikiosk_user_id'); }
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
    async uploadDocument(file, category, sessionId = null) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', category);
        if (sessionId) formData.append('session_id', sessionId);

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
    async getDoctorPatients() {
        return this.request('/doctor/patients');
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
}

// Global instance
const api = new ApiClient();
