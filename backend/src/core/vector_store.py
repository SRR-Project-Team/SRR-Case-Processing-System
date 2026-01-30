import asyncio
import logging
import pandas as pd
from surrealdb import AsyncWsSurrealConnection

# SurrealDB Synchronous Encapsulation (Core: Asynchronous → Synchronous)
# Core idea: Convert asynchronous operations into synchronous operations, use asyncio.run() to execute asynchronous code
class SurrealDBSyncClient:
    _SURREALDB_CASE_ID = "tree_case_all"

    def __init__(self, persist_path: str):
        self.persist_path = persist_path
        self.namespace = "tree_case_ns"
        self.database = "tree_case_db"
        self.user = "root"
        self.password = "root"
        # start DB cmd 
        self._start_surrealdb_if_needed()
    
    def _start_surrealdb_if_needed(self):
        import subprocess
        import time
        # check if port 8000 is used
        try:
            subprocess.run(["pkill","-f","surreal start"], check=False)
            subprocess.Popen(
                [
                    "surreal", "start",
                    "--allow-all",
                    "--unauthenticated",
                    f"file://{self.persist_path}"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # wait for DB to start
            time.sleep(2)
            logging.info(f"SurrealDB started successfully")
        except Exception as e:
            logging.error(f"Error start SurrealDB: {e}")


    async def _async_connect(self) -> AsyncWsSurrealConnection:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db = AsyncWsSurrealConnection(url="ws://127.0.0.1:8000/rpc")
                await db.connect()
                await db.use(self.namespace, self.database)
                await db.query("""
                    DEFINE TABLE vector SCHEMALESS;
                    DEFINE FIELD case_id ON vector TYPE string;
                    DEFINE FIELD content ON vector TYPE string;
                    DEFINE FIELD vector ON vector TYPE array<float>;
                    DEFINE FIELD create_time ON vector TYPE string;
                """)
                return db
            except Exception as e:
                logging.warning(f"SurrealDB 连接失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise e


    # vector add operation
    async def _async_add_vectors(self, text_chunks: list[str], embeddings: list[list[float]]):
        db = await self._async_connect()
        # batch insert
        for i,(chunk, vec) in enumerate(zip(text_chunks, embeddings)):
            await db.query(f"""
                INSERT INTO vector (case_id, content, vector, create_time)
                VALUES $data 
            """, { "data" :{"case_id": self._SURREALDB_CASE_ID, 
                       "content": chunk, 
                       "vector": vec, 
                       "create_time": pd.Timestamp.now().isoformat()
                   }
            })
        await db.close()
    
    async def _async_retrieve_similar(self, query_vector: list[float], top_k: int):
        db = await self._async_connect()
        # cosine similarity search
        results = await db.query(f"""
            SELECT content, vector::similarity::cosine(vector, $query_vec) as similarity
            FROM vector
            WHERE case_id = $case_id
            ORDER BY similarity DESC
            LIMIT $top_k
        """, {
            "query_vec": query_vector,
            "case_id": self._SURREALDB_CASE_ID,
            "top_k": top_k
        })
        ret_docs = []
        if results:
            for item in results:
                ret_docs.append({
                    "content": item["content"],
                    "similarity": round(float(item["similarity"]), 3) 
                })
        await db.close()
        return ret_docs
    
    # Purely synchronous interfaces exposed externally (called by the services layer)
    async def add_vectors_sync(self, text_chunks: list[str], embeddings: list[list[float]]):
        await self._async_add_vectors(text_chunks, embeddings)
        logging.info(f"Added {len(text_chunks)} vectors to SurrealDB")

    # vector retrieve synchronous operation interface
    async def retrieve_similar_sync(self, query: str, top_k: int) -> list[dict]:
        from src.services.embedding_service import generate_embedding
        query_vector = generate_embedding([query])[0]
        return await self._async_retrieve_similar(query_vector, top_k)
    