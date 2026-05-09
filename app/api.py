from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.model import summarize
from app.scraper import fetch_article_text
from app.db import init_db, save_log
import mlflow
import time

app = FastAPI(title="Web Page Summarizer API")
init_db()

mlflow.set_tracking_uri("file:///app/mlruns")
mlflow.set_experiment("summarizer-experiments")

class SummarizeRequest(BaseModel):
    url: str

@app.post("/summarize")
def predict(req: SummarizeRequest):

    start_time = time.time()
    
    with mlflow.start_run():
        try:
            text = fetch_article_text(req.url)
            if not text:
                raise HTTPException(status_code=400, detail="Не удалось извлечь текст по URL")
            
            summary = summarize(text)
            
            mlflow.log_param("model", "IlyaGusev/mt5_ru_summarization")
            mlflow.log_param("url", req.url)
            mlflow.log_param("max_length", 150)
            mlflow.log_metric("input_length", len(text))
            mlflow.log_metric("output_length", len(summary))
            mlflow.log_metric("inference_time", time.time() - start_time)
            
            save_log(req.url, len(text), summary)
            
            return {"url": req.url, "summary": summary}
        
        except HTTPException:
            raise
        except Exception as e:
            mlflow.log_param("error", str(e))
            raise HTTPException(status_code=500, detail=str(e))