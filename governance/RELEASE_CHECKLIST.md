# v0.4.6 릴리스 체크리스트

- [ ] Schema·Skill·Goal·Taxonomy 의미 검증
- [ ] Python/C++ 생성 코드 재현성
- [ ] Python/C++ Golden parity
- [ ] 모든 locked non-archive 수기 Markdown 의미 검사
- [ ] README end-to-end mutation 3종 거부
- [ ] Source File Map 최신성
- [ ] Catalog Archive exact-match
- [ ] Missing/Ghost Archive 회귀 테스트
- [ ] Reverse-lock
- [ ] Freeze Manifest와 Validation Report 재생성
- [ ] deterministic double-pack
- [ ] ZIP CRC·경로·symlink·암호화 검사

```bash
python tools/doc_harness.py release \
  --output ../ai_native_npc_document_harness_v0.4.6.zip
```
