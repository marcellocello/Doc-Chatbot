import numpy as np
from app.embedder import embed_passages, embed_query

docs = [
    "Perintah SELECT digunakan untuk mengambil data dari tabel.",
    "Perintah DELETE menghapus baris pada tabel.",
    "Resep nasi goreng memakai bawang putih dan kecap manis.",
]

doc_vecs = np.array(embed_passages(docs))
print("Dimensi vector:", doc_vecs.shape[1])

query_vec = np.array(embed_query("bagaimana cara menampilkan data dari tabel?"))
scores = doc_vecs @ query_vec

for doc, score in sorted(zip(docs, scores), key=lambda x: -x[1]):
    print(f"{score:.3f}  {doc}")