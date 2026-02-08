import asyncio
import logging
import pandas as pd
from surrealdb import AsyncWsSurrealConnection

# SurrealDB Synchronous Encapsulation (Core: Asynchronous → Synchronous)
# Core idea: Convert asynchronous operations into synchronous operations, use asyncio.run() to execute asynchronous code
class SurrealDBSyncClient:
    _SURREALDB_CASE_ID = "tree_case_all"

    # Multi-collection names for enhanced retrieval
    COLLECTION_HISTORICAL_CASES = "historical_cases_vectors"
    COLLECTION_KNOWLEDGE_DOCS = "knowledge_docs_vectors"
    COLLECTION_TREE_INVENTORY = "tree_inventory_vectors"

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
                # Existing RAG vector table
                await db.query("""
                    DEFINE TABLE vector SCHEMALESS;
                    DEFINE FIELD case_id ON vector TYPE string;
                    DEFINE FIELD file_id ON vector TYPE string;
                    DEFINE FIELD chunk_index ON vector TYPE int;
                    DEFINE FIELD content ON vector TYPE string;
                    DEFINE FIELD vector ON vector TYPE array<float>;
                    DEFINE FIELD create_time ON vector TYPE string;
                """)
                # Multi-collection schema for enhanced retrieval
                await db.query("""
                    DEFINE TABLE historical_cases_vectors SCHEMALESS;
                    DEFINE FIELD case_id ON historical_cases_vectors TYPE string;
                    DEFINE FIELD case_number ON historical_cases_vectors TYPE string;
                    DEFINE FIELD location ON historical_cases_vectors TYPE string;
                    DEFINE FIELD slope_no ON historical_cases_vectors TYPE string;
                    DEFINE FIELD content ON historical_cases_vectors TYPE string;
                    DEFINE FIELD vector ON historical_cases_vectors TYPE array<float>;
                    DEFINE FIELD source ON historical_cases_vectors TYPE string;
                    DEFINE FIELD create_time ON historical_cases_vectors TYPE string;

                    DEFINE TABLE tree_inventory_vectors SCHEMALESS;
                    DEFINE FIELD tree_id ON tree_inventory_vectors TYPE string;
                    DEFINE FIELD slope_no ON tree_inventory_vectors TYPE string;
                    DEFINE FIELD species ON tree_inventory_vectors TYPE string;
                    DEFINE FIELD location ON tree_inventory_vectors TYPE string;
                    DEFINE FIELD content ON tree_inventory_vectors TYPE string;
                    DEFINE FIELD vector ON tree_inventory_vectors TYPE array<float>;
                    DEFINE FIELD create_time ON tree_inventory_vectors TYPE string;

                    DEFINE TABLE knowledge_docs_vectors SCHEMALESS;
                    DEFINE FIELD doc_type ON knowledge_docs_vectors TYPE string;
                    DEFINE FIELD filename ON knowledge_docs_vectors TYPE string;
                    DEFINE FIELD content ON knowledge_docs_vectors TYPE string;
                    DEFINE FIELD vector ON knowledge_docs_vectors TYPE array<float>;
                    DEFINE FIELD create_time ON knowledge_docs_vectors TYPE string;
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
            await db.query("""
                INSERT INTO vector {
                    case_id: $case_id,
                    content: $content,
                    vector: $vector,
                    create_time: $create_time
                }
            """, {
                "case_id": self._SURREALDB_CASE_ID, 
                "content": chunk, 
                "vector": vec, 
                "create_time": pd.Timestamp.now().isoformat()
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
    
    # ============== New methods for file-based vector management ==============
    
    async def _async_add_vectors_with_file_id(self, file_id: str, text_chunks: list[str], embeddings: list[list[float]]) -> list[str]:
        """
        Add vectors with file_id tracking
        
        Args:
            file_id: File ID (e.g., "rag_file_123")
            text_chunks: Text chunks
            embeddings: Vector embeddings
            
        Returns:
            list[str]: List of inserted record IDs
        """
        db = await self._async_connect()
        vector_ids = []
        
        # Batch insert with file_id and chunk_index
        for i, (chunk, vec) in enumerate(zip(text_chunks, embeddings)):
            result = await db.query("""
                INSERT INTO vector {
                    file_id: $file_id,
                    chunk_index: $chunk_index,
                    content: $content,
                    vector: $vector,
                    create_time: $create_time
                }
            """, {
                "file_id": file_id, 
                "chunk_index": i,
                "content": chunk, 
                "vector": vec, 
                "create_time": pd.Timestamp.now().isoformat()
            })
            
            # Extract record ID from result
            if result and len(result) > 0 and isinstance(result[0], list) and len(result[0]) > 0:
                record_id = result[0][0].get('id', '')
                vector_ids.append(record_id)
        
        await db.close()
        logging.info(f"Added {len(text_chunks)} vectors for file {file_id}")
        return vector_ids
    
    async def _async_delete_vectors_by_file_id(self, file_id: str) -> int:
        """
        Delete all vectors for a specific file
        
        Args:
            file_id: File ID
            
        Returns:
            int: Number of deleted records
        """
        db = await self._async_connect()
        
        try:
            result = await db.query("""
                DELETE vector WHERE file_id = $file_id
            """, {"file_id": file_id})
            
            # Count deleted records
            count = 0
            if result:
                count = len(result[0]) if isinstance(result[0], list) else 0
            
            await db.close()
            logging.info(f"Deleted {count} vectors for file {file_id}")
            return count
            
        except Exception as e:
            await db.close()
            logging.error(f"Error deleting vectors for file {file_id}: {e}")
            raise e
    
    async def _async_get_chunk_count_by_file_id(self, file_id: str) -> int:
        """
        Get chunk count for a specific file
        
        Args:
            file_id: File ID
            
        Returns:
            int: Number of chunks
        """
        db = await self._async_connect()
        
        try:
            result = await db.query("""
                SELECT count() as count FROM vector WHERE file_id = $file_id GROUP ALL
            """, {"file_id": file_id})
            
            count = 0
            if result and len(result) > 0 and isinstance(result[0], list) and len(result[0]) > 0:
                count = result[0][0].get('count', 0)
            
            await db.close()
            return count
            
        except Exception as e:
            await db.close()
            logging.error(f"Error getting chunk count for file {file_id}: {e}")
            return 0
    
    # Public synchronous methods for file-based operations
    async def add_vectors_with_file_id_sync(self, file_id: str, text_chunks: list[str], embeddings: list[list[float]]) -> list[str]:
        """Synchronous wrapper for adding vectors with file_id"""
        return await self._async_add_vectors_with_file_id(file_id, text_chunks, embeddings)

    async def delete_vectors_by_file_id_sync(self, file_id: str) -> int:
        """Synchronous wrapper for deleting vectors by file_id"""
        return await self._async_delete_vectors_by_file_id(file_id)

    async def get_chunk_count_by_file_id_sync(self, file_id: str) -> int:
        """Synchronous wrapper for getting chunk count by file_id"""
        return await self._async_get_chunk_count_by_file_id(file_id)

    # ============== Multi-collection retrieval and insert ==============

    async def retrieve_from_collection(
        self,
        collection: str,
        query: str,
        top_k: int,
        filters: dict = None,
    ) -> list[dict]:
        """
        Generic vector retrieval from a named collection (historical_cases_vectors,
        tree_inventory_vectors, knowledge_docs_vectors). Uses cosine similarity.

        Args:
            collection: Table name (e.g. COLLECTION_HISTORICAL_CASES).
            query: Natural language or text query to embed.
            top_k: Maximum number of results.
            filters: Optional dict of field names to values for WHERE clause (e.g. {"location": "X"}).

        Returns:
            List of dicts with at least "content" and "similarity", plus any table fields.
        """
        from src.services.embedding_service import generate_embedding

        query_vector = generate_embedding([query])[0]
        filter_clause = ""
        params = {"query_vec": query_vector, "top_k": top_k}

        if filters:
            non_empty = {k: v for k, v in filters.items() if v is not None and str(v).strip() != ""}
            if non_empty:
                conditions = [f"{k} = ${k}" for k in non_empty.keys()]
                filter_clause = " WHERE " + " AND ".join(conditions)
                params.update(non_empty)

        db = await self._async_connect()
        try:
            sql = f"""
                SELECT *, vector::similarity::cosine(vector, $query_vec) AS similarity
                FROM {collection}
                {filter_clause}
                ORDER BY similarity DESC
                LIMIT $top_k
            """
            results = await db.query(sql, params)
        finally:
            await db.close()

        ret = []
        rows = results[0] if results and isinstance(results[0], list) else (results if isinstance(results, list) else [])
        for item in rows:
            if not isinstance(item, dict):
                continue
            sim = item.get("similarity")
            ret.append({
                "content": item.get("content", ""),
                "similarity": round(float(sim), 3) if sim is not None else 0.0,
                **{k: v for k, v in item.items() if k not in ("vector", "similarity")},
            })
        return ret

    async def add_to_collection(self, collection: str, data: dict):
        """
        Insert a single record into a vector collection. `data` must include
        "content" and "vector"; other fields depend on the collection schema.
        create_time defaults to now if omitted.

        Returns:
            Inserted record id if available, else None.
        """
        data = dict(data)
        if data.get("create_time") is None:
            data["create_time"] = pd.Timestamp.now().isoformat()

        db = await self._async_connect()
        try:
            if collection == self.COLLECTION_HISTORICAL_CASES:
                result = await db.query("""
                    INSERT INTO historical_cases_vectors (
                        case_id, case_number, location, slope_no, content, vector, source, create_time
                    ) VALUES (
                        $case_id, $case_number, $location, $slope_no, $content, $vector, $source, $create_time
                    )
                """, data)
            elif collection == self.COLLECTION_TREE_INVENTORY:
                result = await db.query("""
                    INSERT INTO tree_inventory_vectors (
                        tree_id, slope_no, species, location, content, vector, create_time
                    ) VALUES (
                        $tree_id, $slope_no, $species, $location, $content, $vector, $create_time
                    )
                """, data)
            elif collection == self.COLLECTION_KNOWLEDGE_DOCS:
                result = await db.query("""
                    INSERT INTO knowledge_docs_vectors (
                        doc_type, filename, content, vector, create_time
                    ) VALUES (
                        $doc_type, $filename, $content, $vector, $create_time
                    )
                """, data)
            else:
                await db.close()
                raise ValueError(f"Unknown collection: {collection}")

            rid = None
            if result and len(result) > 0 and isinstance(result[0], list) and len(result[0]) > 0:
                rid = result[0][0].get("id")
                if hasattr(rid, "__str__"):
                    rid = str(rid)
            return rid
        finally:
            await db.close()

    async def add_batch_to_collection(self, collection: str, records: list[dict]) -> list[str]:
        """
        Insert multiple records into a vector collection. Each record is a dict
        with keys matching the collection schema (including "content" and "vector").
        """
        ids = []
        for data in records:
            data = dict(data)
            if "create_time" not in data:
                data["create_time"] = pd.Timestamp.now().isoformat()
            rid = await self.add_to_collection(collection, data)
            if rid:
                ids.append(rid)
        return ids
    