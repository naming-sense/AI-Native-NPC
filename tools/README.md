# Tooling v0.4.6

```bash
python tools/doc_harness.py status
python tools/doc_harness.py inventory
python tools/doc_harness.py validate --strict
python tools/doc_harness.py release --output ../ai_native_npc_document_harness_v0.4.6.zip
```

핵심 도구:

- `validate_schema.py`: YAML·Registry 의미 검증
- `generate_contracts.py`: C++·Python·문서 계약 생성
- `generate_golden.py`: Golden fixture 생성
- `run_contract_tests.py`: 환경 독립 규범 테스트 리포트 생성
- `run_release_mutation_tests.py`: README 기반 end-to-end 의미 변조 방어 검증
- `doc_harness.py`: Catalog, Source Map, Freeze Manifest, Lock, ZIP 릴리스 오케스트레이션
