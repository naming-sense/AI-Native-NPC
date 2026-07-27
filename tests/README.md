# 테스트 v0.4.6

현재 패키지는 다음을 자동 검증한다.

- Schema·Registry semantic validation
- Python↔C++ canonical serialization 및 Golden
- Normalizer·Parameter·Hash 계약
- 동적 semantic mutation probes
- 모든 locked non-archive Markdown의 수기 Hash/Critical 분모 검사
- README 기반 end-to-end release mutation
- Catalog와 실제 Archive 집합의 exact-match
- Source File Map 최신성
- Lock 역방향 파일 집합 검사

Unreal Float/ONNX, Recall, Runtime FSM·Atomic Commit·Safety는 별도 Runtime Gate다.
