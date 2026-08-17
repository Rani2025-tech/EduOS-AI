import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

from env_config import get_missing_vars, validate_supabase_url

load_dotenv()

logger = logging.getLogger("EduOS_DatabaseClient")
logger.setLevel(logging.INFO)

# Connection status reasons — used by the UI to show a precise badge
DB_STATUS_MISSING_CONFIG = "missing_config"   # env vars not set
DB_STATUS_CONNECTED      = "connected"         # Supabase active
DB_STATUS_CONN_FAILED    = "connection_failed" # env vars set but connect failed

class DatabaseClient:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "").strip()
        self.supabase_key = (
            os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")
        ).strip()
        self.supabase: Optional[Client] = None
        self.is_supabase_active = False
        self.connection_status = DB_STATUS_MISSING_CONFIG
        self.config_errors: List[str] = []

        missing = get_missing_vars(for_db=True)
        if missing:
            self.config_errors = missing
            logger.warning(
                "Supabase credentials not found. Missing: %s. "
                "Set SUPABASE_URL and SUPABASE_KEY in your .env file. "
                "Copy .env.example to .env to get started.",
                ", ".join(missing),
            )
        else:
            url_error = validate_supabase_url(self.supabase_url)
            if url_error:
                self.config_errors = [url_error]
                logger.error(url_error)
                self.connection_status = DB_STATUS_CONN_FAILED
            else:
                self._connect_supabase(self.supabase_url, self.supabase_key)

    def _connect_supabase(self, url: str, key: str) -> bool:
        url_error = validate_supabase_url(url)
        if url_error:
            logger.error(url_error)
            self.is_supabase_active = False
            self.connection_status = DB_STATUS_CONN_FAILED
            self.config_errors = [url_error]
            return False
        try:
            self.supabase_url = url
            self.supabase_key = key
            self.supabase = create_client(url, key)
            # Live probe: a lightweight SELECT to confirm credentials are valid
            self.supabase.table("students").select("id").limit(1).execute()
            self.is_supabase_active = True
            self.connection_status = DB_STATUS_CONNECTED
            self.config_errors = []
            logger.info("Supabase PostgreSQL client connected successfully.")
            return True
        except Exception as e:
            logger.error("Supabase connection error: %s", e)
            self.is_supabase_active = False
            self.connection_status = DB_STATUS_CONN_FAILED
            self.config_errors = ["Connection probe failed — check URL, key, and RLS policies."]
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
            logger.warning("upsert_student skipped: Supabase not connected.")
            return student_data
        try:
            res = self.supabase.table("students").upsert(student_data).execute()
            logger.info(f"Upserted student in Supabase: ID={student_data.get('id')}")
            return res.data[0] if res.data else student_data
        except Exception as e:
            logger.error(f"Error upserting student in Supabase: {e}")
            return student_data

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
            logger.warning("upsert_teacher skipped: Supabase not connected.")
            return teacher_data
        try:
            res = self.supabase.table("teachers").upsert(teacher_data).execute()
            logger.info(f"Upserted teacher in Supabase: ID={teacher_data.get('id')}")
            return res.data[0] if res.data else teacher_data
        except Exception as e:
            logger.error(f"Error upserting teacher in Supabase: {e}")
            return teacher_data

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
            logger.warning("upsert_teacher_availability skipped: Supabase not connected.")
            return avail_data
        try:
            if not avail_data.get("id"):
                avail_data["id"] = f"AV-{abs(hash(str(avail_data))) % 100000}"
            res = self.supabase.table("teacher_availability").upsert(avail_data).execute()
            logger.info(f"Upserted teacher availability record in Supabase: ID={avail_data.get('id')}")
            return res.data[0] if res.data else avail_data
        except Exception as e:
            logger.error(f"Error upserting teacher availability: {e}")
            return avail_data

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
            logger.warning("insert_document skipped: Supabase not connected.")
            return doc_data
        try:
            res = self.supabase.table("documents").upsert(doc_data).execute()
            logger.info(f"Saved document audit record in Supabase: ID={doc_data.get('id')}")
            return res.data[0] if res.data else doc_data
        except Exception as e:
            logger.error(f"Error saving document audit record: {e}")
            return doc_data

    def update_document(self, doc_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_supabase_active or not self.supabase:
            logger.warning("update_document skipped: Supabase not connected.")
            return updates
        try:
            res = self.supabase.table("documents").update(updates).eq("id", doc_id).execute()
            logger.info(f"Updated document status in Supabase: ID={doc_id}")
            return res.data[0] if res.data else updates
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return updates

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

    # ----------------------------------------------------
    # 9. Users CRUD (Authentication)
    # ----------------------------------------------------
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Fetches a single user record by username. Returns None if not found."""
        if not self.is_supabase_active or not self.supabase:
            return None
        try:
            res = (
                self.supabase.table("users")
                .select("*")
                .eq("username", username)
                .eq("is_active", True)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error fetching user by username: {e}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetches a single user record by ID. Returns None if not found."""
        if not self.is_supabase_active or not self.supabase:
            return None
        try:
            res = (
                self.supabase.table("users")
                .select("*")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error fetching user by ID: {e}")
            return None

    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Inserts a new user record. Expects password_hash (never plaintext).
        Returns the created record or None on failure.
        """
        if not self.is_supabase_active or not self.supabase:
            logger.warning("create_user skipped: Supabase not connected.")
            return None
        if "password" in user_data:
            logger.error("create_user called with plaintext 'password' key — rejected.")
            return None
        try:
            res = self.supabase.table("users").insert(user_data).execute()
            logger.info(f"Created user in Supabase: ID={user_data.get('id')}, role={user_data.get('role')}")
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    def list_users(self) -> List[Dict[str, Any]]:
        """Returns all users (id, username, role, linked_id, is_active). Never returns password_hash."""
        if not self.is_supabase_active or not self.supabase:
            return []
        try:
            res = (
                self.supabase.table("users")
                .select("id, username, role, linked_id, is_active, created_at")
                .order("created_at")
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    def deactivate_user(self, user_id: str) -> bool:
        """Soft-deletes a user by setting is_active=False."""
        if not self.is_supabase_active or not self.supabase:
            return False
        try:
            self.supabase.table("users").update({"is_active": False}).eq("id", user_id).execute()
            logger.info(f"Deactivated user: ID={user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            return False

db_instance = DatabaseClient()
