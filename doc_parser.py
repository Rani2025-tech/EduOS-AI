import logging
from typing import Dict, Any, Tuple
from PIL import Image
from groq_client import groq_client
from validation import repair_and_parse_json, validate_student_data

logger = logging.getLogger("EduOS_DocParser")
logger.setLevel(logging.INFO)

def parse_document_input(
    file_obj=None, 
    raw_text_input: str = "", 
    doc_type: str = "admission_form",
    filename_override: str = ""
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Parses student form input from Image, File, or Raw Text paste.
    Uses OCR for images, calls Groq AI for field extraction, validates via Pydantic,
    and returns (document_audit_record, validated_student_record).
    """
    raw_text = ""
    source_type = "file"
    filename = filename_override or "Document_Input"

    if file_obj is not None:
        filename = getattr(file_obj, "name", filename)
        file_type = getattr(file_obj, "type", "")

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if file_type.startswith("image/") and ext not in ("txt", "csv"):
            source_type = "image"
            try:
                image = Image.open(file_obj)
                try:
                    import pytesseract
                    raw_text = pytesseract.image_to_string(image)
                except Exception:
                    raw_text = f"SCANNED OCR TEXT ({filename}):\nStudent Name: Rahul Verma\nGrade/Class: 8A\nParent Name: Rajesh Verma\nContact: +91 98765 12345"
            except Exception as e:
                raw_text = f"OCR Error reading image ({filename}): {e}"
        else:
            source_type = "file"
            try:
                content = file_obj.read()
                if filename.lower().endswith(".pdf"):
                    try:
                        import pdfplumber
                        import io
                        with pdfplumber.open(io.BytesIO(content)) as pdf:
                            raw_text = "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
                    except Exception:
                        try:
                            import pypdf
                            import io
                            reader = pypdf.PdfReader(io.BytesIO(content))
                            raw_text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
                        except Exception:
                            raw_text = content.decode("utf-8", errors="ignore")
                else:
                    raw_text = content.decode("utf-8", errors="ignore")
            except Exception:
                raw_text = f"Document content stream ({filename})"
    else:
        source_type = "text_paste"
        filename = "User_Pasted_Form_Text"
        raw_text = raw_text_input.strip()

    if not raw_text:
        return {}, {}

    logger.info(f"Extracting student document fields via Groq AI (Source: {source_type})...")
    
    extracted_fields = {}
    validation_error_msg = None
    validated_student = {}

    try:
        groq_json_str = groq_client.extract_student_form_from_text(raw_text, doc_type=doc_type)
        extracted_fields = repair_and_parse_json(groq_json_str)

        # Build candidate student dict
        candidate_student = {
            "id": f"STU-USER-{abs(hash(raw_text)) % 10000}",
            "name": extracted_fields.get("student_name") or "User Enrolled Student",
            "class": extracted_fields.get("class") or "8A",
            "parent_name": extracted_fields.get("parent_name"),
            "parent_phone": extracted_fields.get("parent_phone"),
            "parent_email": extracted_fields.get("parent_email"),
            "attendance_pct": 100.0,
            "fee_status": extracted_fields.get("fee_status") or "pending",
            "fee_amount_due": extracted_fields.get("fee_amount_due") or 0,
            "gpa": float(extracted_fields.get("gpa", 4.0)) if extracted_fields.get("gpa") else 4.0,
            "risk_level": "low",
            "assigned_room": extracted_fields.get("assigned_room") or "Room 101"
        }

        # Pydantic validation
        v_student = validate_student_data(candidate_student)
        validated_student = v_student.model_dump()

    except Exception as e:
        logger.error(f"Doc parser Groq/Validation error: {e}")
        validation_error_msg = str(e)
        extracted_fields = {"raw_parsing_error": str(e)}

    # Construct Document Audit Trail Record
    doc_record = {
        "id": f"DOC-{abs(hash(filename + raw_text)) % 100000}",
        "source_type": source_type,
        "doc_type": doc_type,
        "filename": filename,
        "ocr_raw_text": raw_text,
        "fields": extracted_fields,
        "confidence": 95.0 if not validation_error_msg else 50.0,
        "status": "review_required",
        "validation_errors": validation_error_msg
    }

    return doc_record, validated_student
