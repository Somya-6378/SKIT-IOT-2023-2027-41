
from pathlib import Path

file_path = Path("large.jpg")

# Create an 11 MB test file
with file_path.open("wb") as file:
    file.write(b"0" * (11 * 1024 * 1024))

print("Test file created:", file_path)
print("File size:", file_path.stat().st_size)
