import tkinter as tk
import pyaudio, wave
import speech_recognition as sr

from PIL import Image, ImageDraw, ImageFont, ImageTk

from shutil import move, rmtree
from os import listdir, path

from random import shuffle
from time import sleep

from unidecode import unidecode
from google_images_download import google_images_download



class SpeakImage:
	def __init__(self, title: str = "Funny Image", size: int = 200):
		# General
		self.out_dir = "downloads" # Output images directory
		self.audio_out_dir = 'output.wav'
		self.last_search = None

		# TKinter
		self.size = size
		self.label = None
		self.window = None
		self.font_color = (255, 0, 0)
		self.font_size = 32
		self.font = ImageFont.truetype("media/arial_bold.ttf", self.font_size)


		# Audio
		self.r = sr.Recognizer() # Recognition
		self.CHUNK = 1024
		self.FORMAT = pyaudio.paInt16
		self.CHANNELS = 1
		self.RATE = 44100
		self.SECONDS = 2 # [!] Time of each record

	def _resize_image(self, image):
		# Open and resize
		img = Image.open(image)
		img = img.resize((self.size, self.size), Image.LANCZOS)

		return img

	def _put_text(self, img) -> tuple[int]:
		width, height = img.size

		# Draw object to the image
		draw = ImageDraw.Draw(img)

		# Load font
		text_w, text_h = draw.textsize(self.last_search, font=self.font)

		# Calc text position
		x = (width - text_w) / 2
		y = height - text_h - self.font_size

		# Add to image
		draw.text((x, y), self.last_search, fill=self.font_color, font=self.font)
		pass

	def init_window(self, title: str = "Funny Images"):
		self.window = tk.Tk()	
		self.window.title(title)
		self.window.geometry(f'{self.size}x{self.size}')

		# Just to init
		self.label = tk.Label(self.window)
		self.label.pack()
		self.update_window()
	

	# Listen to mic instead of recording it
	def liste_mic(self):
		with sr.Microphone() as source:
			print("Say something")
			audio = self.r.listen(source)
		return audio

	def record_mic(self) -> str:
		p = pyaudio.PyAudio()
		stream = p.open(format=self.FORMAT,channels=self.CHANNELS, rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)
		
		print("Recording...")

		frames = []
		for i in range(0, int(self.RATE / self.CHUNK * self.SECONDS)):
			data = stream.read(self.CHUNK)
			frames.append(data)

		print("Record stopped")

		stream.stop_stream()
		stream.close()
		p.terminate()

		wf = wave.open(self.audio_out_dir, 'wb')
		wf.setnchannels(self.CHANNELS)
		wf.setsampwidth(p.get_sample_size(self.FORMAT))
		wf.setframerate(self.RATE)
		wf.writeframes(b''.join(frames))
		wf.close()

		with sr.AudioFile(self.audio_out_dir) as source:
			audio = self.r.record(source) # Red audio file
		return audio

	def recognize_audio(self, audio) -> str:
		try:
			speak = self.r.recognize_google(audio, language='pt-BR') # Recognize Mic speak
			self.last_search = unidecode(speak)
			print("=> Recognized " + speak)

			return unidecode(speak) # Remove accents and not english letters (e.g. = Alçapão => Alcapao)
		except sr.UnknownValueError:
			print("Google Speech Recognition could not understand audio")
		except sr.RequestError as e:
			print("Could not request results from Google Speech Recognition service; {0}".format(e))

		return None


	def image(self, query, limit=2) -> str:
		res = google_images_download.googleimagesdownload()

		# [!] You may want to un-comment some arg
		args = {
			"keywords": query,
			"limit": limit,
			"print_urls": False,
			"safe_search": True,
			"no_numbering": True, # Don't index prefix
			"output_directory": self.out_dir

			# "print_size": True,
			# "aspect_ratio": "square", # Get images with especific aspect ratio
			# "silent_mode": True # Don't show on terminal
			# "exact_size": "100, 100",

			# "no_directory": True, # OUT_DIR/QUERY/image.jpg -> OUT_DIR/image.jpg
			# "related_images": True, # I don't see difference
		}

		paths = res.download(args) # Download image
		
		# Get the name of all downloaded images
		image_names = [f for f in listdir(path.join(self.out_dir, query))]

		# Since the same query returns the images at the same order, a solution is to get more than 1 image and shuffle
		shuffle(image_names)

		# Return image path
		return f'{self.out_dir}/{query}/{image_names[0]}'

	def update_window(self):
		self.window.update_idletasks()

	def display(self, image, init=False):
		if init: # Window not inited
			self._make_window()
			return
		
		img = self._resize_image(image)
		self._put_text(img)
		img = ImageTk.PhotoImage(img)

		self.label.config(image=img)
		self.label.image = img




if __name__ == '__main__':
	# [!] Window size
	spk = SpeakImage("Funny Images", 200)
	
	# Init window
	# [!] Window title
	spk.init_window("Funny Images")
	while True:
		audio = spk.record_mic()
		rec   = spk.recognize_audio(audio)

		# Not recognized
		if not rec:
			continue

		image = spk.image(rec, 1) # Args: Text and [!] Images amount
		display = spk.display(image)

		spk.update_window()

