from fastapi import HTTPException
from database.postgres_connection import connect_to_postgres_db
def check_collection_exists(project_id):
    db_conn = connect_to_postgres_db()
    cur = db_conn.cursor()
    query = """
    SELECT EXISTS (
        SELECT 1
        FROM public.langchain_pg_collection
        WHERE name = %s
    );
    """
    
    try:
        cur.execute(query, (project_id,))
        exists = cur.fetchone()[0]
        if not exists:
            raise HTTPException(status_code=404, detail=f"Collection not found for project ID '{project_id}'.")
        return exists
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking collection existence: {str(e)}")
    finally:
        cur.close()
        db_conn.close()