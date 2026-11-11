import pyttsx3
import threading
import time

class AudioGuide:
    def __init__(self):
        """
        Initializes the pyttsx3 TTS engine in a background thread 
        so it doesn't block the video stream.
        """
        self.speech_queue = []
        self.is_speaking = False
        
        # Start a daemon thread to process the speech queue
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()

    def _speech_worker(self):
        # Engine must be initialized in the thread that uses it
        self.engine = pyttsx3.init()
        # Optimize voice settings for navigation (faster, clear)
        self.engine.setProperty('rate', 160)
        self.engine.setProperty('volume', 1.0)
        
        while True:
            if self.speech_queue:
                text = self.speech_queue.pop(0)
                self.is_speaking = True
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"TTS Error: {e}")
                self.is_speaking = False
            else:
                time.sleep(0.1)

    def speak(self, text, flush=False):
        """
        Adds text to the speech queue.
        If flush is True, clears existing queue to prioritize this message.
        """
        if isinstance(text, dict):
            text = text.get('spoken_text') or text.get('text') or ''
        text = str(text).strip()
        if not text:
            return

        if flush:
            self.speech_queue.clear()
            
        if len(self.speech_queue) < 3: # prevent massive backlog
            self.speech_queue.append(text)

    def update_settings(self, rate=150, volume=1.0):
        # Note: changing properties in a different thread requires careful handling,
        # but for this prototype, we'll keep it simple and restart if needed, 
        # or handle properties inside the queue.
        pass
