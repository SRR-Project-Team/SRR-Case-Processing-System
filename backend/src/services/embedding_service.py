from src.core.embedding import embed_text

def generate_embedding(text_chunks: list[str]) -> list[list[float]]:
    '''
    Generate a batch of embeddings for a list of text chunks, Return a list of embeddings vectors
    '''
    embeddings = []
    for chunk in text_chunks:
        vec = embed_text(chunk)
        embeddings.append(vec)
    return embeddings
