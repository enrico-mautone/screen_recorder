import cv2
import numpy as np
from PIL import ImageGrab
import threading
import pyaudio
import wave
import os
import time
from datetime import datetime
from moviepy import VideoFileClip, AudioFileClip


class ScreenRecorder:
    def __init__(self):
        self.recording = False
        self.exit_flag = False
        self.video_writer = None
        self.audio_frames = []
        self.audio_stream = None
        self.audio_thread = None
        self.frame_rate = 30  # Frequenza di acquisizione video (FPS)
        self.start_time = None

    def start_audio_recording(self):
        """
        Registra l'audio utilizzando PyAudio.
        """
        print("Audio recording started.")
        self.audio_frames = []
        audio_format = pyaudio.paInt16
        channels = 2
        rate = 44100
        chunk = 1024

        pa = pyaudio.PyAudio()
        self.audio_stream = pa.open(format=audio_format, channels=channels,
                                    rate=rate, input=True, frames_per_buffer=chunk)

        while self.recording:
            data = self.audio_stream.read(chunk)
            self.audio_frames.append(data)

        self.audio_stream.stop_stream()
        self.audio_stream.close()
        pa.terminate()
        print("Audio recording stopped.")

    def save_audio(self, file_name):
        """
        Salva l'audio registrato in un file WAV.
        """
        audio_format = pyaudio.paInt16
        channels = 2
        rate = 44100

        with wave.open(file_name, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(audio_format))
            wf.setframerate(rate)
            wf.writeframes(b''.join(self.audio_frames))

    def start_video_recording(self):
        """
        Registra lo schermo e salva il video.
        """
        screen_size = ImageGrab.grab().size
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_file = f"recording_{timestamp}.mp4"
        audio_file = f"audio_{timestamp}.wav"
        output_file = f"output_{timestamp}.mp4"
        self.video_writer = cv2.VideoWriter(video_file, fourcc, self.frame_rate, screen_size)

        print(f"Video recording started. File: {video_file}")
        self.audio_thread = threading.Thread(target=self.start_audio_recording)
        self.audio_thread.start()

        self.start_time = time.time()  # Timestamp iniziale
        while self.recording:
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            target_frame = int(elapsed_time * self.frame_rate)

            img = ImageGrab.grab()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.video_writer.write(frame)

        self.video_writer.release()
        self.save_audio(audio_file)
        self.combine_audio_video(video_file, audio_file, output_file)

        # Rimuovi file temporanei
        os.remove(video_file)
        os.remove(audio_file)
        print(f"File temporanei rimossi: {video_file}, {audio_file}")

        print(f"Video con audio salvato: {output_file}")

    def combine_audio_video(self, video_file, audio_file, output_file):
        """
        Combina il video e l'audio in un unico file MP4.
        """
        video_clip = VideoFileClip(video_file)
        audio_clip = AudioFileClip(audio_file)
        final_clip = video_clip.with_audio(audio_clip)
        final_clip.write_videofile(output_file, fps=self.frame_rate, codec="libx264", audio_codec="aac")

    def stop_recording(self):
        """
        Ferma la registrazione.
        """
        if self.recording:
            self.recording = False
            if self.audio_thread:
                self.audio_thread.join()

    def exit_program(self):
        """
        Termina il programma interrompendo eventuali registrazioni in corso.
        """
        self.exit_flag = True
        self.stop_recording()


def main():
    recorder = ScreenRecorder()

    print("Comandi disponibili: 'rec' per avviare la registrazione, 'stop' per fermarla, 'exit' per uscire.")
    while not recorder.exit_flag:
        command = input("Inserisci un comando: ").strip().lower()

        if command == "rec" and not recorder.recording:
            recorder.recording = True
            recording_thread = threading.Thread(target=recorder.start_video_recording)
            recording_thread.start()

        elif command == "stop" and recorder.recording:
            recorder.stop_recording()

        elif command == "exit":
            recorder.exit_program()
            print("Uscita dal programma.")
            break

        else:
            print("Comando non valido. Usa 'rec', 'stop' o 'exit'.")


if __name__ == "__main__":
    main()
