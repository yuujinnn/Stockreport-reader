문서조사 > AI Services > CLOVA Studio > Chat Completions V3

Prev: 텍스트 및 이미지 \
Next: 오픈AI 호환성

---

# Function Calling

Classic/VPC 환경에서 이용 가능합니다.

외부 함수나 API를 호출해 동적으로 정보를 가져오거나 작업을 수행할 수 있는 Function calling 기능이 지원되는 v3 Chat Completions에 대해 설명합니다.

## 요청

요청 형식을 설명합니다. 요청 형식은 다음과 같습니다.

| 메서드  | URI                              |
| ---- | -------------------------------- |
| POST | /v3/chat-completions/{modelName} |

### 요청 헤더

요청 헤더에 대한 설명은 다음과 같습니다.

| 헤더                             | 필수 여부       | 설명                                         |
| ------------------------------ | ----------- | ------------------------------------------ |
| `Authorization`                | Required    | 인증을 위한 API 키 <예시> `Bearer nv-************` |
| `X-NCP-CLOVASTUDIO-REQUEST-ID` | Optional    | 요청에 대한 아이디                                 |
| `Content-Type`                 | Required    | 요청 데이터의 형식: `application/json`             |
| `Accept`                       | Conditional | 응답 데이터의 형식: `text/event-stream`            |

> **참고**
> 응답 결과는 기본적으로 JSON 형태로 반환되지만, `Accept`를 `text/event-stream`으로 지정 시 응답 결과를 스트림 형태로 반환합니다.

### 요청 경로 파라미터

요청 경로 파라미터에 대한 설명은 다음과 같습니다.

| 필드          | 타입   | 필수 여부    | 설명                   |
| ----------- | ---- | -------- | -------------------- |
| `modelName` | Enum | Required | 모델 이름 <예시> `HCX-005` |

> **참고**
> HyperCLOVA X Function calling은 HCX-005와 HCX-DASH-002의 Chat Completions v3, 오픈AI 호환 API에서만 사용할 수 있습니다.

### 요청 바디

요청 바디에 대한 설명은 다음과 같습니다.

| 필드                         | 타입               | 필수 여부    | 설명                                                                                                                                                                                   |
| -------------------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `messages`                 | Array            | Required | [대화 메시지](#messages)                                                                                                                                                                  |
| `topP`                     | Double           | Optional | 생성 토큰 후보군을 누적 확률을 기반으로 샘플링<br>0.00 ＜ `topP` ≤ 1.00 (기본값: 0.8)<br>최종 텍스트 응답 반환 시에만 적용 (대화 메세지의 role이 tool인 경우)                                                                        |
| `topK`                     | Integer          | Optional | 생성 토큰 후보군에서 확률이 높은 K개를 후보로 지정하여 샘플링<br>0 ≤ `topK` ≤ 128 (기본값: 0)<br>최종 텍스트 응답 반환 시에만 적용 (대화 메세지의 role이 tool인 경우)                                                                     |
| `maxTokens`                | Integer          | Optional | 최대 생성 토큰 수<br>1024≤ `maxTokens` ≤ 모델 최대값                                                                                                                                             |
| `temperature`              | Double           | Optional | 생성 토큰에 대한 다양성 정도(설정값이 높을수록 다양한 문장 생성)<br>0.00 ≤ `temperature` ≤ 1.00 (기본값: 0.5)<br>최종 텍스트 응답 반환 시에만 적용 (대화 메세지의 role이 tool인 경우)                                                      |
| `repetitionPenalty`        | Double           | Optional | 같은 토큰을 생성하는 것에 대한 패널티 정도(설정값이 높을수록 같은 결괏값을 반복 생성할 확률 감소)<br>0.0 ＜ `repetitionPenalty` ≤ 2.0 (기본값: 1.1)<br>최종 텍스트 응답 반환 시에만 적용 (대화 메세지의 role이 tool인 경우)                               |
| `stop`                     | Array            | Optional | 토큰 생성 중단 문자<br>[](기본값)<br>최종 텍스트 응답 반환 시에만 적용 (대화 메세지의 role이 tool인 경우)                                                                                                               |
| `seed`                     | Integer          | Optional | 모델 반복 실행 시 결괏값의 일관성 수준 조정<br>0: 일관성 수준 랜덤 적용 (기본값)<br>1 ≤ `seed` ≤ 4294967295: 일관되게 생성하고자 하는 결괏값의 `seed` 값 또는 사용자가 지정하고자 하는 `seed` 값<br>최종 텍스트 응답 반환 시에만 적용 (대화 메세지의 role이 tool인 경우) |
| `tools`                    | Array            | Optional | `Function Calling` 사용 가능 도구 목록: [tools](#tools)                                                                                                                                      |
| `toolChoice`               | String \| Object | Optional | `Function Calling` 도구 호출 동작 방식<br>`auto` : 모델이 도구 자동 호출 (String)<br>`none` : 모델이 도구 호출 없이 일반 답변 생성(String)<br>모델이 특정도구 강제 호출(Object)                                                 |
| `toolChoice.type`          | String           | Optional | `Function Calling` 모델이 호출할 도구 유형                                                                                                                                                     |
| `toolChoice.function`      | Object           | Optional | `Function Calling` 모델이 호출할 도구                                                                                                                                                        |
| `toolChoice.function.name` | String           | Optional | `Function Calling` 모델이 호출할 도구 이름                                                                                                                                                     |

#### `messages`

`messages`에 대한 설명은 다음과 같습니다.

| 필드           | 타입     | 필수 여부    | 설명                                                                                                                                                                                                 |
| ------------ | ------ | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `role`       | Enum   | Required | 대화 메시지 역할<br>- `system` \| `user` \| `assistant` \| `tool`<br>- `system`: 역할을 규정하는 지시문<br>- `user`: 사용자의 발화 또는 질문<br>- `assistant`: 사용자의 발화 또는 질문에 대한 답변<br>- `tool`: assistant(모델)가 호출한 함수의 실행 결과 |
| `content`    | String | Required | 대화 메시지 내용<br>- 텍스트 입력(String)                                                                                                                                                                      |
| `toolCalls`  | Array  | –        | assistant의 호출 도구 정보<br>- role이 tool인 경우 assistant의 [toolCalls](#toolCalls) 요청과 같이 입력                                                                                                               |
| `toolCallId` | String | –        | 도구 아이디<br>- role이 tool인 경우, 필수 입력<br>- assistant의 [toolCalls](#toolCalls) 요청과 연결하는 용도                                                                                                              |

#### `tools`

| 필드                     | 타입     | 필수 여부    | 설명                                                                                                                                                                                   |
| ---------------------- | ------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `type`                 | String | Required | 도구 유형<br>- `function`(유효값)                                                                                                                                                           |
| `function`             | Object | Required | 호출 `function` 정보                                                                                                                                                                     |
| `function.name`        | String | Required | `function` 이름                                                                                                                                                                        |
| `function.description` | String | Required | `function` 설명                                                                                                                                                                        |
| `function.parameters`  | Object | Required | `function` 사용 시 전달되는 매개변수<br>- properties, required<br>  - 입력: [동작 방식](#동작-방식) 참조<br>  - 형식: [JSON Schema reference](https://json-schema.org/understanding-json-schema/reference) 참조 |

#### `toolCalls`

| 필드                   | 타입     | 필수 여부 | 설명                         |
| -------------------- | ------ | ----- | -------------------------- |
| `id`                 | String | –     | 도구 식별자                     |
| `type`               | String | –     | 도구 유형<br>- `function`(유효값) |
| `function`           | Object | –     | 호출 `function` 정보           |
| `function.name`      | String | –     | `function` 이름              |
| `function.arguments` | Object | –     | `function` 사용 시 전달되는 매개변수  |

> **참고**
> 일부 필드 입력 시 다음 내용을 확인해 주십시오.
>
> * `role`: `system`인 [대화 메시지](#messages)는 요청당 1개만 포함할 수 있습니다.
> * 이미지 해석과 Function calling을 동시에 요청할 수 없습니다.
> * HCX-005
>
>   * 입력 토큰과 출력 토큰의 합은 128,000 토큰을 초과할 수 없습니다.
>   * 입력 토큰은 최대 128,000 토큰까지 가능합니다.
>   * 모델에 요청할 출력 토큰(maxTokens)은 최대 4,096 토큰까지 가능합니다.
> * HCX-DASH-002
>
>   * 입력 토큰과 출력 토큰의 합은 32,000 토큰을 초과할 수 없습니다.
>   * 입력 토큰은 최대 32,000 토큰까지 가능합니다.
>   * 모델에 요청할 출력 토큰(maxTokens)은 최대 4,096 토큰까지 가능합니다.

## 응답

### 응답 헤더

| 헤더             | 필수 여부 | 설명                             |
| -------------- | ----- | ------------------------------ |
| `Content-Type` | –     | 응답 데이터의 형식: `application/json` |

### 응답 바디

| 필드                              | 타입      | 필수 여부 | 설명                                                                                                                                                                             |
| ------------------------------- | ------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `status`                        | Object  | –     | [응답 상태](/docs/ai-naver-clovastudio-summary#응답)                                                                                                                                 |
| `result`                        | Object  | –     | 응답 결과                                                                                                                                                                          |
| `result.created`                | Integer | –     | 응답 날짜(Unix timestamp miliseconds 형식)                                                                                                                                           |
| `result.usage`                  | Object  | –     | 토큰 사용량                                                                                                                                                                         |
| `result.usage.completionTokens` | Integer | –     | 생성 토큰 수                                                                                                                                                                        |
| `result.usage.promptTokens`     | Integer | –     | 입력(프롬프트) 토큰 수                                                                                                                                                                  |
| `result.usage.totalTokens`      | Integer | –     | 전체 토큰 수<br>- 생성 토큰 수+입력 토큰 수                                                                                                                                                   |
| `result.message`                | Object  | –     | 대화 메시지                                                                                                                                                                         |
| `result.message.role`           | Enum    | –     | 대화 메시지 역할<br>- `system` \| `user` \| `assistant`<br>- `system`: 역할을 규정하는 지시문<br>- `user`: 사용자의 발화 또는 질문<br>- `assistant`: 모델의 답변                                               |
| `result.message.content`        | String  | –     | 대화 메시지 내용                                                                                                                                                                      |
| `result.message.toolCalls`      | Array   | –     | [toolCalls](#toolCalls_response)                                                                                                                                               |
| `result.finishReason`           | String  | –     | 토큰 생성 중단 이유(일반적으로 마지막 이벤트에 전달)<br>- `length` \| `stop` \| `tool_calls`<br>  - `length`: 길이 제한<br>  - `stop`: 답변 생성 중 `stop`에 지정한 문자 출현<br>  - `tool_calls`: 모델이 정상적으로 도구 호출 완료 |
| `result.seed`                   | Integer | –     | 입력 seed 값(0 입력 또는 미입력 시 랜덤 값 반환)                                                                                                                                               |

#### `toolCalls`

| 필드                   | 타입     | 필수 여부 | 설명                         |
| -------------------- | ------ | ----- | -------------------------- |
| `id`                 | String | –     | 도구 식별자                     |
| `type`               | String | –     | 도구 유형<br>- `function`(유효값) |
| `function`           | Object | –     | 호출 `function` 정보           |
| `function.name`      | String | –     | `function` 이름              |
| `function.arguments` | Object | –     | `function` 사용 시 전달되는 매개변수  |

## 동작 방식

요청과 응답을 포함한 Function calling의 동작 방식은 다음과 같습니다.

### Step 1. 입력 및 함수 정의 전달

질의 내용을 입력하고 함수 정의를 전달합니다. 요청 예시는 다음과 같습니다.

* **cURL**

```shell
curl --location --request POST 'https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/{modelName}' \
--header 'Authorization: Bearer <api-key>' \
--header 'X-NCP-CLOVASTUDIO-REQUEST-ID: {Request ID}' \
--header 'Content-Type: application/json' \
--data '{
  "messages" : [ {
    "content" : "오늘 서울 날씨 알려줘",
    "role" : "user"
  } ],
  "tools" : [ {
    "function" : {
      "description" : "날씨를 알려줄 수 있는 도구",
      "name" : "get_weather",
      "parameters" : {
        "properties" : {
          "location" : {
            "description" : "서울, 대전, 부산 등의 도시 이름",
            "type" : "string"
          },
          "unit" : {
            "enum" : [ "celsius", "fahrenheit" ],
            "type" : "string"
          },
          "date" : {
            "description" : "2023-08-01 같은 형태의 날짜 문자열. 날씨를 알고 싶은 날짜",
            "type" : "string"
          }
        },
        "required" : [ "location" ],
        "type" : "object"
      }
    }
  }],
  "toolChoice" : "auto"
}'
```

* **Python**

```python
import requests

API_KEY = "YOUR_API_KEY"
REQUEST_ID = "YOUR_REQUEST_ID"

url = "https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/{modelName}"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "X-NCP-CLOVASTUDIO-REQUEST-ID": REQUEST_ID,
    "Content-Type": "application/json"
}

data = {
    "messages": [
        {
            "content": "내일 서울 날씨 어때?",
            "role": "user"
        }
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "description": "날씨를 알려줄 수 있는 도구",
                "name": "get_weather",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "description": "서울, 대전, 부산 등의 도시 이름",
                            "type": "string"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"]
                        },
                        "date": {
                            "description": "2025-03-21 같은 형태의 날짜 문자열. 날씨를 알고 싶은 날짜",
                            "type": "string"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ],
    "toolChoice": "auto"
}

response = requests.post(url, headers=headers, json=data)
result = response.json()
print(result)
```

### Step 2. 호출할 함수 및 인수 반환

호출할 함수와 인수 정보가 반환됩니다. 응답 예시는 다음과 같습니다.

```json
{
    "status": {
        "code": "20000",
        "message": "OK"
    },
    "result": {
        "message": {
            "role": "assistant",
            "content": "",
            "toolCalls": [
                {
                    "id": "call_s83AKVWrPPI6bCTLl5kFGtyo",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": {
                            "location": "서울",
                            "unit": "celsius",
                            "date": "2025-04-10"
                        }
                    }
                }
            ]
        },
        "finishReason": "tool_calls",
        "created": 1744218663,
        "seed": 1354242582,
        "usage": {
            "promptTokens": 134,
            "completionTokens": 48,
            "totalTokens": 315
        }
    }
}
```

### Step 3. 응답 결과 기반으로 실제 함수 호출

Step 2.의 응답 결과를 기반으로 실제 함수를 호출합니다. 요청 예시는 다음과 같습니다.

* **cURL**

```shell
# <예시> 다음과 같은 API를 호출한다고 가정합니다.
# GET https://weather.example.com?location=서울&unit=celsius&date=2025-04-10

curl --request GET 'https://weather.example.com?location=서울&unit=celsius&date=2025-04-10'
```

* **Python**

```python
"""
<예시> 다음과 같은 함수를 구성했다고 가정합니다.
def get_weather(location, unit="celsius", date=None):
    response = requests.get(f"https://weather.example.com?location={location}&unit={unit}&date={date}")
    data = response.json()
    return data
"""

tool_call = result["result"]["message"]["toolCalls"][0]
function_name = tool_call["function"]["name"]
arguments = tool_call["function"]["arguments"]

if function_name == "get_weather":
    function_result = get_weather(**arguments)
```

### Step 4. 함수 실행 결과 전달

함수 실행 결과를 전달합니다. 요청 예시는 다음과 같습니다.

* **cURL**

```shell
curl --location --request POST 'https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/{modelName}' \
--header 'Authorization: Bearer <api-key>' \
--header 'X-NCP-CLOVASTUDIO-REQUEST-ID: {Request ID}' \
--header 'Content-Type: application/json' \
--data '{
  "messages": [
    {
      "role": "user",
      "content": "내일 서울 날씨 어때?"
    },
    {
      "role": "assistant",
      "content": "",
      "toolCalls": [
        {
          "id": "call_s83AKVWrPPI6bCTLl5kFGtyo",
          "type": "function",
          "function": {
            "name": "get_weather",
            "arguments": {
              "location": "서울",
              "unit": "celsius",
              "date": "2025-04-10"
            }
          }
        }
      ]
    },
    {
      "role": "tool",
      "toolCallId": "call_s83AKVWrPPI6bCTLl5kFGtyo",
      "content": "{ \"location\": \"서울\", \"temperature\": \"17도\", \"condition\": \"맑음\" }"
    }
  ],
  "seed": 0,
  "topP": 0.8,
  "topK": 0,
  "maxTokens": 1024,
  "temperature": 0,
  "repeatPenalty": 1.1,
  "stopBefore": []
}'
```

* **Python**

```python
url = "https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/{modelName}"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "X-NCP-CLOVASTUDIO-REQUEST-ID": REQUEST_ID,
    "Content-Type": "application/json"
}

data = {
    "messages": [
        {
            "role": "user",
            "content": "내일 서울 날씨 어때?"
        },
        {
            "role": "assistant",
            "content": "",
            "toolCalls": [
                {
                    "id": "call_s83AKVWrPPI6bCTLl5kFGtyo",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": {
                            "location": "서울",
                            "unit": "celsius",
                            "date": "2025-04-10"
                        }
                    }
                }
            ]
        },
        {
            "role": "tool",
            "toolCallId": "call_s83AKVWrPPI6bCTLl5kFGtyo",
            "content": str(function_result)
        }
    ],
    "seed": 0,
    "topP": 0.8,
    "topK": 0,
    "maxTokens": 1024,
    "temperature": 0,
    "repeatPenalty": 1.1,
    "stopBefore": []
}

response = requests.post(url, headers=headers, json=data)
result = response.json()
print(result)
```

### Step 5. 최종 텍스트 응답 반환

최종 반환된 응답 결과의 텍스트를 확인합니다.

```json
{
    "status": {
        "code": "20000",
        "message": "OK"
    },
    "result": {
        "message": {
            "role": "assistant",
            "content": "내일 서울의 날씨는 맑을 예정이며, 기온은 17도로 예상됩니다. 따뜻한 봄날씨가 될 것 같으니 외출하기에 좋은 날이 될 것 같아요!"
        },
        "finishReason": "stop",
        "created": 1744218776,
        "seed": 2744409319,
        "usage": {
            "promptTokens": 88,
            "completionTokens": 37,
            "totalTokens": 125
        }
    }
}
```

## 응답 스트림

생성되는 토큰을 하나씩 출력하도록 토큰 스트리밍을 사용할 수 있습니다. 토큰 스트리밍 형식을 설명합니다.

### 응답 헤더

| 헤더       | 필수 여부 | 설명                              |
| -------- | ----- | ------------------------------- |
| `Accept` | –     | 응답 데이터의 형식: `text/event-stream` |

### 응답 바디

#### StreamingChatCompletionsTokenEvent

`StreamingChatCompletionsTokenEvent`에 대한 설명은 다음과 같습니다.

| 필드                       | 타입      | 필수 여부 | 설명                                                                                                                 |
| ------------------------ | ------- | ----- | ------------------------------------------------------------------------------------------------------------------ |
| `created`                | Integer | –     | 응답 시간 타임스탬프                                                                                                        |
| `usage`                  | Object  | –     | 토큰 사용량                                                                                                             |
| `usage.promptTokens`     | Integer | –     | 입력(프롬프트) 토큰 수                                                                                                      |
| `usage.completionTokens` | Integer | –     | 생성 토큰 수                                                                                                            |
| `message`                | Object  | –     | 대화 메시지                                                                                                             |
| `message.role`           | Enum    | –     | 대화 메시지 역할<br>- `user` \| `assistant`<br>- `user`: 사용자의 발화 또는 질문<br>- `assistant`: 모델의 답변                           |
| `message.content`        | String  | –     | 대화 메시지 내용                                                                                                          |
| `message.toolCalls`      | Array   | –     | [toolCalls](#toolCalls_streaming)                                                                                  |
| `finishReason`           | String  | –     | 토큰 생성 중단 이유(일반적으로 마지막 이벤트에 전달)<br>- `length` \| `stop`<br>- `length`: 길이 제한<br>- `stop`: 답변 생성 중 `stop`에 지정한 문자 출현 |

#### `toolCalls`

`StreamingChatCompletionsTokenEvent`에서의 `toolCalls`에 대한 설명은 다음과 같습니다.

| 필드                     | 타입     | 필수 여부 | 설명                                    |
| ---------------------- | ------ | ----- | ------------------------------------- |
| `id`                   | String | –     | 도구 식별자                                |
| `type`                 | String | –     | 도구 유형<br>- `function`(유효값)            |
| `function`             | Object | –     | 호출 `function` 정보                      |
| `function.name`        | String | –     | `function` 이름                         |
| `function.partialJson` | String | –     | `function`에 전달할 JSON 인자를 구성하는 문자열의 일부 |

#### StreamingChatCompletionsResultEvent

`StreamingChatCompletionsResultEvent`에 대한 설명은 다음과 같습니다.

| 필드                       | 타입      | 필수 여부 | 설명                                                                                                                                                       |
| ------------------------ | ------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `created`                | Integer | –     | 응답 시간 타임스탬프                                                                                                                                              |
| `usage`                  | Object  | –     | 토큰 사용량                                                                                                                                                   |
| `usage.promptTokens`     | Integer | –     | 입력(프롬프트) 토큰 수                                                                                                                                            |
| `usage.completionTokens` | Integer | –     | 생성 토큰 수                                                                                                                                                  |
| `usage.totalTokens`      | Integer | –     | 전체 토큰 수<br>- 생성 토큰 수+입력 토큰 수                                                                                                                             |
| `message`                | Object  | –     | 대화 메시지                                                                                                                                                   |
| `message.role`           | Enum    | –     | 대화 메시지 역할<br>- `user` \| `assistant`<br>- `user`: 사용자의 발화 또는 질문<br>- `assistant`: 모델의 답변                                                                 |
| `message.content`        | String  | –     | 대화 메시지 내용                                                                                                                                                |
| `message.toolCalls`      | Array   | –     | [toolCalls](#toolCalls)                                                                                                                                  |
| `finishReason`           | String  | –     | 토큰 생성 중단 이유(일반적으로 마지막 이벤트에 전달)<br>- `length` \| `stop`<br>- `length`: 길이 제한<br>- `stop`: 답변 생성 중 `stop`에 지정한 문자 출현<br>- `tool_calls`: 모델이 정상적으로 도구 호출 완료 |

#### ErrorEvent

`ErrorEvent`에 대한 설명은 다음과 같습니다.

| 필드               | 타입     | 필수 여부 | 설명                                                                         |
| ---------------- | ------ | ----- | -------------------------------------------------------------------------- |
| `status`         | Object | –     | [응답 상태](/docs/ai-naver-clovastudio-summary#응답)                             |
| `status.code`    | Object | –     | (참고) [CLOVA Studio 문제 해결](/release-20250619/docs/clovastudio-troubleshoot) |
| `status.message` | Object | –     | (참고) [CLOVA Studio 문제 해결](/release-20250619/docs/clovastudio-troubleshoot) |

#### SignalEvent

`SignalEvent`에 대한 설명은 다음과 같습니다.

| 필드     | 타입     | 필수 여부 | 설명             |
| ------ | ------ | ----- | -------------- |
| `data` | String | –     | 전달할 시그널 데이터 정보 |

### 응답 예시

#### 성공

호출이 성공한 경우의 응답 예시는 다음과 같습니다.

```python
id:ef40438b-d49a-4fff-9335-a19e5abfcff1
event:token
data:{"message":{"role":"assistant","content":"","toolCalls":[{"id":"call_zumbHGLfLwV3xn0Rn2gSPqfz","type":"function","function":{"name":"get_weather"}}]},"finishReason":null,"created":1749810707,"seed":1775609431,"usage":null}

id:75cae060-e19b-4a82-9106-81b784dcde51
event:token
data:{"message":{"role":"assistant","content":"","toolCalls":[{"type":"function","function":{"partialJson":"{\""}}]},"finishReason":null,"created":1749810707,"seed":1775609431,"usage":null}

id:d29c7e43-d8ed-43f1-8265-6e5fa91b4b65
event:token
data:{"message":{"role":"assistant","content":"","toolCalls":[{"type":"function","function":{"partialJson":"location"}}]},"finishReason":null,"created":1749810707,"seed":1775609431,"usage":null}

id:700f5c00-07b3-4bcc-892d-00913d22ad9f
event:token
data:{"message":{"role":"assistant","content":"","toolCalls":[{"type":"function","function":{"partialJson":"\":"
}}]},"finishReason":null,"created":1749810707,"seed":1775609431,"usage":null}

id:0c3e3439-699d-400a-af23-29a09eab28f3
event:token
data:{"message":{"role":"assistant","content":"","toolCalls":[{"type":"function","function":{"partialJson":" \""}}]},"finishReason":null,"created":1749810707,"seed":1775609431,"usage":null}

id:b7506691-ffb0-4e23-a068-ce50013920de
event:token
data:{"message":{"role":"assistant","content":"","toolCalls":[{"type":"function","function":{"partialJson":"서울"}}]},"finishReason":null,"created":1749810707,"seed":1775609431,"usage":null}

id:7c26e5c8-d75e-4e33-8185-1877c9c2c8d7
event:token
data:{"message":{"role":"assistant","content":"","toolCalls":[{"type":"function","function":{"partialJson":"\","}}]},"finishReason":null,"created":1749810707,"seed":1775609431,"usage":null}

...

id:f32289bd-0b94-4733-9df2-9f1a3eee48a6
event:result
data:{"message":{"role":"assistant","content":"","toolCalls":[{"id":"call_zumbHGLfLwV3xn0Rn2gSPqfz","type":"function","function":{"name":"get_weather","arguments":{"location":"서울","unit":"celsius","date":"2025-06-13"}}}]},"finishReason":"tool_calls","created":1749810707,"seed":1775609431,"usage":{"promptTokens":9,"completionTokens":47,"totalTokens":56}}
```

#### 실패

호출이 실패한 경우의 응답 예시는 다음과 같습니다.

* [클라이언트 공통 오류 문제(4xx)](C:\Users\junseok\Documents\.VAULT\.github\Stockreport-reader\api_docs\클라이언트_공통_오류_문제(4xx).md)

---

Prev: 텍스트 및 이미지 \
Next: 오픈AI 호환성