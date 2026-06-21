"""
Direct test of the analysis pipeline to debug data flow.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.document_parser import DocumentParser
from services.scrutiny_engine import ScrutinyEngine

class MockUploadFile:
    def __init__(self, path):
        self.filename = os.path.basename(path)
        with open(path, 'rb') as f:
            self._content = f.read()
    async def read(self):
        return self._content

async def test():
    print("=" * 60)
    print("TESTING ANALYSIS PIPELINE")
    print("=" * 60)
    
    # Parse documents
    parser = DocumentParser()
    
    print("\n1. Parsing Question Paper...")
    qp = MockUploadFile('samples/sample_question_paper.docx')
    qp_content = await parser.parse(qp)
    print(f"   Questions found: {len(qp_content.get('questions', []))}")
    for q in qp_content.get('questions', [])[:3]:
        print(f"   - Q{q['number']}: {q['text'][:50]}...")
    
    print("\n2. Parsing Syllabus...")
    syl = MockUploadFile('samples/sample_syllabus.docx')
    syl_content = await parser.parse(syl)
    print(f"   Sections found: {len(syl_content.get('sections', []))}")
    print(f"   Raw text length: {len(syl_content.get('raw_text', ''))}")
    
    print("\n3. Running Scrutiny Engine...")
    engine = ScrutinyEngine()
    findings = await engine.analyze(
        question_paper=qp_content,
        syllabus=syl_content,
        previous_paper=None,
        pattern=None,
        department=None,
        regulation=None
    )
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Passed count: {findings['passed_count']}")
    print(f"Blooms Distribution: {findings['blooms']}")
    print(f"Syllabus Coverage: {findings['syllabus_coverage']}")
    print(f"CO Mapping count: {len(findings['co_mapping'])}")
    
    # Print first few CO mappings for debugging
    print("\nFirst 3 CO Mappings:")
    for co in findings['co_mapping'][:3]:
        print(f"  {co['question_no']}: {co['bloom_level']} (conf: {co.get('confidence', 'N/A')})")

if __name__ == "__main__":
    asyncio.run(test())
