import os
import requests
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv

load_dotenv()

class JobParser:
    def __init__(self):
        self.hh_base_url = "https://api.hh.ru"
        self.superjob_base_url = "https://api.superjob.ru/2.0"
        self.superjob_token = os.getenv("SUPERJOB_API_KEY")
        
    async def search_headhunter_jobs(self, keywords: str, location: str = None, salary_min: int = None) -> List[Dict]:
        """Search jobs on HeadHunter using their API."""
        url = f"{self.hh_base_url}/vacancies"
        
        params = {
            "text": keywords,
            "per_page": 50,
            "period": 1,  # Jobs posted in last 24 hours
            "order_by": "publication_time"
        }
        
        if location:
            # Get area ID for location
            area_id = await self._get_hh_area_id(location)
            if area_id:
                params["area"] = area_id
        
        if salary_min:
            params["salary"] = salary_min
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for item in data.get("items", []):
                job = await self._parse_hh_job(item)
                if job:
                    jobs.append(job)
            
            return jobs
            
        except Exception as e:
            print(f"Error searching HeadHunter jobs: {e}")
            return []
    
    async def search_superjob_jobs(self, keywords: str, location: str = None, salary_min: int = None) -> List[Dict]:
        """Search jobs on SuperJob using their API."""
        if not self.superjob_token:
            print("SuperJob API token not configured")
            return []
            
        url = f"{self.superjob_base_url}/vacancies/"
        
        headers = {
            "X-Api-App-Id": self.superjob_token,
            "Authorization": f"Bearer {self.superjob_token}"
        }
        
        params = {
            "keyword": keywords,
            "count": 50,
            "period": 1  # Last day
        }
        
        if location:
            params["town"] = location
        
        if salary_min:
            params["payment_from"] = salary_min
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for item in data.get("objects", []):
                job = await self._parse_superjob_job(item)
                if job:
                    jobs.append(job)
            
            return jobs
            
        except Exception as e:
            print(f"Error searching SuperJob jobs: {e}")
            return []
    
    async def search_all_jobs(self, keywords: str, location: str = None, salary_min: int = None) -> List[Dict]:
        """Search jobs on all configured job boards."""
        all_jobs = []
        
        # Search HeadHunter
        hh_jobs = await self.search_headhunter_jobs(keywords, location, salary_min)
        all_jobs.extend(hh_jobs)
        
        # Search SuperJob
        sj_jobs = await self.search_superjob_jobs(keywords, location, salary_min)
        all_jobs.extend(sj_jobs)
        
        # Remove duplicates based on title and company
        unique_jobs = []
        seen = set()
        
        for job in all_jobs:
            key = (job["title"].lower(), job["company"].lower())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    async def _parse_hh_job(self, item: Dict) -> Optional[Dict]:
        """Parse a single HeadHunter job item."""
        try:
            # Get detailed job information
            job_id = item["id"]
            detail_url = f"{self.hh_base_url}/vacancies/{job_id}"
            detail_response = requests.get(detail_url)
            detail_data = detail_response.json()
            
            salary_min = None
            salary_max = None
            salary_currency = None
            
            if item.get("salary"):
                salary_min = item["salary"].get("from")
                salary_max = item["salary"].get("to")
                salary_currency = item["salary"].get("currency")
            
            return {
                "title": item["name"],
                "company": item["employer"]["name"],
                "location": item["area"]["name"] if item.get("area") else None,
                "description": detail_data.get("description", ""),
                "requirements": detail_data.get("key_skills", []),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_currency": salary_currency,
                "source": "hh.ru",
                "external_id": job_id,
                "external_url": item["alternate_url"],
                "published_at": item["published_at"]
            }
            
        except Exception as e:
            print(f"Error parsing HeadHunter job: {e}")
            return None
    
    async def _parse_superjob_job(self, item: Dict) -> Optional[Dict]:
        """Parse a single SuperJob job item."""
        try:
            return {
                "title": item["profession"],
                "company": item["firm_name"],
                "location": item["town"]["title"] if item.get("town") else None,
                "description": item.get("candidat", ""),
                "requirements": item.get("candidat", ""),
                "salary_min": item.get("payment_from"),
                "salary_max": item.get("payment_to"),
                "salary_currency": item.get("currency", "RUR"),
                "source": "superjob.ru",
                "external_id": str(item["id"]),
                "external_url": item["link"],
                "published_at": datetime.fromtimestamp(item["date_published"]).isoformat()
            }
            
        except Exception as e:
            print(f"Error parsing SuperJob job: {e}")
            return None
    
    async def _get_hh_area_id(self, location: str) -> Optional[str]:
        """Get HeadHunter area ID for a location."""
        try:
            url = f"{self.hh_base_url}/areas"
            response = requests.get(url)
            areas = response.json()
            
            # Search for location in areas
            for country in areas:
                if country["name"] == "Россия":
                    for region in country["areas"]:
                        if location.lower() in region["name"].lower():
                            return region["id"]
                        for city in region.get("areas", []):
                            if location.lower() in city["name"].lower():
                                return city["id"]
            
            return None
            
        except Exception as e:
            print(f"Error getting area ID: {e}")
            return None