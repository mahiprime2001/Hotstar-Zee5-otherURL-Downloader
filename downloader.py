try:
	import requests
	import sys
	from webdriver_manager.chrome import ChromeDriverManager

	from selenium import webdriver
	from selenium.webdriver.support.ui import WebDriverWait
	from selenium.webdriver.support import expected_conditions as EC
	
	from multiprocessing.pool import ThreadPool
	import tqdm
	import os 
	from pytube import YouTube
	import youtube_dl
	import subprocess
	import json
 
 
except:
	print("Some packages are missing, \n command to install packages is follow")
	print("python -m pip install selenium webdriver_manager requests tqdm")
	print("Trying to install the missing modules...")
	os.system("pip install selenium webdriver_manager requests tqdm pytube requests shutil youtube_dl subprocess json")
	print("run the code again...")
	exit(0)

browser_url = ""

print("\n------ Video Stream Downloader ------\n")
print("Supported sites:\n")
print("1. Hotstar - Supports to download all videos. just you need to get premium account in order to download premium videos\n")
print("2. Youtube- Supports to download all videos. Just you need to get the url link and everything will be done all by it's self.\n")
print("3. zee5 - Supports to download all videos. just you need to get premium account in order to download premium videos")

currentFile = __file__
realPath = os.path.realpath(currentFile)
dirPath = os.path.dirname(realPath)
dirName = os.path.basename(dirPath)
ytdlp = dirPath + "/binaries/yt-dlp.exe"
aria2c = dirPath + "/binaries/aria2c.exe"
mkvmerge = dirPath + "/binaries/mkvmerge.exe"



while True:
    
	if len(sys.argv) > 1:
		browser_url = sys.argv[1]
		print("\nEnter video url:", browser_url)
	else:
		browser_url = input("\nEnter video url: ")

	print("Once the browser will start playing video then your download will start")
	print("-------------------------------------")



	hotstar_link= "https://www.hotstar.com/in"
	youtub_link= "https://www.youtube.com/"	
	zee5_link = "https://www.zee5.com/"
	mdisk_link= "https://mdisk.me/"



	def Download(link):
		youtubeObject = YouTube(link)
		youtubeObject = youtubeObject.streams.get_highest_resolution()
		try:
			youtubeObject.download()
		except:
			print("An error has occurred")
		print("Download is completed successfully")



	if hotstar_link in browser_url:

		THREADS = 5
		MAX_RETRIES = 5

		browser = webdriver.Chrome(ChromeDriverManager().install())
		browser.get(browser_url)
		threadPool = ThreadPool(processes = THREADS)

		def is_video_exist(args):
			network_logs = browser.execute_script("var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {}; var network = performance.getEntries() || {}; return network;")
			for network_log in network_logs:
				name = network_log.get("name", "")
				if name[-9:] == "seg-1.m4s" and "video" in name:
					return name
			return False	

		def is_audio_exist(args):
			network_logs = browser.execute_script("var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {}; var network = performance.getEntries() || {}; return network;")
			for network_log in network_logs:
				name = network_log.get("name", "")
				if name[-9:] == "seg-1.m4s" and "audio" in name:
					return name
			return False

		print("-------------------------------------")
		print("\nFetching video link")
		video_url_link = WebDriverWait(browser, 300).until(is_video_exist).replace("seg-1.m4s", "seg-<URL_REPLACER>.m4s", 1)
		audio_url_link = WebDriverWait(browser, 300).until(is_audio_exist).replace("seg-1.m4s", "seg-<URL_REPLACER>.m4s", 1)
		title = browser.title
		bad_chars = [';', ':', '!', "*", "?", "|"] 
		for i in bad_chars:
			title = title.replace(i, '')
		video_file_name = title + "_video.mp4"
		audio_file_name = title + "_audio.mp4"
		print("Fetching url completed for: " , video_file_name)


		browser.get(video_url_link.replace("<URL_REPLACER>", "1", 1))
		headers = {
			'origin': 'https://www.hotstar.com',
			'referer': 'https://www.hotstar.com/'
		}

		cookies = {}
		for cookie in browser.get_cookies():
			cookies[cookie.get("name")] = cookie.get("value")
		headers['cookie'] = "; ".join([str(x)+"="+str(y) for x,y in cookies.items()])

		browser.close()

		def get_content_from_url(content_url):
			content = b''
			r = requests.request("GET", content_url, headers=headers, data={}, stream=True)
			for chunk in r.iter_content(chunk_size=8192):
				content += chunk
			return r.status_code, content

		def get_last_index(content_url, index=1, increment = 1000):
			r1 = requests.request("HEAD", content_url.replace("<URL_REPLACER>", str(index), 1), headers=headers, data={}, stream=True)
			r2 = requests.request("HEAD", content_url.replace("<URL_REPLACER>", str(index + 1), 1), headers=headers, data={}, stream=True)
			if r1.status_code == 200 and r2.status_code == 200:
				return get_last_index(content_url, index + increment, increment)
			elif r1.status_code == 404 and r2.status_code == 404:
				if increment > 1:
					increment //= 2
				return get_last_index(content_url, index - increment, increment)
			elif r1.status_code == 200 and r2.status_code == 404:
				return index

		def download_file(content_url):
			retries_index = 0
			while True:
				status_code, content = get_content_from_url(content_url)
				if status_code == 200:
					return content
				elif retries_index > MAX_RETRIES:
					raise RuntimeError("Max retries failed")
				retries_index += 1


		last_index = get_last_index(video_url_link)

		def download_files(file_name, content_url):
			threads = []
			threads.append(threadPool.apply_async(download_file, (content_url.replace("seg-<URL_REPLACER>.m4s", "init.mp4", 1),)))

			for index in range(1, last_index +1):
				threads.append(threadPool.apply_async(download_file, (content_url.replace("<URL_REPLACER>", str(index), 1),)))

			file = open(file_name, 'wb')
			for i in tqdm.tqdm(range(len(threads))):
				file.write(threads[i].get())
			file.close()



		print("\nDownloading video")
		download_files(video_file_name, video_url_link)

		print("\nDownloading audio")
		download_files(audio_file_name, audio_url_link)

		print("\nDownload complete ...")
		print(video_file_name)
		print(audio_file_name)
		print("\n\n Encrypting the video....\n\n")

		output_name= title+".mp4"

		os.system("mkvmerge -o \""+output_name+"\" -A \""+video_file_name+"\" \""+audio_file_name+"\"")
		print("\n\t The Video has Successfully Downloaded\n\t")
  
		for f in os.listdir():
			if f.endswith("_audio.mp4") or f.endswith("_video.mp4"):
				os.remove(f)
  
	elif zee5_link in browser_url:
		THREADS = 5
		MAX_RETRIES = 5

		browser = webdriver.Chrome(ChromeDriverManager().install())
		browser.get(browser_url)
		threadPool = ThreadPool(processes = THREADS)
		def is_video_exist(args):
			network_logs = browser.execute_script("var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {}; var network = performance.getEntries() || {}; return network;")
			for network_log in network_logs:
				name = network_log.get("name", "")
				if name[-9:] == "seg-1.m4s" and "video/" in name:
					return name
			return False	

		def is_audio_exist(args):
			network_logs = browser.execute_script("var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {}; var network = performance.getEntries() || {}; return network;")
			for network_log in network_logs:
				name = network_log.get("name", "")
				if name[-9:] == "seg-1.m4s" and "audio/" in name:
					return name
			return False

		print("-------------------------------------")
		print("\nFetching video link")
		video_url_link = WebDriverWait(browser, 300).until(is_video_exist).replace("seg-1.m4s", "seg-<URL_REPLACER>.m4s", 1)
		audio_url_link = WebDriverWait(browser, 300).until(is_audio_exist).replace("seg-1.m4s", "seg-<URL_REPLACER>.m4s", 1)
		title = browser.title
		bad_chars = [';', ':', '!', "*", "?", "|"] 
		for i in bad_chars:
			title = title.replace(i, '')
		video_file_name = title + "_video.mp4"
		audio_file_name = title + "_audio.mp4"
		print("Fetching url completed for: " , video_file_name)


		browser.get(video_url_link.replace("<URL_REPLACER>", "1", 1))
		headers = {
			'origin': 'https://www.zee5.com/',
			'referer': 'https://www.zee5.com/'
				}

		cookies = {}
		for cookie in browser.get_cookies():
					cookies[cookie.get("name")] = cookie.get("value")
		headers['cookie'] = "; ".join([str(x)+"="+str(y) for x,y in cookies.items()])

		browser.close()

		def get_content_from_url(content_url):
				content = b''	
				r = requests.request("GET", content_url, headers=headers, data={}, stream=True)
				for chunk in r.iter_content(chunk_size=8192):	
						content += chunk
						return r.status_code, content

		def get_last_index(content_url, index=1, increment = 1000):
					r1 = requests.request("HEAD", content_url.replace("<URL_REPLACER>", str(index), 1), headers=headers, data={}, stream=True)
					r2 = requests.request("HEAD", content_url.replace("<URL_REPLACER>", str(index + 1), 1), headers=headers, data={}, stream=True)
					if r1.status_code == 200 and r2.status_code == 200:
						return get_last_index(content_url, index + increment, increment)
					elif r1.status_code == 404 and r2.status_code == 404:
						if increment > 1:
							increment //= 2
						return get_last_index(content_url, index - increment, increment)
					elif r1.status_code == 200 and r2.status_code == 404:
						return index

		def download_file(content_url):
					retries_index = 0
					while True:
						status_code, content = get_content_from_url(content_url)
						if status_code == 200:
							return content
						elif retries_index > MAX_RETRIES:
							raise RuntimeError("Max retries failed")
						retries_index += 1


		last_index = get_last_index(video_url_link)

		def download_files(file_name, content_url):
					threads = []
					threads.append(threadPool.apply_async(download_file, (content_url.replace("seg-<URL_REPLACER>.m4s", "init.mp4", 1),)))

					for index in range(1, last_index +1):
						threads.append(threadPool.apply_async(download_file, (content_url.replace("<URL_REPLACER>", str(index), 1),)))

					file = open(file_name, 'wb')
					for i in tqdm.tqdm(range(len(threads))):
						file.write(threads[i].get())
					file.close()



		print("\nDownloading video")
		download_files(video_file_name, video_url_link)

		print("\nDownloading audio")
		download_files(audio_file_name, audio_url_link)

		print("\nDownload complete ...")
		print(video_file_name)
		print(audio_file_name)
		print("\n\n Encrypting the video....\n\n")

		output_name= title+".mp4"

		os.system("mkvmerge -o \""+output_name+"\" -A \""+video_file_name+"\" \""+audio_file_name+"\"")
		print("\n\t The Video has Successfully Downloaded\n\t")
		
		for f in os.listdir():
			if f.endswith("_audio.mp4") or f.endswith("_video.mp4"):
						os.remove(f)

 
	elif youtub_link in browser_url :
		Download(browser_url)
  
	else:
		with youtube_dl.YoutubeDL() as ydl:
    			ydl.download([browser_url])
    
       





  


				
