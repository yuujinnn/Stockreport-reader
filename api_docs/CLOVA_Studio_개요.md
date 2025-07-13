문서조사 > AI Services > CLOVA Studio

Next: 텍스트 및 이미지

---

# CLOVA Studio 개요

Classic/VPC 환경에서 이용 가능합니다.

CLOVA Studio는 초대규모(Hyperscale) AI 기술인 HyperCLOVA 언어 모델을 활용하여 사용자가 입력한 내용에 따라 AI 기술을 통해 생성된 문구를 출력하는 네이버 클라우드 플랫폼의 서비스입니다. CLOVA Studio 서비스에서는 문장 생성, 튜닝, 익스플로러, 스킬 트레이너 기능에 대한 API를 RESTful 형태로 제공합니다.

## API 키

CLOVA Studio API는 권한을 가진 사용자만 호출할 수 있도록 사용자 식별 도구인 API 키를 계정별로 발급하고 있습니다. API 키는 API 호출 시 인증 정보로 전달하는 요청 헤더의 파라미터로 사용합니다. 따라서 CLOVA Studio API를 사용하려면 우선 API 키를 발급받아야 합니다.

### API 키 발급

API 키는 네이버 클라우드 플랫폼 콘솔의 CLOVA Studio에서 발급할 수 있습니다. 발급 방법은 다음과 같습니다.

1. 네이버 클라우드 플랫폼 콘솔에서 **Services** > **AI Services** > **CLOVA Studio** 메뉴를 차례대로 클릭해 주십시오.
2. 화면 우측 상단의 사용자명을 클릭한 다음 **API 키** 메뉴를 클릭해 주십시오.
3. **API 키** 화면이 나타나면 발급할 API 키 탭 메뉴를 클릭한 다음 발급 버튼을 클릭해 주십시오.

   * **테스트 API 키**: **테스트** 탭 선택 > **테스트 API 키 발급**

     * 서비스 앱을 제외한 CLOVA Studio API 호출 시 이용 가능
   * **서비스 API 키**: **서비스** 탭 선택 > **서비스 API 키 발급**

     * 서비스 앱을 포함한 모든 CLOVA Studio API 호출 시 이용 가능
4. **API 키 발급** 팝업 창이 나타나면 **발급** 버튼을 클릭해 주십시오.

   * **API 키 복사** 팝업 창에서 발급된 API 키를 복사합니다.

> **주의**
> 발급된 API 키는 **API 키 복사** 팝업 창을 닫은 후에는 확인이 불가능합니다. 따라서 반드시 발급 시점에 별도의 안전한 공간에 보관하여 주십시오.

> **참고**
> 테스트 API 키, 서비스 API 키는 네이버 클라우드 플랫폼의 메인 계정 기준으로 각각 최대 10개까지 생성할 수 있습니다.

### API 보안 설정

API 키가 제3자에게 유출되는 경우, CLOVA Studio 리소스를 임의로 이용하는 등 보안 문제가 발생할 수 있으므로 적절한 사전 대비와 대응이 필요합니다.

#### API 키 삭제 및 재발급

API 키를 사용하지 않거나 제3자의 도용이 의심된다면 발급한 API 키를 삭제한 후 다시 발급해야 합니다. 삭제 및 재발급 방법은 다음과 같습니다.

1. 네이버 클라우드 플랫폼 콘솔에서 **Services** > **AI Services** > **CLOVA Studio** 메뉴를 차례대로 클릭해 주십시오.
2. 화면 우측 상단의 사용자명을 클릭한 다음 **API 키** 메뉴를 클릭해 주십시오.
3. **API 키** 화면이 나타나면 삭제할 API 키가 있는 탭 메뉴를 클릭해 주십시오.
4. 삭제할 API 키의 설정 버튼을 클릭한 다음 **삭제** 메뉴를 클릭해 주십시오.
5. **API 키 삭제** 팝업 창이 나타나면 **\[삭제]** 버튼을 클릭해 주십시오.
6. [API 키 발급](#api-키-발급)을 참조하여 새로운 API 키를 발급해 주십시오.

> **주의**
> 삭제한 API 키는 유효하지 않은 키로 인식되기 때문에 더 이상 API 호출에 사용할 수 없습니다.

## 공통 설정

CLOVA Studio API에서 공통으로 사용하는 요청 형식과 응답 형식을 설명합니다.

### 테스트 앱 생성

CLOVA Studio API를 사용하려면 테스트 앱 또는 서비스 앱을 생성해야 합니다. 앱은 네이버 클라우드 플랫폼 콘솔에서 생성할 수 있습니다. 자세한 내용은 [CLOVA Studio 사용 가이드](https://guide.ncloud-docs.com/docs/clovastudio-playground01#%ED%85%8C%EC%8A%A4%ED%8A%B8-%EC%95%B1-%EC%83%9D%EC%84%B1)를 참조해 주십시오.

### 요청

#### API URL

요청 API URL은 다음과 같습니다.

```http
https://clovastudio.stream.ntruss.com/
```

> **참고**
> 기존 요청 API URL (`https://clovastudio.apigw.ntruss.com/`)로도 계속해서 CLOVA Studio API를 이용할 수 있으나, 제공 중단이 예정되어 있으므로 변경할 것을 권고합니다. 기존 요청 API URL을 이용할 경우 신규 API 키를 통한 인증이 불가하며 생성되는 토큰을 하나씩 출력하는 스트리밍 응답을 사용할 수 없습니다.

#### 요청 헤더

요청 헤더에 대한 설명은 다음과 같습니다.

| 필드            | 필수 여부    | 설명 (예시)                                  |
| ------------- | -------- | ---------------------------------------- |
| Authorization | Required | 인증을 위한 API 키 <예시> `Bearer nv-**********` |
| Content-Type  | Required | `application/json`                       |

### 응답

#### 응답 바디

응답 바디에 대한 설명은 다음과 같습니다.

| 필드               | 타입     | 필수 여부 | 설명       |
| ---------------- | ------ | ----- | -------- |
| `status`         | Object | -     | 응답 상태    |
| `status.code`    | String | -     | 응답 상태 코드 |
| `status.message` | String | -     | 응답 메시지   |
| `result`         | Any    | -     | 응답 결과    |

> **참고**
> 응답 상태 코드별 원인 및 해결 방법은 [CLOVA Studio 문제 해결](/docs/clovastudio-troubleshoot)을 참조해 주십시오.

#### 응답 예시

* **성공**

  ```json
  {
    "status": {
      "code": "20000",
      "message": "OK"
    },
    "result": {}
  }
  ```

* **실패**

  ```json
  {
    "status": {
      "code": "50000",
      "message": "Internal Server Error"
    }
  }
  ```

* **실패(오픈AI 호환 API)**

  ```json
  {
    "error": {
      "message": "Internal Server Error",
      "type": null,
      "param": null, //미지원
      "code": "50000"
    }
  }
  ```

## CLOVA Studio API

CLOVA Studio에서 제공하는 API는 다음과 같습니다.

| API                                                                                           | 설명                                                           |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| [Chat Completions](/docs/clovastudio-chatcompletions)                                         | HyperCLOVA X 모델을 활용한 대화형 문장 생성                               |
| [Chat Completions v3 (텍스트 및 이미지)](/release-20250619/docs/clovastudio-chatcompletionsv3)       | 비전/언어 모델을 활용한 이미지 해석 또는 대화형 문장 생성                            |
| [Chat Completions v3 (Fuction Calling)](/release-20250619/docs/clovastudio-chatcompletionsv3) | 외부 함수나 API를 호출해 동적으로 정보를 가져오거나 작업을 수행할 수 있는 Function calling |
| [Completions](/docs/clovastudio-completions)                                                  | 플레이그라운드의 일반 모드(LK 모델)를 통한 문장 생성                              |
| [오픈AI 호환성](/release-20250619/docs/%EC%98%A4%ED%94%88ai-%ED%98%B8%ED%99%98%EC%84%B1)           | 주요 API에 대한 오픈AI SDK 및 API 호환성 제공                             |
| [학습 조회](/docs/clovastudio-gettask)                                                            | 학습 현황 조회                                                     |
| [학습 목록 조회](/docs/clovastudio-gettasks)                                                        | 생성한 학습 목록 조회                                                 |
| [학습 생성](/docs/clovastudio-posttask)                                                           | 사용자의 데이터셋을 사용한 학습 생성                                         |
| [학습 삭제](/docs/clovastudio-deletetask)                                                         | 생성한 학습 삭제                                                    |
| [토큰 계산기(챗)](/docs/clovastudio-tokenizerhcx)                                                   | HCX 모델(Chat Completions API)에서 입력한 문장의 토큰 수 계산               |
| [토큰 계산기(챗 v3)](/docs/clovastudio-tokenizerhcxv3)                                              | HCX 모델(Chat Completions v3 API)에서 입력한 문장 및 이미지의 토큰 수 계산      |
| [토큰 계산기(임베딩 v2)](/docs/clovastudio-tokenizerembedding)                                        | 임베딩 v2에서 입력한 문장의 토큰 수 계산                                     |
| [토큰 계산기](/docs/clovastudio-tokenizer)                                                         | HCX 외 모델(Completions API)에서 입력한 문장의 토큰 수 계산                  |
| [슬라이딩 윈도우](/docs/clovastudio-sliding)                                                         | Chat Completions 이용 시 최대 토큰 수를 초과하는 문장 처리                    |
| [문단 나누기](/docs/clovastudio-segmentation)                                                      | 문장 간 유사도를 파악하여 주제 단위로 글의 단락 구분                               |
| [요약](/docs/clovastudio-summarization)                                                         | 다양한 옵션을 적용하여 긴 문장 요약                                         |
| [임베딩](/docs/clovastudio-embedding)                                                            | 텍스트를 숫자로 표현하는 벡터화 작업 수행                                      |
| [임베딩 v2](/docs/clovastudio-embeddingv2)                                                       | 장문 텍스트를 숫자로 표현하는 벡터화 작업 수행                                   |
| [스킬셋](/docs/clovastudio-generateskillsetfinalanswer)                                          | 스킬셋 API 호출로 답변 생성                                            |
| [라우터](/docs/clovastudio-router)                                                               | 사용자 입력에 대해 도메인과 필터 판별 수행                                     |

## CLOVA Studio 연관 리소스

CLOVA Studio API에 대한 사용자의 이해를 돕기 위해 다양한 연관 리소스를 제공하고 있습니다.

* **CLOVA Studio API 사용 방법**

  * [API 개요](/docs/common-ncpapi): 네이버 클라우드 플랫폼에서 발급받은 Access Key, Secret Key 발급 및 확인, 요청 헤더에 필요한 서명 생성 방법
  * [Sub Account 사용 가이드](https://guide.ncloud-docs.com/docs/subaccount-overview): 네이버 클라우드 플랫폼에서 발급받은 서브 계정의 Access Key 발급 및 확인 방법

* **CLOVA Studio 서비스 사용 방법**

  * [CLOVA Studio 사용 가이드](https://guide.ncloud-docs.com/docs/clovastudio-overview): 네이버 클라우드 플랫폼 콘솔에서 CLOVA Studio 사용하는 방법
  * [Ncloud 사용 환경 가이드](https://guide.ncloud-docs.com//docs/environment-environment-1-1): VPC, Classic 환경 및 지원 여부에 관한 사용 가이드
  * [요금 소개, 특징, 상세 기능](https://www.ncloud.com/product/aiService/clovaStudio): CLOVA Studio의 요금 체계, 특징, 상세 기능 및 활용 예시 요약
  * [서비스 최신 소식](https://www.ncloud.com/intro/news): CLOVA Studio 관련 최신 소식
  * [문의하기](https://www.ncloud.com/support/question/service): 사용 가이드를 통해서도 궁금증이 해결되지 않는 경우 직접 문의
  * [CLOVA Studio 포럼](https://www.ncloud-forums.com/forum/4/): CLOVA Studio 관련 공지, 활용법, 사용 경험 공유, 이용 문의

---

Next: 텍스트 및 이미지
