from fastapi import FastAPI
app = FastAPI(title="Git History Intelligence")

@app.get("/")
def root():
    return {"name": "Git History Intelligence API", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status" : "ok"}