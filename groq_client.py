import os
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("EduOS_GroqClient")
logger.setLevel(logging.INFO)

try:
    from groq import Groq
    HAS_GROQ_LIB = True
except ImportError:
    HAS_GROQ_LIB = False
    logger.warning("Groq library not installed.")

class GroqAIClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = "llama-3.3-70b-versatile"
        self.client = None

        if not self.api_key:
            logger.warning(
                "GROQ_API_KEY is not set. "
                "AI document extraction and timetable parsing will be unavailable. "
                "Set GROQ_API_KEY in your .env file."
            )
        elif HAS_GROQ_LIB:
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info("Groq API client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Groq API client: {e}")
                self.client = None

    def is_available(self) -> bool:
        return self.client is not None

    def _call_groq_json(self, system_prompt: str, user_text: str) -> str:
        """Sends a system and user prompt to Groq API with JSON object response enforcement."""
        if not self.is_available():
            raise RuntimeError("Groq API key is missing or client is unavailable.")

        try:
            logger.info(f"Sending prompt to Groq AI (Model: {self.model})")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            raw_output = response.choices[0].message.content
            logger.info("Groq AI response received successfully.")
            return raw_output
        except Exception as e:
            logger.error(f"Groq API call error: {e}")
            raise RuntimeError(f"Groq API Error: {str(e)}")

    def extract_student_form_from_text(self, raw_text: str, doc_type: str = "admission_form") -> Dict[str, Any]:
        """Extracts structured student/document JSON from raw OCR text using Groq LLM."""
        system_prompt = (
            "You are an AI information extraction engine for school administrative documents.\n"
            "Analyze the input text and extract all relevant student/document fields into a valid JSON object.\n"
            "Return JSON matching these keys:\n"
            "{\n"
            '  "student_name": "Full Name",\n'
            '  "class": "Class/Grade section e.g. 8A",\n'
            '  "parent_name": "Parent or Guardian Name",\n'
            '  "parent_phone": "Contact Phone Number",\n'
            '  "parent_email": "Email Address",\n'
            '  "fee_status": "paid or overdue or pending",\n'
            '  "fee_amount_due": integer_amount,\n'
            '  "gpa": float_gpa,\n'
            '  "assigned_room": "Room Number or Lab"\n'
            "}\n"
            "Output ONLY valid JSON. If a field is not present in the text, use null."
        )
        return self._call_groq_json(system_prompt, f"Document Type: {doc_type}\n\nDocument Raw Text:\n{raw_text}")

    def parse_teacher_availability_from_text(self, raw_text: str) -> Dict[str, Any]:
        """Parses user-defined teacher roster & availability text into structured JSON."""
        system_prompt = (
            "You are an AI assistant parsing teacher roster details and availability instructions for a school.\n"
            "Extract teacher information and specific availability constraints into a valid JSON object.\n"
            "Return JSON matching this exact structure:\n"
            "{\n"
            '  "teachers": [\n'
            '    {\n'
            '      "id": "TCH-01",\n'
            '      "name": "Dr. Sunita Mehta",\n'
            '      "subject": "Mathematics",\n'
            '      "email": "sunita.mehta@eduos.school",\n'
            '      "assigned_classes": "8A,8B",\n'
            '      "status": "active or absent"\n'
            '    }\n'
            '  ],\n'
            '  "availabilities": [\n'
            '    {\n'
            '      "teacher_name": "Dr. Sunita Mehta",\n'
            '      "day_of_week": "Monday",\n'
            '      "period": 3,\n'
            '      "status": "unavailable or available or preferred",\n'
            '      "notes": "Reason for unavailabilty"\n'
            '    }\n'
            '  ]\n'
            "}\n"
            "Output ONLY valid JSON."
        )
        return self._call_groq_json(system_prompt, f"Teacher Input Details:\n{raw_text}")

    def parse_timetable_slots_from_text(self, raw_text: str) -> Dict[str, Any]:
        """Parses user-defined timetable schedule text into structured timetable slots JSON."""
        system_prompt = (
            "You are an AI timetable schedule extractor.\n"
            "Extract timetable slots from the provided text into a valid JSON object.\n"
            "Return JSON matching this exact structure:\n"
            "{\n"
            '  "slots": [\n'
            '    {\n'
            '      "period": 1,\n'
            '      "time": "08:30 AM - 09:20 AM",\n'
            '      "class_name": "8A",\n'
            '      "subject": "Mathematics",\n'
            '      "teacher_name": "Dr. Sunita Mehta",\n'
            '      "room": "Room 201"\n'
            '    }\n'
            '  ]\n'
            "}\n"
            "Output ONLY valid JSON."
        )
        return self._call_groq_json(system_prompt, f"Raw Timetable Input:\n{raw_text}")

groq_client = GroqAIClient()
