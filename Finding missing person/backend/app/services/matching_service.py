import sys , os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from AI.face_pipeline import generate_embedding


def find_candidates(image_path):

    # Generate embedding
    result = generate_embedding(image_path)

    if not result["success"]:
        return result

    embedding = result["embedding"]

    # Next:
    # 1. PostgreSQL connection
    # 2. Search using pgvector
    # 3. Fetch top 5 candidates
    # 4. Return candidates for human review

    return {
        "success": True,
        "message": "Embedding generated successfully",
        "dimension": len(embedding)
    }