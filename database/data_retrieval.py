import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, '..')
sys.path.append(root_dir)

from database.database_utils import check_collection_exists
from database.pg_connection import connect_to_postgres_vector_db

def initialize_db_retriever(collectionID, top_k, embeddings_model):
    try:
        check_collection_exists(collectionID)
        
        # Initialize the PGVector and retriever
        db = PGVector(
            collection_name=collectionID,
            connection=connect_to_postgres_vector_db(),
            embeddings=bedrock_embedding(model_id=embeddings_model),
            use_jsonb=True
        )
        retriever = db.as_retriever(search_kwargs={'k': top_k})
        return retriever
    
    except HTTPException as e:
        # Reraise HTTPException to be handled in the API layer
        raise e
    except Exception as e:
        # Handle unexpected exceptions
        raise HTTPException(status_code=500, detail=f"Error initializing DB retriever: {str(e)}")