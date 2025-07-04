from django.shortcuts import render,redirect
from django.contrib.auth import authenticate
from django.contrib.auth .models import User
from poetry_app.models import *
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login
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
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer, util
from django.http import JsonResponse
from .bb import  (
    setup_driver, search_rekhta, similarity
    ,search_youtube_and_transcribe, transcribe_and_refine,clean)
# Load environment variables
load_dotenv()
def home_view(request):
    return render (request,'home.html')
def search_poetry(request):
    print("🔄 search_poetry() called")
    driver = None
    try:
        response_data = {}

        if request.method == 'POST':
            data = json.loads(request.body)
            search_term = data.get('search_term')
        elif request.method == 'GET':
            search_term = request.GET.get('q')
        else:
            return JsonResponse({'error': 'Unsupported HTTP method'}, status=405)

        print(f"\n🔍 Search term received: {search_term}")
        if not search_term:
            return JsonResponse({'error': 'No search term provided'}, status=400)

        driver = setup_driver()
        print("🚗 Driver setup complete!")

        poetry = search_rekhta(driver, search_term)
        print("📜 Poetry from Rekhta:", poetry)

        if poetry and isinstance(poetry, list) and any(p.get("content", "").strip() for p in poetry):
            print("✅ Rekhta poetry found.")
            response_data["results"] = poetry
        else:
            print("❌ Rekhta failed. Trying YouTube...")

            yt_poetry = search_youtube_and_transcribe(search_term)
            print("🎥 YouTube Transcription:", yt_poetry)

            if yt_poetry:
                refined_results = transcribe_and_refine( yt_poetry)
                if refined_results:
                    response_data["results"] = refined_results
                else:
                    print("😔 Refining failed.")
            else:
                print("😔 No YouTube results found.")

    except Exception as e:
        print("🔥 Caught error in search_poetry():", e)
        return JsonResponse({'error': str(e)}, status=500)

    finally:
        if driver:
            try:
                driver.quit()
            except Exception as ex:
                print("⚠️ Error while quitting driver:", ex)

    print(f"📦 Response data: {response_data}")
    return JsonResponse(response_data)