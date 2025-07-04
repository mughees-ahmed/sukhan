from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer, util
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import asyncio
import json
import requests
import subprocess
import google.generativeai as genai
from dotenv import load_dotenv
import os 
from Levenshtein import distance
import re
import yt_dlp


# Load environment variables
def clean(text):
    return re.sub(r"[^a-zA-Z0-9\s]", "", text).lower()

load_dotenv()
model = SentenceTransformer('paraphrase-MiniLM-L6-v2', device='cpu')

# Utility functions
def similarity(s, f,model):
    # Clean inputs
    s = clean(s)
    f = clean(f)
    
    # Encode
    embeddings = model.encode([s, f], convert_to_tensor=True, normalize_embeddings=True)
    
    # Cosine similarity
    sim_score = util.cos_sim(embeddings[0], embeddings[1])
    return sim_score.item()


# Selenium setup
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    #chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins-discovery")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--incognito")
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def search_rekhta(driver, search_term):
    url = "https://www.rekhta.org"
    driver.get(url)

    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "search"))
    )
    search_box.send_keys(search_term)
    search_box.send_keys(Keys.ENTER)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "genricMatchCard"))
    )

    cards = driver.find_elements(
        By.XPATH, "//div[contains(@class, 'genricMatchCard')]//p/a"
    )
    heading = cards[0].text if cards else ""

    if similarity(search_term, heading,model) >= 0.7:  # <<< corrected threshold
        print("Similarity > 0.6: Proceeding with poetry extraction")
        for link in cards:
            if link.is_displayed():
                link.click()
                break

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "poemPageContentHeader"))
        )

        poem_name = driver.find_element(By.XPATH, "//div[contains(@class,'poemPageContentHeader')]/h1").text
        shayar = driver.find_element(By.XPATH, "//div[contains(@class,'authorAddFavorite  clearfix')]/h2").text

        print(f"\nPoem: {poem_name}\nShayar: {shayar}\n")

        poetry_lines = driver.find_elements(
            By.XPATH, "//div[contains(@class,'poemPageContent') or contains(@class,'poemPageContentUrdu')]//p"
        )
        for line in poetry_lines:
            text = line.text.strip()
            if text:
                print(text)

        return True
    else:
        print("No similar poetry found.")
        return False

def get_audio_url(video_url):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            return info_dict['url']  # Direct audio stream URL
    except Exception as e:
        print("❌ Error getting audio URL:", e)
        return None
    
def search_youtube_and_transcribe(query):
    try:
        driver = setup_driver()
        driver.get("https://www.youtube.com")

        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "search_query"))
        )
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        first_result = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a#video-title"))
        )
        video_url = first_result.get_attribute("href")
        driver.quit()

        if not video_url:
            print("❌ Could not find a YouTube video.")
            return None

        print(f"▶️ Found YouTube video: {video_url}")

        DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
        if not DEEPGRAM_API_KEY:
            print("❌ Deepgram API key not found in environment.")
            return None

        # yt-dlp command to get best audio to stdout
        ytdlp_cmd = [
            "yt-dlp",
            "-f", "bestaudio",
            "-o", "-",  # output to stdout
            video_url
        ]

        # ffmpeg command to convert input to WAV PCM 16kHz mono on stdout
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", "pipe:0",
            "-f", "wav",
            "-acodec", "pcm_s16le",
            "-ac", "1",
            "-ar", "16000",
            "pipe:1"
        ]

        # Start yt-dlp process
        ytdlp_proc = subprocess.Popen(ytdlp_cmd, stdout=subprocess.PIPE)

        # Start ffmpeg process, input from yt-dlp stdout
        ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdin=ytdlp_proc.stdout, stdout=subprocess.PIPE)

        # Close yt-dlp stdout in parent to allow process to receive SIGPIPE if ffmpeg exits
        ytdlp_proc.stdout.close()

        # Send audio from ffmpeg stdout to Deepgram API
        response = requests.post(
            "https://api.deepgram.com/v1/listen?punctuate=true",
            headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "audio/wav"
            },
            data=ffmpeg_proc.stdout
        )

        # Cleanup
        ffmpeg_proc.stdout.close()
        ffmpeg_proc.wait()
        ytdlp_proc.wait()

        if response.status_code != 200:
            print(f"❌ Deepgram API error {response.status_code}: {response.text}")
            return None

        result = response.json()
        if "results" in result:
            transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
            print("✅ Transcript:\n", transcript)
            return transcript
        else:
            print("❌ Deepgram response format error:", result)
            return None

    except Exception as e:
        print("❌ Error occurred:", e)
        return None


def transcribe_and_refine(raw_text):
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = (
            f"{raw_text}\n"
            "Refine and format this as proper Urdu poetry only.\n"
            "Remove any non-Urdu words or phrases.\n"
            "Correct any spelling or grammar errors.\n"
            "Give only the final clean Urdu poetry as output."
        )

        result = model.generate_content(prompt)
        print("\n📝 Refined Urdu Poetry:\n", result.text)

        return [{"content": line.strip()} for line in result.text.split("\n") if line.strip()]
    except Exception as e:
        print("🚨 Error in Gemini refinement:", e)
        return None


if __name__ == "__main__":
    try:
        search_term = input("Enter poetry: ")
        driver = setup_driver()
        result = search_rekhta(driver, search_term)
        if not result:
         print("Similarity < 0.6: Trying YouTube...")
         raw_text = search_youtube_and_transcribe(search_term)
         if raw_text:
             transcribe_and_refine(raw_text)
         else:
             print("❌ Could not find a YouTube video.")


    except Exception as e:
        print("Error:", e)
    finally:
        try:
            driver.quit()
        except:
            pass
