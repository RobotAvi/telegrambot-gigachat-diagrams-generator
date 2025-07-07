import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv
import openai
import anthropic

load_dotenv()

class LLMService:
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize OpenAI if API key is available
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            openai.api_key = openai_key
            self.openai_client = openai
        
        # Initialize Anthropic if API key is available
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
    
    async def analyze_resume(self, resume_text: str) -> Dict:
        """Analyze resume and extract structured information."""
        prompt = f"""
        Проанализируй следующее резюме и извлеки структурированную информацию в формате JSON:

        Резюме:
        {resume_text}

        Верни JSON с полями:
        - skills: список ключевых навыков
        - experience: список опыта работы с описанием
        - education: образование
        - key_competencies: основные компетенции
        - summary: краткое резюме в 2-3 предложениях
        - strengths: сильные стороны кандидата
        """
        
        response = await self._call_llm(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse LLM response", "raw_response": response}
    
    async def match_job_to_resume(self, job_description: str, resume_data: Dict) -> Dict:
        """Analyze how well a job matches the resume."""
        prompt = f"""
        Оцени соответствие вакансии резюме кандидата по шкале от 0 до 100.

        Данные резюме:
        {json.dumps(resume_data, ensure_ascii=False, indent=2)}

        Описание вакансии:
        {job_description}

        Верни JSON с полями:
        - match_score: оценка соответствия (0-100)
        - match_reasons: список причин соответствия
        - missing_skills: список недостающих навыков
        - recommendation: рекомендация (стоит ли подавать заявку)
        - cover_letter_hints: подсказки для сопроводительного письма
        """
        
        response = await self._call_llm(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse LLM response", "raw_response": response}
    
    async def generate_cover_letter(self, job_description: str, company: str, resume_data: Dict, user_name: str) -> str:
        """Generate a personalized cover letter."""
        prompt = f"""
        Создай персонализированное сопроводительное письмо для вакансии.

        Данные кандидата:
        - Имя: {user_name}
        - Резюме: {json.dumps(resume_data, ensure_ascii=False, indent=2)}

        Вакансия:
        - Компания: {company}
        - Описание: {job_description}

        Требования к письму:
        1. Профессиональный тон
        2. Упоминание конкретных навыков из резюме, релевантных для позиции
        3. Объяснение интереса к компании
        4. Длина 200-300 слов
        5. На русском языке

        Верни только текст письма без дополнительных комментариев.
        """
        
        return await self._call_llm(prompt)
    
    async def generate_hr_message(self, company: str, position: str, resume_data: Dict, user_name: str) -> str:
        """Generate a message to HR manager."""
        prompt = f"""
        Создай сообщение HR-менеджеру компании для установления контакта.

        Данные кандидата:
        - Имя: {user_name}
        - Резюме: {json.dumps(resume_data, ensure_ascii=False, indent=2)}

        Целевая позиция:
        - Компания: {company}
        - Позиция: {position}

        Требования к сообщению:
        1. Вежливый и профессиональный тон
        2. Краткость (100-150 слов)
        3. Упоминание ключевых навыков
        4. Просьба о рассмотрении кандидатуры
        5. На русском языке

        Верни только текст сообщения.
        """
        
        return await self._call_llm(prompt)
    
    async def _call_llm(self, prompt: str) -> str:
        """Call the available LLM service."""
        try:
            # Try OpenAI first
            if self.openai_client:
                response = await self.openai_client.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            # Try Anthropic if OpenAI is not available
            elif self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            else:
                return "LLM service not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY."
                
        except Exception as e:
            return f"Error calling LLM: {str(e)}"