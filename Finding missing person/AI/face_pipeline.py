
from pathlib import Path

import cv2
import numpy as np
from deepface import DeepFace


# Selected face recognition model
MODEL_NAME = "Facenet512"

# Model output dimension
EMBEDDING_DIMENSION = 512

# Allowed image extensions
ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp"
}


def generate_embedding(image_path):

    image_path = Path(image_path)

    # 1. Check file existence
    if not image_path.exists():
        return {
            "success": False,
            "error": "Image file not found"
        }

    # 2. Check file extension
    if image_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return {
            "success": False,
            "error": "Invalid image format"
        }

    # 3. Check file size (maximum 10 MB)
    if image_path.stat().st_size > 10 * 1024 * 1024:
        return {
            "success": False,
            "error": "Image size must be below 10 MB"
        }

    # 4. Read image using OpenCV
    image = cv2.imread(str(image_path))

    if image is None:
        return {
            "success": False,
            "error": "Image could not be read"
        }

    # 5. Check image dimensions
    height, width = image.shape[:2]

    if height < 50 or width < 50:
        return {
            "success": False,
            "error": "Image resolution is too small"
        }
    max_dim = 1200 
    if max(height, width) > max_dim: 
        scale = max_dim / max(height, width)
        image = cv2.resize(image, (int(width * scale), int(height * scale)))
        height, width = image.shape[:2]
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l , a , b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        image = cv2.cvtColor(cv2.merge((l,a,b)), cv2.COLOR_LAB2BGR)
    try:

         # 6. Detect faces and generate embeddings
        raw_results = DeepFace.represent(
            img_path=image,
            model_name=MODEL_NAME,
            detector_backend="opencv",
            enforce_detection=True,
            align=True
        )

        
        img_area = height * width

       
        valid_faces = []
        for res in raw_results:
            area_info = res["facial_area"]
            face_area = area_info["w"] * area_info["h"]
            
            if face_area >= (0.015 * img_area):
                valid_faces.append(res)

        valid_faces.sort(key=lambda x: x["facial_area"]["w"] * x["facial_area"]["h"], reverse=True)

        face_results = []
        for res in valid_faces:
            x1, y1, w1, h1 = res["facial_area"]["x"], res["facial_area"]["y"], res["facial_area"]["w"], res["facial_area"]["h"]
            is_duplicate = False
            for kept in face_results:
                kx, ky, kw, kh = kept["facial_area"]["x"], kept["facial_area"]["y"], kept["facial_area"]["w"], kept["facial_area"]["h"]
                ix = max(0, min(x1 + w1, kx + kw) - max(x1, kx))
                iy = max(0, min(y1 + h1, ky + kh) - max(y1, ky))
                if (ix * iy) > 0.3 * (w1 * h1):
                    is_duplicate = True
                    break
            if not is_duplicate:
                face_results.append(res)

        # 7. Handle no face / multiple faces
        if len(face_results) == 0:
            return {
                "success": False,
                "error": "No clear face detected"
            }

        if len(face_results) > 1:
            return {
                "success": False,
                "error": "Multiple faces detected. Upload a photo with one face."
            }

        # 8. Extract embedding
        embedding = np.array(
            face_results[0]["embedding"],
            dtype=np.float32
        )

        # 9. Verify embedding dimension
        if embedding.shape != (EMBEDDING_DIMENSION,):
            return {
                "success": False,
                "error": "Unexpected embedding dimension"
            }

        if not np.all(np.isfinite(embedding)):
            return {
                "success": False,
                "error": "Invalid embedding values"
            }

        return {
            "success": True,
            "model_name": MODEL_NAME,
            "dimension": len(embedding),
            "embedding": embedding.tolist(),
            "face_region": face_results[0].get("facial_area")
        }

    except ValueError:
        return {
            "success": False,
            "error": "No usable face detected in the image"
        }

    except Exception as exc:
        print("Face pipeline error:", type(exc).__name__)

        return {
            "success": False,
            "error": "Face processing failed"
        }
