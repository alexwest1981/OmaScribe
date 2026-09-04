import io
import wave
import threading
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal

try:
    import sounddevice as sd
except ImportError:
    sd = None

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

class DictationEngine(QObject):
    state_changed = pyqtSignal(str)  # "idle", "listening", "transcribing"
    audio_level = pyqtSignal(float)   # 0.0 to 1.0 for live mic meter
    transcription_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, config_mgr):
        super().__init__()
        self.config = config_mgr
        self.is_recording = False
        self._audio_buffer = []
        self._sample_rate = 16000
        self._stream = None
        self._whisper_model = None
        self._model_loading = False

    def _get_model(self):
        if self._whisper_model is None and WhisperModel is not None and not self._model_loading:
            try:
                self._model_loading = True
                model_size = self.config.get("dictation_model", "base")
                # Load on CPU with int8 quantization for instant performance
                self._whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
            except Exception as e:
                print(f"[Dictation] Error loading whisper model: {e}")
            finally:
                self._model_loading = False
        return self._whisper_model

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        if sd is None:
            self.error.emit("sounddevice library not installed.")
            return

        if self.is_recording:
            return

        self._audio_buffer = []
        self.is_recording = True
        self.state_changed.emit("listening")

        def audio_callback(indata, frames, time_info, status):
            if not self.is_recording:
                return
            mono = indata[:, 0]
            self._audio_buffer.append(mono.copy())
            rms = float(np.sqrt(np.mean(mono ** 2)))
            self.audio_level.emit(min(1.0, rms * 5.0))

        try:
            self._stream = sd.InputStream(
                samplerate=self._sample_rate,
                channels=1,
                dtype="float32",
                callback=audio_callback
            )
            self._stream.start()
        except Exception as e:
            self.is_recording = False
            self.state_changed.emit("idle")
            self.error.emit(f"Microphone error: {str(e)}")

    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self.state_changed.emit("transcribing")
        threading.Thread(target=self._transcribe_worker, daemon=True).start()

    def _transcribe_worker(self):
        if not self._audio_buffer:
            self.state_changed.emit("idle")
            return

        audio_data = np.concatenate(self._audio_buffer, axis=0)
        
        # Check if model available
        model = self._get_model()
        if model is not None:
            try:
                lang = self.config.get("dictation_lang", "auto")
                lang_param = None if lang == "auto" else lang
                segments, info = model.transcribe(audio_data, language=lang_param, beam_size=2)
                text = " ".join([seg.text.strip() for seg in segments])
                if text:
                    self.transcription_ready.emit(text)
            except Exception as e:
                self.error.emit(f"Transcription error: {str(e)}")
        else:
            # Fallback mock speech for development testing if faster-whisper not yet downloaded
            self.transcription_ready.emit(" [Dictation transcription ready] ")

        self.state_changed.emit("idle")
