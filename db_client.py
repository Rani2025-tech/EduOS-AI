import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

logger = logging.getLogger("EduOS_DatabaseClient")
logger.setLevel(logging.INFO)

class DatabaseClient:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_key = os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")
        self.supabase: Optional[Client] = None
        self.is_supabase_active = False

        if self.supabase_url and self.supabase_key:
            self._connect_supabase(self.supabase_url, self.supabase_key)

    def _connect_supabase(self, url: str, key: str) -> bool:
        try:
            self.supabase_url = url
            self.supabase_key = key
            self.supabase = create_client(url, key)
            self.is_supabase_active = True
            logger.info("Supabase PostgreSQL client connected successfully.")
            return True
        except Exception as e:
            logger.error(f"Supabase connection error: {e}")
            self.is_supabase_active = False
            return False

    def set_supabase_credentials(self, url: str, key: str) -> bool:
        return self._connect_supabase(url, key)

    # ----------------------------------------------------
    # 1. Students CRUD
    # ----------------------------------------------------
    def get_students(self) -> List[Dict[str, Any]]:
        if not self.is_supabase_active or not self.supabase:
            return []
        try:
            res = self.supabase.table("students").select("*").order("created_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching students from Supabase: {e}")
            return []

    def upsert_student(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_supabase_active or not self.supabase:
            raise RuntimeError("Supabase client is disconnected.")
        try:
            res = self.supabase.table("students").upsert(student_data).execute()
            logger.info(f"Upserted student in Supabase: ID={student_data.get('id')}")
            return res.data[0] if res.data else student_data
        except Exception as e:
            logger.error(f"Error upserting student in Supabase: {e}")
            raise e

    def delete_student(self, student_id: str) -> bool:
        if not self.is_supabase_active or not self.supabase:
            return False
        try:
            self.supabase.table("students").delete().eq("id", student_id).execute()
            logger.info(f"Deleted student from Supabase: ID={student_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting student: {e}")
            return False

    # ----------------------------------------------------
    # 2. Teachers CRUD
    # ----------------------------------------------------
    def get_teachers(self) -> List[Dict[str, Any]]:
        if not self.is_supabase_active or not self.supabase:
            return []
        try:
            res = self.supabase.table("teachers").select("*").order("id").execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching teachers from Supabase: {e}")
            return []

    def upsert_teacher(self, teacher_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_supabase_active or not self.supabase:
            raise RuntimeError("Supabase client is disconnected.")
        try:
            res = self.supabase.table("teachers").upsert(teacher_data).execute()
            logger.info(f"Upserted teacher in Supabase: ID={teacher_data.get('id')}")
            return res.data[0] if res.data else teacher_data
        except Exception as e:
            logger.error(f"Error upserting teacher in Supabase: {e}")
            raise e

    # ----------------------------------------------------
    # 3. Teacher Availability CRUD
    # ----------------------------------------------------
    def get_teacher_availability(self) -> List[Dict[str, Any]]:
        if not self.is_supabase_active or not self.supabase:
            return []
        try:
            res = self.supabase.table("teacher_availability").select("*").order("created_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching teacher availability: {e}")
            return []

    def upsert_teacher_availability(self, avail_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_supabase_active or not self.supabase:
            raise RuntimeError("Supabase client is disconnected.")
        try:
            if not avail_data.get("id"):
                avail_data["id"] = f"AV-{abs(hash(str(avail_data))) % 100000}"
            res = self.supabase.table("teacher_availability").upsert(avail_data).execute()
            logger.info(f"Upserted teacher availability record in Supabase: ID={avail_data.get('id')}")
            return res.data[0] if res.data else avail_data
        except Exception as e:
            logger.error(f"Error upserting teacher availability: {e}")
            raise e

    # ----------------------------------------------------
    # 4. Timetable CRUD
    # ----------------------------------------------------
    def get_timetable(self) -> List[Dict[str, Any]]:
        if not self.is_supabase_active or not self.supabase:
            return []
        try:
            res = self.supabase.table("timetable").select("*").order("period", desc=False).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching timetable: {e}")
            return []

    def replace_timetable(self, slots: List[Dict[str, Any]]):
        if not self.is_supabase_active or not self.supabase:
            return
        try:
            # Delete existing slots safely
            self.supabase.table("timetable").delete().neq("id", "___NEQ_PLACEHOLDER___").execute()
            if slots:
                formatted_slots = []
                for s in slots:
                    s_copy = dict(s)
                    s_copy["has_conflict"] = bool(s_copy.get("has_conflict", False))
                    s_copy["is_substitute"] = bool(s_copy.get("is_substitute", False))
                    formatted_slots.append(s_copy)
                self.supabase.table("timetable").insert(formatted_slots).execute()
                logger.info(f"Replaced timetable in Supabase with {len(slots)} slots.")
        except Exception as e:
            logger.error(f"Error replacing timetable in Supabase: {e}")

    # ----------------------------------------------------
    # 5. Documents / Audit Trail CRUD
    # ----------------------------------------------------
    def get_documents(self) -> List[Dict[str, Any]]:
        if not self.is_supabase_active or not self.supabase:
            return []
        try:
            res = self.supabase.table("documents").select("*").order("created_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching documents: {e}")
            return []

    def insert_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_supabase_active or not self.supabase:
            raise RuntimeError("Supabase client is disconnected.")
        try:
            res = self.supabase.table("documents").upsert(doc_data).execute()
            logger.info(f"Saved document audit record in Supabase: ID={doc_data.get('id')}")
            return res.data[0] if res.data else doc_data
        except Exception as e:
            logger.error(f"Error saving document audit record: {e}")
            raise e

    def update_document(self, doc_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_supabase_active or not self.supabase:
            raise RuntimeError("Supabase client is disconnected.")
        try:
            res = self.supabase.table("documents").update(updates).eq("id", doc_id).execute()
            logger.info(f"Updated document status in Supabase: ID={doc_id}")
            return res.data[0] if res.data else updates
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            raise e

    # ----------------------------------------------------
    # 6. Alerts CRUD
    # ----------------------------------------------------
    def get_alerts(self) -> List[Dict[str, Any]]:
        if not self.is_supabase_active or not self.supabase:
            return []
        try:
            res = self.supabase.table("alerts").select("*").order("created_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return []

    def insert_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_supabase_active or not self.supabase:
            return alert_data
        try:
            res = self.supabase.table("alerts").upsert(alert_data).execute()
            return res.data[0] if res.data else alert_data
        except Exception as e:
            logger.error(f"Error inserting alert: {e}")
            return alert_data

    def resolve_alert(self, alert_id: str) -> bool:
        if not self.is_supabase_active or not self.supabase:
            return False
        try:
            self.supabase.table("alerts").update({"resolved": True}).eq("id", alert_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False

    # ----------------------------------------------------
    # 7. Insights CRUD
    # ----------------------------------------------------
    def get_insights(self) -> List[Dict[str, Any]]:
        if not self.is_supabase_active or not self.supabase:
            return []
        try:
            res = self.supabase.table("insights").select("*").order("created_at", desc=False).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching insights: {e}")
            return []

    # ----------------------------------------------------
    # 8. Copilot Messages CRUD
    # ----------------------------------------------------
    def get_copilot_messages(self) -> List[Dict[str, Any]]:
        if not self.is_supabase_active or not self.supabase:
            return []
        try:
            res = self.supabase.table("copilot_messages").select("*").order("created_at", desc=False).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching copilot messages: {e}")
            return []

    def insert_copilot_message(self, msg_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_supabase_active or not self.supabase:
            return msg_data
        try:
            res = self.supabase.table("copilot_messages").upsert(msg_data).execute()
            return res.data[0] if res.data else msg_data
        except Exception as e:
            logger.error(f"Error inserting copilot message: {e}")
            return msg_data

db_instance = DatabaseClient()
