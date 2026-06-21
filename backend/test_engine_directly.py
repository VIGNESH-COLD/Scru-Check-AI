"""
Direct scrutiny engine test script using FastAPI UploadFile objects to get traceback.
"""
import asyncio
import io
from fastapi import UploadFile
from services.scrutiny_engine import ScrutinyEngine
from services.document_parser import DocumentParser

async def test():
    parser = DocumentParser()
    engine = ScrutinyEngine()
    
    # Read files to bytes
    with open("samples/sample_question_paper.docx", "rb") as f:
        qp_bytes = f.read()
    with open("samples/sample_syllabus.docx", "rb") as f:
        syll_bytes = f.read()
        
    # Wrap in FastAPI UploadFile objects
    qp_upload = UploadFile(filename="sample_question_paper.docx", file=io.BytesIO(qp_bytes))
    syll_upload = UploadFile(filename="sample_syllabus.docx", file=io.BytesIO(syll_bytes))
    
    print("Parsing files...")
    qp = await parser.parse(qp_upload)
    syllabus = await parser.parse(syll_upload)
    
    print("Running analysis...")
    try:
        res = await engine.analyze(qp, syllabus)
        print("Analysis completed successfully!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
