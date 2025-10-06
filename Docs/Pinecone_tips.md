# Pinecone Tips

## Namespace 생성 방법
**작성 시간: 2025-10-07 02:29**

Pinecone의 namespace 생성 방식은 일반적인 DB처럼 `create namespace` 명령을 따로 호출하는 형태가 아닙니다.
Pinecone은 **"lazy creation"**, 즉 데이터가 처음 저장될 때 자동 생성되는 구조를 사용합니다.

### 핵심 개념

| 항목 | 설명 |
|------|------|
| 명시적 생성(create) | ❌ 없음 |
| 암묵적 생성(lazy) | ✅ `upsert()` 시 처음 지정하면 자동 생성 |
| 삭제 방식 | ✅ `delete(delete_all=True, namespace="...")` 로 내용 비우면 자동 삭제됨 (사실상 비활성 상태) |

### 사용 예시

```python
# namespace는 upsert 시 자동으로 생성됨
pc_index.upsert(
    vectors=[
        {"id": "vec1", "values": [0.1, 0.2, ...], "metadata": {...}}
    ],
    namespace="my_namespace"  # 처음 사용 시 자동 생성
)

# namespace 삭제 (내용을 모두 비움)
pc_index.delete(delete_all=True, namespace="my_namespace")
```
