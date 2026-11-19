
from AI.face_pipeline import generate_embedding

image_path = "test_images/person1.jpg"

result = generate_embedding(image_path)

if result["success"]:

    print("Face detected successfully!")

    print("Model:", result["model_name"])

    print("Embedding dimension:", result["dimension"])

    print("First 10 embedding values:")

    print(result["embedding"][:10])

else:

    print("Error:", result["error"])
