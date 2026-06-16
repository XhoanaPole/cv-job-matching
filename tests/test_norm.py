from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

emb = model.encode("Hello world", convert_to_numpy=True)
print("Norm:", np.linalg.norm(emb))