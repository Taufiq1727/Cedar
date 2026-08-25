/**
 * Voice input using Web Speech API.
 * Structured for future replacement with Whisper or Indian-language ASR.
 */
class VoiceInput {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.onResult = null;
        this.onError = null;
        this.language = 'en-IN';
        this.supported = this._checkSupport();
    }

    _checkSupport() {
        return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
    }

    setLanguage(lang) {
        const langMap = {
            'en': 'en-IN',
            'hi': 'hi-IN',
            'kn': 'kn-IN',
        };
        this.language = langMap[lang] || 'en-IN';
    }

    start(callback, errorCallback) {
        if (!this.supported) {
            if (errorCallback) errorCallback('Speech recognition not supported in this browser.');
            return false;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        this.recognition.lang = this.language;
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;

        this.recognition.onresult = (event) => {
            let transcript = '';
            let isFinal = false;
            for (let i = event.resultIndex; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
                if (event.results[i].isFinal) isFinal = true;
            }
            if (callback) callback(transcript, isFinal);
        };

        this.recognition.onerror = (event) => {
            this.isListening = false;
            const errorMessages = {
                'no-speech': 'No speech detected. Please try again.',
                'audio-capture': 'Microphone not found. Please check your device.',
                'not-allowed': 'Microphone access denied. Please allow microphone access.',
                'network': 'Network error. Speech recognition requires an internet connection.',
            };
            const msg = errorMessages[event.error] || `Speech recognition error: ${event.error}`;
            if (errorCallback) errorCallback(msg);
        };

        this.recognition.onend = () => {
            this.isListening = false;
        };

        try {
            this.recognition.start();
            this.isListening = true;
            return true;
        } catch (e) {
            if (errorCallback) errorCallback('Failed to start speech recognition.');
            return false;
        }
    }

    stop() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.isListening = false;
        }
    }
}

const voiceInput = new VoiceInput();
