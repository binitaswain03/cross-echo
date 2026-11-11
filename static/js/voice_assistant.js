/**
 * CrossEcho Voice & Accessibility Assistant
 * Multilingual (English, Hindi, Odia) Speech Engine & Interactive Voice Commands
 * Designed for visually impaired users - hands-free navigation, camera switching & language controls.
 */

class CrossEchoVoiceAssistant {
    constructor() {
        this.synth = window.speechSynthesis;
        this.isEnabled = localStorage.getItem('crossecho_voice_enabled') !== 'false';
        this.speechRate = parseFloat(localStorage.getItem('crossecho_voice_rate') || '1.0');
        this.speechVolume = parseFloat(localStorage.getItem('crossecho_voice_volume') || '1.0');
        
        // Active Language: 'en' (English), 'hi' (Hindi), 'or' (Odia)
        this.currentLanguage = localStorage.getItem('crossecho_language') || 'en';
        
        this.selectedVoice = null;
        this.lastSpokenText = '';
        this.lastSpokenTime = 0;
        this.isSpeakingNow = false; // Prevents microphone from hearing its own speech
        this.audioCtx = null;
        
        // Speech Recognition (Voice Commands)
        this.recognition = null;
        this.isListening = false;
        this.speechRecognitionSupported = false;
        this.micEnabled = localStorage.getItem('crossecho_mic_enabled') !== 'false'; // Default ON for accessibility
        
        // Cooldown cache for duplicate messages
        this.phraseCooldowns = new Map();

        this.initVoices();
        this.initAudioContext();
        this.initSpeechRecognition();
        this.initKeyboardShortcuts();
        this.initAccessibilityNarration();
    }

    initAudioContext() {
        try {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) {
                this.audioCtx = new AudioCtx();
            }
        } catch (e) {
            console.warn("Web Audio API not supported:", e);
        }
    }

    ensureAudioContext() {
        if (this.audioCtx && this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }
    }

    initVoices() {
        if (!this.synth) return;
        
        const updateVoices = () => {
            this.updateVoiceForLanguage(this.currentLanguage);
        };

        updateVoices();
        if (this.synth.onvoiceschanged !== undefined) {
            this.synth.onvoiceschanged = updateVoices;
        }
    }

    updateVoiceForLanguage(lang) {
        if (!this.synth) return;
        const voices = this.synth.getVoices();
        if (!voices || voices.length === 0) return;

        if (lang === 'hi') {
            this.selectedVoice = voices.find(v => v.lang.startsWith('hi') || v.lang.includes('Hindi'))
                || voices.find(v => v.lang.startsWith('en-IN'))
                || voices.find(v => v.lang.startsWith('en'))
                || voices[0];
        } else if (lang === 'or') {
            this.selectedVoice = voices.find(v => v.lang.startsWith('or') || v.lang.includes('Odia') || v.lang.includes('Oriya'))
                || voices.find(v => v.lang.startsWith('hi') || v.lang.includes('Hindi'))
                || voices.find(v => v.lang.startsWith('en-IN'))
                || voices.find(v => v.lang.startsWith('en'))
                || voices[0];
        } else {
            this.selectedVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('David') || v.name.includes('Zira')))
                || voices.find(v => v.lang.startsWith('en'))
                || voices[0];
        }
    }

    setLanguage(lang) {
        if (!['en', 'hi', 'or'].includes(lang)) return;
        this.currentLanguage = lang;
        localStorage.setItem('crossecho_language', lang);
        this.updateVoiceForLanguage(lang);
        this.updateRecognitionLanguage();
        
        // Sync language select dropdowns in the UI
        document.querySelectorAll('.language-select').forEach(sel => {
            sel.value = lang;
        });

        // Confirmation announcement in selected language
        const msgs = {
            'en': "Language set to English.",
            'hi': "भाषा बदलकर हिन्दी कर दी गई है।",
            'or': "ଭାଷା ବଦଳାଇ ଓଡ଼ିଆ କରାଗଲା।"
        };
        const phoneticMsgs = {
            'or': "Bhasa badalai Odia karagala."
        };

        const spoken = (lang === 'or' && !this.hasNativeOdiaVoice()) ? phoneticMsgs['or'] : msgs[lang];
        this.speak(spoken, { flush: true, priority: 'urgent', lang: lang });
        this.playChime('action');
    }

    hasNativeOdiaVoice() {
        if (!this.synth) return false;
        const voices = this.synth.getVoices();
        return voices.some(v => v.lang.startsWith('or') || v.lang.includes('Odia') || v.lang.includes('Oriya'));
    }

    cycleLanguage() {
        const order = ['en', 'hi', 'or'];
        const nextIdx = (order.indexOf(this.currentLanguage) + 1) % order.length;
        this.setLanguage(order[nextIdx]);
    }

    /* ----------------- Continuous Speech Recognition (Voice Commands) ----------------- */

    initSpeechRecognition() {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
            console.warn("Speech Recognition API not supported in this browser.");
            return;
        }
        this.speechRecognitionSupported = true;

        try {
            this.recognition = new SpeechRec();
            this.recognition.continuous = true;
            this.recognition.interimResults = false;
            this.recognition.maxAlternatives = 2;

            this.updateRecognitionLanguage();

            this.recognition.onstart = () => {
                this.isListening = true;
                this.updateMicToolbarState(true);
            };

            this.recognition.onend = () => {
                if (this.micEnabled) {
                    setTimeout(() => {
                        if (this.micEnabled && !this.isListening) {
                            try {
                                this.recognition.start();
                            } catch (e) {}
                        }
                    }, 400);
                } else {
                    this.isListening = false;
                    this.updateMicToolbarState(false);
                }
            };

            this.recognition.onerror = (e) => {
                console.debug("Speech recognition notice:", e.error);
                if (e.error === 'not-allowed') {
                    this.micEnabled = false;
                    this.isListening = false;
                    localStorage.setItem('crossecho_mic_enabled', 'false');
                    this.updateMicToolbarState(false);
                }
            };

            this.recognition.onresult = (event) => {
                if (this.isSpeakingNow) {
                    return;
                }
                const lastIdx = event.results.length - 1;
                const result = event.results[lastIdx];
                if (result && result[0]) {
                    const transcript = result[0].transcript.trim().toLowerCase();
                    this.handleVoiceCommand(transcript);
                }
            };

            if (this.micEnabled) {
                setTimeout(() => this.startListening(), 1200);
            }
        } catch (e) {
            console.warn("SpeechRecognition init error:", e);
        }
    }

    updateRecognitionLanguage() {
        if (!this.recognition) return;
        if (this.currentLanguage === 'hi') {
            this.recognition.lang = 'hi-IN';
        } else if (this.currentLanguage === 'or') {
            this.recognition.lang = 'hi-IN';
        } else {
            this.recognition.lang = 'en-US';
        }
    }

    startListening() {
        if (!this.recognition) return;
        this.micEnabled = true;
        localStorage.setItem('crossecho_mic_enabled', 'true');
        this.updateRecognitionLanguage();
        try {
            this.recognition.start();
        } catch (e) {}
        this.updateMicToolbarState(true);
    }

    stopListening() {
        this.micEnabled = false;
        this.isListening = false;
        localStorage.setItem('crossecho_mic_enabled', 'false');
        if (this.recognition) {
            try {
                this.recognition.stop();
            } catch (e) {}
        }
        this.updateMicToolbarState(false);
    }

    toggleSpeechRecognition() {
        if (this.isListening) {
            this.stopListening();
            const msg = {
                'en': "Voice commands paused.",
                'hi': "आवाज नियंत्रण बंद किया गया।",
                'or': "ଭଏସ୍ କମାଣ୍ଡ ବନ୍ଦ ହେଲା।"
            };
            this.speak(msg[this.currentLanguage] || msg['en'], { flush: true });
        } else {
            this.startListening();
            this.playChime('action');
            const msg = {
                'en': "Voice commands active. Say: Start navigation, Switch camera, or Hindi.",
                'hi': "आवाज नियंत्रण चालू है। कहिए: कैमरा शुरू करो, कैमरा बदलो, या अंग्रेज़ी।",
                'or': "ଭଏସ୍ କମାଣ୍ଡ ସକ୍ରିୟ। କୁହନ୍ତୁ: କ୍ୟାମେରା ଆରମ୍ଭ, କ୍ୟାମେରା ବଦଳାଅ, କିମ୍ବା ହିନ୍ଦୀ।"
            };
            this.speak(msg[this.currentLanguage] || msg['en'], { flush: true, priority: 'urgent' });
        }
    }

    showCommandFeedback(text) {
        const pill = document.getElementById('voice-command-pill');
        const heardText = document.getElementById('voice-command-heard');
        if (pill && heardText) {
            heardText.textContent = `Heard: "${text}"`;
            pill.style.display = 'inline-flex';
            clearTimeout(this._pillTimer);
            this._pillTimer = setTimeout(() => {
                pill.style.display = 'none';
            }, 3500);
        }
    }

    updateMicToolbarState(listening) {
        const btn = document.getElementById('btn-toggle-mic');
        const textEl = document.getElementById('mic-btn-text');
        const iconEl = document.getElementById('mic-btn-icon');
        
        if (btn) {
            btn.setAttribute('aria-pressed', listening ? 'true' : 'false');
            if (listening) {
                btn.classList.add('voice-mic-active');
                if (textEl) textEl.textContent = 'Voice Commands: ON';
                if (iconEl) iconEl.setAttribute('data-lucide', 'mic');
            } else {
                btn.classList.remove('voice-mic-active');
                if (textEl) textEl.textContent = 'Voice Commands: OFF';
                if (iconEl) iconEl.setAttribute('data-lucide', 'mic-off');
            }
            if (window.lucide) window.lucide.createIcons();
        }
    }

    /**
     * Interactive Voice Commands Processor
     * Understands multilingual natural spoken instructions:
     * - Start / Stop camera navigation
     * - Switch default camera device
     * - Switch voice language (Hindi, Odia, English)
     * - Status / Summary / Mute / Dashboard
     */
    handleVoiceCommand(rawTranscript) {
        if (!rawTranscript) return;
        const cmd = rawTranscript.toLowerCase().trim();
        console.log("CrossEcho Voice Command Recognized:", cmd);
        this.showCommandFeedback(cmd);

        // 1. Language Commands ("Hindi", "Odia", "English", "Switch Language")
        if (cmd.includes('hindi') || cmd.includes('हिन्दी') || cmd.includes('hindee')) {
            this.playChime('action');
            this.setLanguage('hi');
            return;
        }
        if (cmd.includes('odia') || cmd.includes('oriya') || cmd.includes('ଓଡ଼ିଆ') || cmd.includes('oriyaa')) {
            this.playChime('action');
            this.setLanguage('or');
            return;
        }
        if (cmd.includes('english') || cmd.includes('अंग्रेजी') || cmd.includes('ଇଂରାଜୀ') || cmd.includes('angrezi')) {
            this.playChime('action');
            this.setLanguage('en');
            return;
        }
        if ((cmd.includes('language') || cmd.includes('bhasha') || cmd.includes('bhasa')) && 
            (cmd.includes('change') || cmd.includes('switch') || cmd.includes('next') || cmd.includes('badlo') || cmd.includes('badala'))) {
            this.playChime('action');
            this.cycleLanguage();
            return;
        }

        // 2. Camera Device Switching Commands ("switch camera", "change camera", "next camera", "camera badlo")
        const isCameraSwitch = 
            cmd.includes('switch camera') || cmd.includes('change camera') || cmd.includes('next camera') ||
            cmd.includes('toggle camera') || cmd.includes('other camera') || cmd.includes('swap camera') ||
            cmd.includes('flip camera') || cmd.includes('front camera') || cmd.includes('back camera') ||
            cmd.includes('rear camera') || cmd.includes('camera badlo') || cmd.includes('camera badala') ||
            (cmd.includes('camera') && (cmd.includes('switch') || cmd.includes('change') || cmd.includes('next') || cmd.includes('badlo') || cmd.includes('badala')));

        if (isCameraSwitch) {
            this.playChime('action');
            if (window.switchCameraDevice) {
                window.switchCameraDevice();
            } else {
                const msg = {
                    'en': "Camera switching is available on the navigation page.",
                    'hi': "कैमरा बदलने का विकल्प नेविगेशन पृष्ठ पर उपलब्ध है।",
                    'or': "କ୍ୟାମେରା ବଦଳାଇବା ନେଭିଗେସନ୍ ପୃଷ୍ଠାରେ ଉପଲବ୍ଧ।"
                };
                this.speak(msg[this.currentLanguage] || msg['en'], { priority: 'urgent' });
            }
            return;
        }

        // 3. Start Camera Navigation
        const isStart = 
            cmd.includes('start navigation') || cmd.includes('start camera') || cmd.includes('start stream') ||
            cmd.includes('open camera') || cmd.includes('turn on camera') || cmd === 'start' ||
            cmd.includes('navigation shuru') || cmd.includes('camera shuru') || cmd.includes('shuru karo') ||
            cmd.includes('chalu karo') || cmd.includes('arambha kara') || cmd.includes('arambha');

        if (isStart) {
            this.playChime('action');
            if (window.startCameraNavigation) {
                window.startCameraNavigation();
            } else {
                const startMsg = {
                    'en': "Launching Live Camera Navigation HUD.",
                    'hi': "लाइव कैमरा नेविगेशन शुरू हो रहा है।",
                    'or': "ଲାଇଭ୍ କ୍ୟାମେରା ନେଭିଗେସନ୍ ଆରମ୍ଭ ହେଉଛି।"
                };
                this.speak(startMsg[this.currentLanguage] || startMsg['en'], { priority: 'urgent', flush: true });
                setTimeout(() => {
                    window.location.href = '/detection';
                }, 400);
            }
            return;
        }

        // 4. Stop Camera Navigation
        const isStop = 
            cmd.includes('stop navigation') || cmd.includes('stop camera') || cmd.includes('stop stream') ||
            cmd.includes('close camera') || cmd.includes('turn off camera') || cmd === 'stop' ||
            cmd.includes('band karo') || cmd.includes('rok do') || cmd.includes('banda kara') ||
            cmd.includes('pause');

        if (isStop) {
            this.playChime('action');
            if (window.stopCameraNavigation) {
                window.stopCameraNavigation();
            } else {
                this.speak("Camera navigation is not running.", { priority: 'normal' });
            }
            return;
        }

        // 5. Status / Summary
        if (cmd.includes('status') || cmd.includes('summary') || cmd.includes('report') || cmd.includes('what do you see') || cmd.includes('saransh') || cmd.includes('saransa')) {
            this.playChime('action');
            this.readPageSummary();
            return;
        }

        // 6. Mute / Unmute
        if (cmd.includes('mute') || cmd.includes('unmute') || cmd.includes('silence') || cmd.includes('quiet')) {
            this.toggleVoice();
            return;
        }

        // 7. Dashboard Navigation
        if (cmd.includes('dashboard') || cmd.includes('home') || cmd.includes('main page')) {
            this.playChime('action');
            if (!window.location.pathname.endsWith('/dashboard')) {
                const dashMsg = {
                    'en': "Navigating to Operations Dashboard.",
                    'hi': "डैशबोर्ड पर जा रहे हैं।",
                    'or': "ଡ୍ୟାସବୋର୍ଡକୁ ଯାଉଛି।"
                };
                this.speak(dashMsg[this.currentLanguage] || dashMsg['en'], { priority: 'urgent', flush: true });
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 400);
            }
            return;
        }

        // 8. Help / Commands
        if (cmd.includes('help') || cmd.includes('command') || cmd.includes('what can i say') || cmd.includes('madad')) {
            this.playChime('action');
            const helpMsg = {
                'en': "Available voice commands: Start navigation, Stop navigation, Switch camera, Hindi, Odia, English, Status, or Dashboard.",
                'hi': "उपलब्ध आवाज कमांड: कैमरा शुरू करो, कैमरा बंद करो, कैमरा बदलो, हिन्दी, उड़िया, अंग्रेजी, सारांश, या डैशबोर्ड।",
                'or': "ଉପଲବ୍ଧ ଭଏସ୍ କମାଣ୍ଡ: କ୍ୟାମେରା ଆରମ୍ଭ କର, କ୍ୟାମେରା ବନ୍ଦ କର, କ୍ୟାମେରା ବଦଳାଅ, ହିନ୍ଦୀ, ଓଡ଼ିଆ, ଇଂରାଜୀ, ସାରାଂଶ, କିମ୍ବା ଡ୍ୟାସବୋର୍ଡ।"
            };
            this.speak(helpMsg[this.currentLanguage] || helpMsg['en'], { priority: 'urgent' });
            return;
        }
    }

    /**
     * Spatial 3D Stereo Audio Navigation Pulse
     * Uses Web Audio API's StereoPannerNode to position sound in user's left/right ear.
     * Works 100% offline with zero internet.
     */
    playDirectionalPulse(pan = 0.0, distance = 2.0, isUrgent = false) {
        if (!this.isEnabled) return;
        this.ensureAudioContext();
        if (!this.audioCtx) return;

        try {
            const ctx = this.audioCtx;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            let freq = 380;
            if (distance > 0 && distance < 1.0) freq = 880;
            else if (distance > 0 && distance < 2.0) freq = 580;
            else if (distance > 0 && distance < 3.5) freq = 440;

            osc.type = isUrgent ? 'sawtooth' : 'sine';
            osc.frequency.setValueAtTime(freq, ctx.currentTime);

            const duration = isUrgent ? 0.12 : 0.08;
            gain.gain.setValueAtTime(isUrgent ? 0.35 : 0.18, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);

            if (ctx.createStereoPanner) {
                const panner = ctx.createStereoPanner();
                const clampedPan = Math.max(-1.0, Math.min(1.0, pan));
                panner.pan.setValueAtTime(clampedPan, ctx.currentTime);
                osc.connect(gain);
                gain.connect(panner);
                panner.connect(ctx.destination);
            } else {
                osc.connect(gain);
                gain.connect(ctx.destination);
            }

            osc.start();
            osc.stop(ctx.currentTime + duration);
        } catch (e) {
            console.debug("Spatial audio pulse notice:", e);
        }
    }

    playTone(frequency, duration = 0.15, type = 'sine', gainVal = 0.2) {
        if (!this.isEnabled) return;
        this.ensureAudioContext();
        if (!this.audioCtx) return;

        try {
            const osc = this.audioCtx.createOscillator();
            const gain = this.audioCtx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(frequency, this.audioCtx.currentTime);

            gain.gain.setValueAtTime(gainVal, this.audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, this.audioCtx.currentTime + duration);

            osc.connect(gain);
            gain.connect(this.audioCtx.destination);

            osc.start();
            osc.stop(this.audioCtx.currentTime + duration);
        } catch (e) {
            console.debug("Audio tone error:", e);
        }
    }

    playChime(type) {
        if (!this.isEnabled) return;
        this.ensureAudioContext();

        if (type === 'welcome') {
            setTimeout(() => this.playTone(440, 0.2, 'triangle', 0.25), 0);
            setTimeout(() => this.playTone(554.37, 0.2, 'triangle', 0.25), 100);
            setTimeout(() => this.playTone(659.25, 0.35, 'sine', 0.3), 200);
        } else if (type === 'action') {
            this.playTone(600, 0.08, 'sine', 0.15);
        } else if (type === 'warning') {
            this.playTone(440, 0.1, 'sawtooth', 0.2);
            setTimeout(() => this.playTone(880, 0.15, 'sawtooth', 0.25), 100);
        } else if (type === 'danger') {
            this.playTone(880, 0.12, 'square', 0.35);
            setTimeout(() => this.playTone(880, 0.12, 'square', 0.35), 140);
        }
    }

    /**
     * Speaks text using offline speech synthesis with smart multilingual fallbacks.
     */
    speak(text, options = {}) {
        if (!this.isEnabled || !this.synth) return;
        if (!text || typeof text !== 'string') return;

        const cleanText = text.trim();
        if (!cleanText) return;

        const priority = options.priority || 'normal';
        const flush = options.flush || (priority === 'urgent');
        const cooldown = options.cooldown !== undefined ? options.cooldown : 2200;
        const lang = options.lang || this.currentLanguage;

        // Check phrase cooldown
        const now = Date.now();
        const lastSpokePhrase = this.phraseCooldowns.get(cleanText) || 0;
        if (priority !== 'urgent' && (now - lastSpokePhrase) < cooldown) {
            return;
        }

        this.phraseCooldowns.set(cleanText, now);
        this.lastSpokenText = cleanText;
        this.lastSpokenTime = now;

        if (flush) {
            this.synth.cancel();
        }

        const utterance = new SpeechSynthesisUtterance(cleanText);
        
        // Ensure voice is tuned to target language
        this.updateVoiceForLanguage(lang);
        if (this.selectedVoice) {
            utterance.voice = this.selectedVoice;
        }
        
        utterance.rate = options.rate || this.speechRate;
        utterance.volume = options.volume || this.speechVolume;
        utterance.pitch = options.pitch || 1.0;

        // Visual status pulse & self-echo suppression
        this.isSpeakingNow = true;
        this.pulseVoiceIndicator(true);

        const resetSpeaking = () => {
            this.pulseVoiceIndicator(false);
            setTimeout(() => {
                this.isSpeakingNow = false;
            }, 300);
        };

        utterance.onend = resetSpeaking;
        utterance.onerror = resetSpeaking;

        this.synth.speak(utterance);
    }

    pulseVoiceIndicator(speaking) {
        const indicator = document.getElementById('voice-guide-status');
        if (indicator) {
            if (speaking) {
                indicator.classList.add('voice-speaking');
            } else {
                indicator.classList.remove('voice-speaking');
            }
        }
    }

    toggleVoice() {
        this.isEnabled = !this.isEnabled;
        localStorage.setItem('crossecho_voice_enabled', this.isEnabled ? 'true' : 'false');
        
        if (!this.isEnabled && this.synth) {
            this.synth.cancel();
        }

        this.updateToolbarState();

        if (this.isEnabled) {
            this.playChime('action');
            const onMsg = {
                'en': "Voice guidance enabled.",
                'hi': "आवाज मार्गदर्शन चालू है।",
                'or': "ଭଏସ୍ ଗାଇଡ୍ ସକ୍ରିୟ ହେଲା।"
            };
            this.speak(onMsg[this.currentLanguage] || onMsg['en'], { flush: true, priority: 'urgent' });
        } else {
            this.playTone(300, 0.2, 'sine', 0.2);
        }
    }

    updateToolbarState() {
        const btn = document.getElementById('btn-toggle-voice-guide');
        const textEl = document.getElementById('voice-guide-btn-text');
        const iconEl = document.getElementById('voice-guide-btn-icon');
        
        if (btn) {
            btn.setAttribute('aria-pressed', this.isEnabled ? 'true' : 'false');
            if (this.isEnabled) {
                btn.classList.add('voice-active');
                if (textEl) textEl.textContent = 'Voice Guide: Active';
                if (iconEl) iconEl.setAttribute('data-lucide', 'volume-2');
            } else {
                btn.classList.remove('voice-active');
                if (textEl) textEl.textContent = 'Voice Guide: Muted';
                if (iconEl) iconEl.setAttribute('data-lucide', 'volume-x');
            }
            if (window.lucide) window.lucide.createIcons();
        }

        // Sync language selector dropdowns
        document.querySelectorAll('.language-select').forEach(sel => {
            sel.value = this.currentLanguage;
        });

        // Sync mic toolbar state
        this.updateMicToolbarState(this.isListening || this.micEnabled);
    }

    repeatLast() {
        if (this.lastSpokenText) {
            this.speak(this.lastSpokenText, { flush: true, priority: 'urgent' });
        } else {
            const noMsg = {
                'en': "No recent announcement to repeat.",
                'hi': "दोहराने के लिए कोई हालिया घोषणा नहीं है।",
                'or': "ଦୋହରାଇବା ପାଇଁ କୌଣସି ଘୋଷଣା ନାହିଁ।"
            };
            this.speak(noMsg[this.currentLanguage] || noMsg['en'], { flush: true });
        }
    }

    initKeyboardShortcuts() {
        window.addEventListener('keydown', (e) => {
            const tag = (e.target.tagName || '').toLowerCase();
            if (tag === 'input' || tag === 'textarea' || e.target.isContentEditable) {
                return;
            }

            const key = e.key.toUpperCase();

            // Toggle Voice Recognition Mic: 'V'
            if (key === 'V') {
                e.preventDefault();
                this.toggleSpeechRecognition();
            }
            // Cycle Language: 'L'
            else if (key === 'L') {
                e.preventDefault();
                this.cycleLanguage();
            }
            // Switch Camera Device: 'C'
            else if (key === 'C') {
                e.preventDefault();
                if (window.switchCameraDevice) {
                    window.switchCameraDevice();
                }
            }
            // Mute / Unmute: 'M'
            else if (key === 'M') {
                e.preventDefault();
                this.toggleVoice();
            }
            // Repeat last announcement: 'R'
            else if (key === 'R') {
                e.preventDefault();
                this.repeatLast();
            }
            // Read summary: 'S'
            else if (key === 'S') {
                e.preventDefault();
                this.readPageSummary();
            }
            // Jump to live navigation HUD: 'N' or Space (on dashboard)
            else if (key === 'N' || (e.code === 'Space' && window.location.pathname.includes('/dashboard'))) {
                e.preventDefault();
                this.speak("Launching Live Camera Navigation HUD.", { flush: true, priority: 'urgent' });
                this.playChime('action');
                setTimeout(() => {
                    window.location.href = '/detection';
                }, 400);
            }
            // Return to dashboard: 'D'
            else if (key === 'D' && !window.location.pathname.endsWith('/dashboard')) {
                e.preventDefault();
                this.speak("Navigating to Operations Dashboard.", { flush: true, priority: 'urgent' });
                this.playChime('action');
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 400);
            }
            // Help shortcuts: '?' or 'H'
            else if (e.key === '?' || key === 'H') {
                e.preventDefault();
                this.speak("Keyboard shortcuts: V for Voice Commands. C to switch Camera. L to switch Language between English, Hindi and Odia. Space to toggle Camera. S for Summary. M to mute. D for Dashboard.", { flush: true, priority: 'urgent' });
            }
        });
    }

    initAccessibilityNarration() {
        document.addEventListener('focusin', (e) => {
            const target = e.target;
            const speechText = target.getAttribute('data-speech') 
                || target.getAttribute('aria-label') 
                || (target.classList.contains('metric-card') ? target.innerText.replace(/\n+/g, ' ') : null);
            
            if (speechText) {
                this.speak(speechText, { cooldown: 1000, priority: 'normal' });
            }
        });

        document.addEventListener('click', (e) => {
            this.ensureAudioContext();
            const btn = e.target.closest('button, a, .metric-card');
            if (btn && !btn.id.includes('toggle-voice')) {
                this.playTone(520, 0.05, 'sine', 0.1);
            }
        });
    }

    readPageSummary() {
        const lang = this.currentLanguage;
        if (window.location.pathname.includes('/dashboard')) {
            const totalEl = document.querySelector('[data-stat="total"]');
            const todayEl = document.querySelector('[data-stat="today"]');
            const topEl = document.querySelector('[data-stat="top"]');

            const total = totalEl ? totalEl.textContent.trim() : '0';
            const today = todayEl ? todayEl.textContent.trim() : '0';
            const top = topEl ? topEl.textContent.trim() : 'None';

            let summary = "";
            if (lang === 'hi') {
                summary = `डैशबोर्ड सारांश। कुल दर्ज लॉग: ${total}। आज के स्कैन: ${today}। मुख्य बाधा: ${top}। कैमरा नेविगेशन शुरू करने के लिए Space दबाएं या बोलें शुरू करो।`;
            } else if (lang === 'or') {
                summary = `ଡ୍ୟାସବୋର୍ଡ ସାରାଂଶ। ମୋଟ ରେକର୍ଡ: ${total}। ଆଜିର ସ୍କାନ: ${today}। ମୁଖ୍ୟ ବାଧା: ${top}। କ୍ୟାମେରା ଆରମ୍ଭ ପାଇଁ Space ଦବାନ୍ତୁ କିମ୍ବା ଆରମ୍ଭ କର କୁହନ୍ତୁ।`;
                if (!this.hasNativeOdiaVoice()) {
                    summary = `Dashboard saransa. Mota record: ${total}. Ajira scan: ${today}. Mukhya badha: ${top}. Camera navigation pain Space dabantu kiba shuru karo kuhantu.`;
                }
            } else {
                summary = `Dashboard Summary. Total logs recorded: ${total}. Today's scans: ${today}. Dominant obstacle: ${top}. Say: Start navigation, or press Space.`;
            }
            this.speak(summary, { flush: true, priority: 'urgent', lang: lang });
        } else if (window.location.pathname.includes('/detection')) {
            const objCount = document.getElementById('obj-counter');
            const count = objCount ? objCount.textContent.trim() : '0';
            let summary = "";
            if (lang === 'hi') {
                summary = `लाइव नेविगेशन एचयूडी। वर्तमान में ${count} वस्तुओं को ट्रैक कर रहा है। कैमरा बदलने के लिए बोलें: कैमरा बदलो।`;
            } else if (lang === 'or') {
                summary = `ଲାଇଭ୍ ନେଭିଗେସନ୍ HUD. ବର୍ତ୍ତମାନ ${count} ବସ୍ତୁ ଟ୍ରାକ୍ କରୁଛି। କ୍ୟାମେରା ବଦଳାଇବାକୁ କୁହନ୍ତୁ କ୍ୟାମେରା ବଦଳାଅ।`;
                if (!this.hasNativeOdiaVoice()) {
                    summary = `Live Navigation HUD. Bartamana ${count} bastu track karuchhi. Camera badalaiba pain kuhantu: camera badala.`;
                }
            } else {
                summary = `Live Navigation HUD. Currently tracking ${count} objects. Say: Switch camera, or Stop navigation.`;
            }
            this.speak(summary, { flush: true, priority: 'urgent', lang: lang });
        } else {
            this.speak("CrossEcho Assistive System. Say: Start navigation, or press Space.", { flush: true, lang: lang });
        }
    }
}

// Global singleton instance
window.CrossEchoVoice = new CrossEchoVoiceAssistant();

document.addEventListener('DOMContentLoaded', () => {
    window.CrossEchoVoice.updateToolbarState();
    
    // Auto-welcome on dashboard
    if (window.location.pathname.includes('/dashboard')) {
        const welcomeUserEl = document.getElementById('dashboard-username');
        const username = welcomeUserEl ? welcomeUserEl.textContent.trim() : 'Operator';
        
        setTimeout(() => {
            window.CrossEchoVoice.playChime('welcome');
            const lang = window.CrossEchoVoice.currentLanguage;
            let welcomeMsg = `Welcome to CrossEcho Dashboard, ${username}. You can control navigation by speaking commands. Say: Start navigation, Switch camera, or change language.`;
            if (lang === 'hi') {
                welcomeMsg = `क्रॉसईको डैशबोर्ड में स्वागत है, ${username}। आप बोलकर भी नियंत्रित कर सकते हैं। कहिए: कैमरा शुरू करो, या कैमरा बदलो।`;
            } else if (lang === 'or') {
                welcomeMsg = `କ୍ରସ-ଇକୋ ଡ୍ୟାସବୋର୍ଡରେ ସ୍ଵାଗତ, ${username}। ଆପଣ ଭଏସ୍ କମାଣ୍ଡ ଦେଇପାରିବେ। କୁହନ୍ତୁ: କ୍ୟାମେରା ଆରମ୍ଭ, କିମ୍ବା କ୍ୟାମେରା ବଦଳାଅ।`;
                if (!window.CrossEchoVoice.hasNativeOdiaVoice()) {
                    welcomeMsg = `CrossEcho dashboard-re swagata, ${username}. Apana voice command dei paribe: camera arambha, kiba camera badala.`;
                }
            }
            window.CrossEchoVoice.speak(welcomeMsg, { priority: 'high', cooldown: 5000, lang: lang });
        }, 800);
    }
});
