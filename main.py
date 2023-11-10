import cv2
import pyaudio, wave
import speech_recognition as sr

from shutil import move, rmtree
from os import listdir, path

from random import shuffle
from time import sleep

from unidecode import unidecode
from google_images_download import google_images_download


class SpeakImage:
	def __init__(self):
		# General
		self.out_dir = "downloads" # Output images directory
		self.audio_out_dir = 'output.wav'
		self.last_query = None

		# OpenCV
		self.window_name = "Funny Images" # [!] Window title
		self.MAX_SIZE = 200 # [!] Window size
		self.font = cv2.FONT_HERSHEY_SIMPLEX
		self.font_scale = 1
		self.font_thickness = self.font_scale * 2
		self.font_color = (0, 0, 255)

		# Audio
		self.r = sr.Recognizer() # Recognition
		self.CHUNK = 1024
		self.FORMAT = pyaudio.paInt16
		self.CHANNELS = 1
		self.RATE = 44100
		self.SECONDS = 2 # [!] Time of each record


	def _make_window(self):
		cv2.namedWindow(self.window_name, cv2.WND_PROP_FULLSCREEN) # Make window (this is just to resize it)
		cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
		cv2.resizeWindow(self.window_name, (self.MAX_SIZE, self.MAX_SIZE))

	def _calc_new_size(self, img) -> tuple[int]:
		org_h, org_w = img.shape[:2]
		return (min(self.MAX_SIZE, (org_w // 2)), max(self.MAX_SIZE, (org_h // 2)))

	def _put_text(self, img, top=False) -> tuple[int]:
		# Calc text size
		text_size = cv2.getTextSize(self.last_query, self.font, self.font_scale, self.font_thickness)[0]
		if top: # Calc position
			text_position = ((img.shape[1] - text_size[0]) // 2, text_size[1] + (text_size[1] // 2))
		else:
			text_position = ((img.shape[1] - text_size[0]) // 2, img.shape[0] - 10)
		cv2.putText(img, self.last_query, text_position, self.font, self.font_scale, self.font_color, self.font_thickness)

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
			self.last_query = unidecode(speak)
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


	def display(self, image, init=False):
		if init: # Window not inited
			self._make_window()

		img = cv2.imread(image)
		img = cv2.resize(img, (self.MAX_SIZE, self.MAX_SIZE)) # Resize image
		self._put_text(img)
		cv2.imshow(self.window_name, img)

		# Images not needed anymore delete it 
		# rmtree(path.join(self.out_dir, query))


if __name__ == '__main__':
	spk = SpeakImage()

	spk.display('init.jpg', init=True) # Init window
	while True:
		audio = spk.record_mic()
		rec   = spk.recognize_audio(audio)

		# Not recognized
		if not rec:
			continue

		image = spk.image(rec, 1) # Args: Text and [!] Images amount
		display = spk.display(image)

		if cv2.waitKey(1) == ord('q'):
			break
		sleep(2)
	cv2.destroyAllWindows()

