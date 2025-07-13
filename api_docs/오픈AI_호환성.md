문서조사 > AI Services > CLOVA Studio

Prev: Function Calling \
Next: 클라이언트 공통 오류 문제(4xx)

---

# 오픈AI 호환성

Classic/VPC 환경에서 이용 가능합니다.

CLOVA Studio 서비스는 Chat Completions, 임베딩을 비롯한 주요 API에 대해 오픈AI API와의 호환성을 제공합니다.

## 호환 API

CLOVA Studio 서비스에서 오픈AI API와 호환되는 API 목록은 다음과 같습니다.

| API                                   | 메서드  | URI                 |
| ------------------------------------- | ---- | ------------------- |
| Chat Completions, Chat Completions v3 | POST | `/chat/completions` |
| 임베딩, 임베딩 v2                           | POST | `/embeddings`       |
| 모델 조회                                 | GET  | `/models`           |

## 사용 방법

오픈AI 호환 API의 요청 형식과 응답 형식을 설명합니다.

### 요청

CLOVA Studio API의 요청 항목을 일부 조정하여 OpenAI 공식 라이브러리(SDK) 및 REST API로 이용할 수 있습니다.

#### API 키

CLOVA Studio 서비스에서 발급받은 테스트 또는 서비스 API 키를 이용합니다.

> **주의**
>
> 오픈AI 호환 API는 CLOVA Studio의 **\[API 키]** 에서 발급받은 테스트 API 키나 서비스 API 키를 통해서만 사용할 수 있습니다.
> 테스트 API 키를 사용하는 경우에는 테스트 앱을, 서비스 API 키를 사용하는 경우에는 서비스 앱을 이용하는 것으로 간주합니다.

#### API URL

요청 API URL은 다음과 같습니다.

```http
https://clovastudio.stream.ntruss.com/v1/openai/
```

> **참고**
>
> 오픈AI 호환 API URL은 `testapp`, `serviceapp`을 포함하지 않습니다. 테스트 앱과 서비스 앱은 API 키를 통해 구별합니다. 다음 예시를 참고해 주십시오.
> <예시>
>
> * Chat Completions v3 API URL
>
>   * 테스트 앱: `https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/{modelName}`
>   * 서비스 앱: `https://clovastudio.stream.ntruss.com/serviceapp/v3/chat-completions/{modelName}`
> * 오픈AI 호환 Chat Completions API URL
>
>   * `https://clovastudio.stream.ntruss.com/v1/openai/chat/completions`

#### 모델

요청 바디의 모델 이름은 CLOVA Studio 서비스에서 제공하는 모델 이름으로 입력해 주십시오.

#### 명명 규칙

요청 필드의 명명 규칙은 스네이크 표기법(snake\_case)을 준수합니다.

### 응답

오픈AI API와 동일한 구조와 형식의 응답 결과를 지원합니다.

## SDK 예제

OpenAI 공식 라이브러리를 활용하여 CLOVA Studio 서비스를 이용하는 예제를 소개합니다.

### Python

Python으로 작성한 예제는 다음과 같습니다.

```python
from openai import OpenAI

client = OpenAI(
    api_key="CLOVA_STUDIO_API_KEY",  # CLOVA Studio API 키
    base_url="https://clovastudio.stream.ntruss.com/v1/openai"  # CLOVA Studio 오픈AI 호환 API URL 
)

# Chat Completions
response = client.chat.completions.create(
    model="HCX-005",  # CLOVA Studio 지원 모델명
    messages=[
        {"role": "system", "content": "당신은 유능한 AI 어시스턴트입니다."},
        {"role": "user", "content": "인공지능에 대해 설명해 주세요."}
    ]
)

print(response.choices[0].message.content)

# Embeddings
embedding = client.embeddings.create(
    model="bge-m3",  # CLOVA Studio 지원 모델명 (임베딩)
    input="클로바 스튜디오를 이용해 주셔서 감사합니다.",
    encoding_format="float"  # 오픈AI Python SDK로 임베딩을 이용하는 경우, 필수 설정(base64 미지원)
)
```

> **유의사항**
>
> OpenAI 공식 Python 라이브러리로 임베딩을 이용하고자 하는 경우, `encoding_format="float"`은 필수 설정입니다.

### TypeScript/JavaScript (Node.js)

TypeScript/JavaScript (Node.js)로 작성한 예제는 다음과 같습니다.

```javascript
import OpenAI from "openai";

const openai = new OpenAI({
    baseURL: "https://clovastudio.stream.ntruss.com/v1/openai", // CLOVA Studio 오픈AI 호환 API URL
    apiKey: "YOUR_API_KEY", // CLOVA Studio API 키
}); // CLOVA Studio API 키

// Chat Completions
const completion = await openai.chat.completions.create({
    model: "HCX-005",   // CLOVA Studio 지원 모델명
    messages: [
        {"role": "system", "content": "당신은 유능한 AI 어시스턴트입니다."},
        {"role": "user", "content": "인공지능에 대해 설명해 주세요."}
    ]
});

console.log(completion.choices[0].message);

// Embedding
const embedding = await openai.chat.completions.create({
    model: "bge-m3",   // CLOVA Studio 지원 모델명 (임베딩)
    input: "클로바 스튜디오를 이용해주셔서 감사합니다."
});

console.log(embedding.data[0].embedding);
```

> **참고**
>
> 이외 다양한 언어의 OpenAI 공식 SDK 및 호환 API로 구현된 오픈소스 프레임워크를 통해 CLOVA Studio를 이용할 수 있습니다.

## 호환 정보

오픈AI API와 호환되는 API별 상세 호환 정보를 안내합니다. 지원 필드와 CLOVA Studio 전용 필드의 입력 형식 및 범위는 해당 API 가이드를 확인해 주십시오.

### Chat Completions/Chat Completions v3

Chat Completions API, Chat Completions v3 API의 오픈AI 호환 정보는 다음과 같습니다.

| 지원 필드                                                                                                                                                                          | 미지원 필드                                                                                                                                                                                                                                                                                   | CLOVA Studio 전용 필드                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `model`<br>`messages`<br>`stream`<br>`tools`<br>`tool_choice`<br>`temperature`<br>`max_tokens` (기본값: 512)<br>`max_completion_tokens` (기본값: 512)<br>`top_p`<br>`stop`<br>`seed` | `frequency_penalty`<br>`presence_penalty`<br>`response_format`<br>`store`<br>`reasoning_effort`<br>`metadata`<br>`logit_bias`<br>`logprobs`<br>`top_logprobs`<br>`n`<br>`modalities`<br>`prediction`<br>`audio`<br>`service_tier`<br>`stream_options`<br>`parallel_tool_calls`<br>`user` | `top_k`<br>`repeat_penalty`<br>`repetition_penalty` |

### 임베딩/임베딩 v2

임베딩 API, 임베딩 v2 API의 오픈AI 호환 정보는 다음과 같습니다.

| 지원 필드              | 미지원 필드                                      | CLOVA Studio 전용 필드 |
| ------------------ | ------------------------------------------- | ------------------ |
| `input`<br>`model` | `dimensions`<br>`encoding_format`<br>`user` | -                  |

---

Prev: Function Calling \
Next: 클라이언트 공통 오류 문제(4xx)
