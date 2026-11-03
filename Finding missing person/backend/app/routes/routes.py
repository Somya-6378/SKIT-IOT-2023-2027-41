
import os
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from app.db import get_db_connection

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Keep uploaded images outside the publicly served frontend folder.
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "private_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def error(message, status):
    return jsonify({"error": message}), status


# 1. POST /api/cases
@api_bp.post("/cases")
def create_case():
    data = request.get_json(silent=True) or {}

    person_name = data.get("person_name")
    case_number = data.get("case_number")

    if not isinstance(person_name, str) or not person_name.strip():
        return error("person_name is required", 400)

    if not isinstance(case_number, str) or not case_number.strip():
        return error("case_number is required", 400)

    try:
        age = data.get("age_years")
        if age is not None:
            age = int(age)
            if not 0 <= age <= 120:
                return error("age_years must be between 0 and 120", 400)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO missing_cases
                        (case_number, person_name, age_years,
                         gender, description, last_seen_location,
                         last_seen_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING case_id, case_number, person_name,
                              case_status, created_at
                    """,
                    (
                        case_number.strip(),
                        person_name.strip(),
                        age,
                        data.get("gender"),
                        data.get("description"),
                        data.get("last_seen_location"),
                        data.get("last_seen_at"),
                    ),
                )
                row = cur.fetchone()

        return jsonify({
            "message": "Case created",
            "case": {
                "case_id": row[0],
                "case_number": row[1],
                "person_name": row[2],
                "case_status": row[3],
                "created_at": row[4].isoformat(),
            },
        }), 201

    except Exception as exc:
        # Log the detailed error privately in a production application.
        print("create_case failed:", type(exc).__name__)
        return error("Could not create case. Check input and database.", 500)


# 2. POST /api/cases/<case_id>/photos
@api_bp.post("/cases/<int:case_id>/photos")
def upload_case_photo(case_id):
    uploaded = request.files.get("photo")

    if uploaded is None or not uploaded.filename:
        return error("Upload a file using the 'photo' field", 400)

    original_name = secure_filename(uploaded.filename)
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return error("Only JPG, JPEG, PNG and WEBP are allowed", 400)

    try:
        # Verify that the case exists.
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT case_id FROM missing_cases WHERE case_id = %s",
                    (case_id,),
                )
                if cur.fetchone() is None:
                    return error("Case not found", 404)

                # Generate a random storage name; don't trust the user filename.
                storage_name = f"{uuid.uuid4().hex}{extension}"
                storage_path = UPLOAD_DIR / storage_name

                uploaded.save(storage_path)

                try:
                    cur.execute(
                        """
                        INSERT INTO photos (case_id, storage_key)
                        VALUES (%s, %s)
                        RETURNING photo_id, case_id, uploaded_at
                        """,
                        (case_id, storage_name),
                    )
                    row = cur.fetchone()
                except Exception:
                    storage_path.unlink(missing_ok=True)
                    raise

        return jsonify({
            "message": "Photo uploaded",
            "photo": {
                "photo_id": row[0],
                "case_id": row[1],
                "uploaded_at": row[2].isoformat(),
            },
        }), 201

    except Exception as exc:
        print("upload_case_photo failed:", type(exc).__name__)
        return error("Could not upload photo", 500)


# 3. POST /api/searches
# This is a MOCK search, not real facial recognition.
@api_bp.post("/searches")
def create_search():
    data = request.get_json(silent=True) or {}
    query_photo_id = data.get("query_photo_id")

    if query_photo_id is None:
        return error("query_photo_id is required", 400)

    try:
        query_photo_id = int(query_photo_id)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT photo_id FROM photos WHERE photo_id = %s",
                    (query_photo_id,),
                )
                if cur.fetchone() is None:
                    return error("Query photo not found", 404)

                cur.execute(
                    """
                    INSERT INTO searches
                        (query_photo_id, search_status, completed_at)
                    VALUES (%s, 'completed', NOW())
                    RETURNING search_id, search_status, created_at
                    """,
                    (query_photo_id,),
                )
                search_row = cur.fetchone()

                # Demo candidates only. Scores are invented test data.
                cur.execute(
                    """
                    SELECT case_id, case_number, person_name
                    FROM missing_cases
                    WHERE case_status IN ('open', 'under_review')
                    ORDER BY case_id
                    LIMIT 3
                    """
                )
                candidates = cur.fetchall()

                results = []
                for index, candidate in enumerate(candidates):
                    demo_score = [0.91, 0.82, 0.76][index]

                    cur.execute(
                        """
                        INSERT INTO match_reviews
                            (search_id, candidate_case_id, similarity_score)
                        VALUES (%s, %s, %s)
                        RETURNING review_id
                        """,
                        (search_row[0], candidate[0], demo_score),
                    )
                    review_id = cur.fetchone()[0]

                    results.append({
                        "review_id": review_id,
                        "case_id": candidate[0],
                        "case_number": candidate[1],
                        "person_name": candidate[2],
                        "demo_score": demo_score,
                        "decision": "pending",
                        "note": "Mock candidate; not an AI match",
                    })

        return jsonify({
            "search_id": search_row[0],
            "search_status": search_row[1],
            "matches": results,
            "warning": "Demo results only. No face recognition was performed.",
        }), 201

    except (TypeError, ValueError):
        return error("query_photo_id must be an integer", 400)
    except Exception as exc:
        print("create_search failed:", type(exc).__name__)
        return error("Could not create search", 500)


# 4. GET /api/searches/<search_id>/matches
@api_bp.get("/searches/<int:search_id>/matches")
def get_matches(search_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT review_id, candidate_case_id,
                           similarity_score, decision, review_notes
                    FROM match_reviews
                    WHERE search_id = %s
                    ORDER BY similarity_score DESC NULLS LAST
                    """,
                    (search_id,),
                )
                rows = cur.fetchall()

        return jsonify({
            "search_id": search_id,
            "matches": [
                {
                    "review_id": row[0],
                    "case_id": row[1],
                    "demo_score": float(row[2]) if row[2] is not None else None,
                    "decision": row[3],
                    "review_notes": row[4],
                }
                for row in rows
            ],
        }), 200

    except Exception as exc:
        print("get_matches failed:", type(exc).__name__)
        return error("Could not retrieve matches", 500)


# 5. POST /api/matches/<review_id>/review
@api_bp.post("/matches/<int:review_id>/review")
def review_match(review_id):
    data = request.get_json(silent=True) or {}
    decision = data.get("decision")
    notes = data.get("review_notes")

    allowed_decisions = {"potential_match", "not_a_match", "verified_match"}
    if decision not in allowed_decisions:
        return error(
            "decision must be potential_match, not_a_match, or verified_match",
            400,
        )

    # Prototype only: production must obtain reviewer_id from
    # the authenticated session, never trust it from arbitrary client input.
    reviewer_id = data.get("reviewer_id")
    if reviewer_id is None:
        return error("reviewer_id is required for this prototype", 400)

    try:
        reviewer_id = int(reviewer_id)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT role FROM users
                    WHERE user_id = %s AND is_active = TRUE
                    """,
                    (reviewer_id,),
                )
                reviewer = cur.fetchone()

                if reviewer is None:
                    return error("Reviewer not found or inactive", 404)

                if reviewer[0] not in {"police", "admin"}:
                    return error("Only police/admin can review matches", 403)

                cur.execute(
                    """
                    UPDATE match_reviews
                    SET decision = %s,
                        reviewer_id = %s,
                        review_notes = %s,
                        reviewed_at = NOW()
                    WHERE review_id = %s
                    RETURNING review_id, decision, reviewed_at
                    """,
                    (decision, reviewer_id, notes, review_id),
                )
                row = cur.fetchone()

                if row is None:
                    return error("Match review not found", 404)

                cur.execute(
                    """
                    INSERT INTO audit_logs
                        (user_id, action, entity_type, entity_id)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        reviewer_id,
                        "review_match",
                        "match_review",
                        review_id,
                    ),
                )

        return jsonify({
            "message": "Review saved",
            "review_id": row[0],
            "decision": row[1],
            "reviewed_at": row[2].isoformat(),
        }), 200

    except (TypeError, ValueError):
        return error("reviewer_id must be an integer", 400)
    except Exception as exc:
        print("review_match failed:", type(exc).__name__)
        return error("Could not save review", 500)
