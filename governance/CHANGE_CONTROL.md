# 변경 관리 규칙 v0.4.6

## 단일 릴리스 명령

승인된 변경은 다음 명령으로만 패키징한다.

```bash
python tools/doc_harness.py release \
  --output ../ai_native_npc_document_harness_v0.4.6.zip
```

이 명령은 생성 코드, 자동 문서 블록, end-to-end mutation, Golden, Catalog, Source File Map, Freeze Manifest, Lock과 ZIP을 일괄 재생성한다.

## 변경 순서

1. Current YAML·Registry 또는 Current 문서를 수정한다.
2. `release`를 실행한다.
3. `validate --strict`와 생성된 리포트를 확인한다.
4. ZIP SHA-256과 승인 기록을 남긴다.

## 금지 사항

- Archive를 현재 구현 입력으로 사용하지 않는다.
- Catalog Archive 항목을 수동으로 누락하거나 존재하지 않는 경로로 등록하지 않는다.
- Lock 대상 non-archive Markdown에 Hash serializer 값을 수기로 복제하지 않는다.
- Critical Suite 분모를 Taxonomy와 별도로 수기 관리하지 않는다.
- Runtime Gate 통과 전 대량 학습 데이터 생성을 승인하지 않는다.
