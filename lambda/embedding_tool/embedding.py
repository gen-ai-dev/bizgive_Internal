import boto3



from database.data_retrieval import initialize_db_retriever

def get_reference(query: str, type=None):
    if type is None:
        retriever= initialize_db_retriever(collectionID= collection_id, top_k=config_data['top_k'], embeddings_model=config_data['embeddings_model'], industry_collectionID= None)
        context = retriever.invoke(query)
    elif type =="project":
        retriever= initialize_db_retriever(project_collectionID= projectCollection, top_k=config_data['top_k'], embeddings_model=config_data['embeddings_model'], industry_collectionID= None)
        context = retriever.invoke(query)
    elif type =="industry":
        retriever= initialize_db_retriever(project_collectionID= projectCollection, industry_collectionID= industryCollection, top_k=config_data['top_k'], embeddings_model=config_data['embeddings_model'])
        context = retriever.invoke(query)
    return context

def lambda_handler(event, context):   
    structured_json = event.get("processed_text", {})

    claims = structured_json["type"].get("claim", [])
    opinions = structured_json["type"].get("opinion", [])

    if claims:
        for claim in claims:
            claim["context"] = get_reference(claim["quote"], claim["claim-type"])
    
    if opinions:
        for opinion in opinions:
            opinion["context"] = get_reference(opinion["quote"], None)
    
    return {"processed_text": structured_json}