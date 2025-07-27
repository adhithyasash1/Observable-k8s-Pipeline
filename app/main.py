import logging
import time
import json
from fastapi import FastAPI, Request, HTTPException, Response
from pydantic import BaseModel
import joblib
import pandas as pd

# OpenTelemetry setup for Cloud Trace
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

# 1. Set up the tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
span_processor = BatchSpanProcessor(CloudTraceSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)

# 2. Set up a structured JSON logger for Cloud Logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
            "trace_id": format(trace.get_current_span().get_span_context().trace_id, "032x")
        }
        return json.dumps(log_record)

logger = logging.getLogger("iris-app")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)

# --- FastAPI Application ---

app = FastAPI(title="🌸 Observable Iris Classifier API")

# 3. Load ML model
model = joblib.load("model.joblib")

# 4. Define input/output schemas
class IrisInput(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

class PredictionOutput(BaseModel):
    predicted_class: str

# --- Middleware & Exception Handling ---

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    # Start a new span for the incoming request
    with tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = (time.time() - start_time) * 1000
        response.headers["X-Process-Time-ms"] = str(round(duration, 2))
        
        # Add attributes to the span
        span.set_attribute("http.status_code", response.status_code)
        span.set_attribute("http.response.duration_ms", duration)
        
        return response

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception for {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )

# --- API Endpoints ---

@app.get("/", tags=["General"])
def read_root():
    return {"message": "Welcome to the Observable Iris Classifier API!"}

@app.post("/predict", response_model=PredictionOutput, tags=["Prediction"])
def predict_species(data: IrisInput):
    with tracer.start_as_current_span("model_inference") as span:
        start_time = time.time()
        try:
            input_df = pd.DataFrame([data.dict()])
            prediction_result = model.predict(input_df)[0]
            
            latency_ms = (time.time() - start_time) * 1000
            span.set_attribute("ml.inference.latency_ms", latency_ms)
            
            logger.info(f"Prediction successful. Latency: {latency_ms:.2f} ms")
            
            return {"predicted_class": prediction_result}
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Prediction failed"))
            raise HTTPException(status_code=500, detail="Model inference failed")

# --- Kubernetes Probes ---

@app.get("/live_check", tags=["Probes"])
def liveness_probe():
    return {"status": "alive"}

@app.get("/ready_check", tags=["Probes"])
def readiness_probe():
    # In a real app, this would check DB connections, etc.
    return {"status": "ready"}
