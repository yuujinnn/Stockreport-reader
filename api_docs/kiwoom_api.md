## 키움 API의 TR 별 요청 및 응답 구조

### 주식틱차트조회요청 (ka10079)

Request Header

| Element       | 한글명    | Type   | Required | Length | Description                                            |
| ------------- | ------ | ------ | -------- | ------ | ------------------------------------------------------ |
| authorization | 접근토큰   | String | Y        | 1000   | 토큰 지정 시 토큰타입("Bearer") 붙여서 호출<br>예) `Bearer Egicyx...` |
| cont-yn       | 연속조회여부 | String | N        | 1      | 응답 Header의 연속조회여부값이 `Y`일 경우, 다음 데이터 요청 시 cont-yn 값 세팅  |
| next-key      | 연속조회키  | String | N        | 50     | 응답 Header의 연속조회여부값이 `Y`일 경우, 다음 데이터 요청 시 next-key 값 세팅 |
| api-id        | TR명    | String | Y        | 10     |                                                        |

Request Body

| Element        | 한글명    | Type   | Required | Length | Description                                            |
| -------------- | ------ | ------ | -------- | ------ | ------------------------------------------------------ |
| stk\_cd        | 종목코드   | String | Y        | 20     | 종목코드(KRX)                                            |
| tic\_scope     | 틱범위    | String | Y        | 2      | `1`:1틱, `3`:3틱, `5`:5틱, `10`:10틱, `30`:30틱             |
| upd\_stkpc\_tp | 수정주가구분 | String | Y        | 1      | `0` or `1`                                             |

Response Header

| Element  | 한글명    | Type   | Required | Length | Description           |
| -------- | ------ | ------ | -------- | ------ | --------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을 시 `Y` 전달   |
| next-key | 연속조회키  | String | N        | 50     | 다음 데이터가 있을 시 다음 키값 전달 |
| api-id   | TR명    | String | Y        | 10     |                       |

Response Body

| Element              | 한글명     | Type   | Required | Length | Description  |
| -------------------- | ------- | ------ | -------- | ------ | ------------ |
| stk\_cd              | 종목코드    | String | N        | 6      |              |
| last\_tic\_cnt       | 마지막틱갯수  | String | N        |        |              |
| stk\_tic\_chart\_qry | 주식틱차트조회 | LIST   | N        |        | 아래 필드 리스트 참조 |

stk\_tic\_chart\_qry 항목

| Element           | 한글명     | Type   | Required | Length | Description                                                                     |
| ----------------- | ------- | ------ | -------- | ------ | ------------------------------------------------------------------------------- |
| cur\_prc          | 현재가     | String | N        | 20     |                                                                                 |
| trde\_qty         | 거래량     | String | N        | 20     |                                                                                 |
| cntr\_tm          | 체결시간    | String | N        | 20     |                                                                                 |
| open\_pric        | 시가      | String | N        | 20     |                                                                                 |
| high\_pric        | 고가      | String | N        | 20     |                                                                                 |
| low\_pric         | 저가      | String | N        | 20     |                                                                                 |
| upd\_stkpc\_tp    | 수정주가구분  | String | N        | 20     | `1`:유상증자, `2`:무상증자, `4`:배당락, `8`:액면분할, `16`:액면병합, `32`:기업합병, `64`:감자, `256`:권리락 |
| upd\_rt           | 수정비율    | String | N        | 20     |                                                                                 |
| bic\_inds\_tp     | 대업종구분   | String | N        | 20     |                                                                                 |
| sm\_inds\_tp      | 소업종구분   | String | N        | 20     |                                                                                 |
| stk\_infr         | 종목정보    | String | N        | 20     |                                                                                 |
| upd\_stkpc\_event | 수정주가이벤트 | String | N        | 20     |                                                                                 |
| pred\_close\_pric | 전일종가    | String | N        | 20     |                                                                                 |

Request 예시
```
{
	"stk_cd" : "005930",
	"tic_scope" : "1",
	"upd_stkpc_tp" : "1"
}
```

Response 예시
```
{
	"stk_cd":"005930",
	"last_tic_cnt":"",
	"stk_tic_chart_qry":
		[
			{
				"cur_prc":"132500",
				"trde_qty":"1",
				"cntr_tm":"20241106141853",
				"open_pric":"132500",
				"high_pric":"132500",
				"low_pric":"132500",
				"upd_stkpc_tp":"",
				"upd_rt":"",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			},
			{
				"cur_prc":"132600",
				"trde_qty":"10",
				"cntr_tm":"20241106111111",
				"open_pric":"132600",
				"high_pric":"132600",
				"low_pric":"132600",
				"upd_stkpc_tp":"",
				"upd_rt":"",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			},
			{
				"cur_prc":"132600",
				"trde_qty":"10",
				"cntr_tm":"20241106110519",
				"open_pric":"132600",
				"high_pric":"132600",
				"low_pric":"132600",
				"upd_stkpc_tp":"",
				"upd_rt":"",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

### 주식분봉차트조회요청 (ka10080)

Request Header

| Element       | 한글명    | Type   | Required | Length | Description                                            |
| ------------- | ------ | ------ | -------- | ------ | ------------------------------------------------------ |
| authorization | 접근토큰   | String | Y        | 1000   | 토큰 지정 시 토큰타입("Bearer") 붙여서 호출<br>예) `Bearer Egicyx...` |
| cont-yn       | 연속조회여부 | String | N        | 1      | 응답 Header의 연속조회여부값이 `Y`일 경우, 다음 데이터 요청 시 cont-yn 값 세팅  |
| next-key      | 연속조회키  | String | N        | 50     | 응답 Header의 연속조회여부값이 `Y`일 경우, 다음 데이터 요청 시 next-key 값 세팅 |
| api-id        | TR명    | String | Y        | 10     |                                                        |

Request Body

| Element        | 한글명    | Type   | Required | Length | Description                                                              |
| -------------- | ------ | ------ | -------- | ------ | ------------------------------------------------------------------------ |
| stk\_cd        | 종목코드   | String | Y        | 20     | 종목코드(KRX)                                            |
| tic\_scope     | 틱범위    | String | Y        | 2      | `1`:1분, `3`:3분, `5`:5분, `10`:10분, `15`:15분, `30`:30분, `45`:45분, `60`:60분 |
| upd\_stkpc\_tp | 수정주가구분 | String | Y        | 1      | `0` or `1`                                                               |

Response Header

| Element  | 한글명    | Type   | Required | Length | Description           |
| -------- | ------ | ------ | -------- | ------ | --------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을 시 `Y` 전달   |
| next-key | 연속조회키  | String | N        | 50     | 다음 데이터가 있을 시 다음 키값 전달 |
| api-id   | TR명    | String | Y        | 10     |                       |

Response Body

| Element                    | 한글명      | Type   | Required | Length | Description  |
| -------------------------- | -------- | ------ | -------- | ------ | ------------ |
| stk\_cd                    | 종목코드     | String | N        | 6      |              |
| stk\_min\_pole\_chart\_qry | 주식분봉차트조회 | LIST   | N        |        | 아래 필드 리스트 참조 |

stk\_min\_pole\_chart\_qry 항목

| Element           | 한글명     | Type   | Required | Length | Description                                                                     |
| ----------------- | ------- | ------ | -------- | ------ | ------------------------------------------------------------------------------- |
| cur\_prc          | 현재가     | String | N        | 20     |                                                                                 |
| trde\_qty         | 거래량     | String | N        | 20     |                                                                                 |
| cntr\_tm          | 체결시간    | String | N        | 20     |                                                                                 |
| open\_pric        | 시가      | String | N        | 20     |                                                                                 |
| high\_pric        | 고가      | String | N        | 20     |                                                                                 |
| low\_pric         | 저가      | String | N        | 20     |                                                                                 |
| upd\_stkpc\_tp    | 수정주가구분  | String | N        | 20     | `1`:유상증자, `2`:무상증자, `4`:배당락, `8`:액면분할, `16`:액면병합, `32`:기업합병, `64`:감자, `256`:권리락 |
| upd\_rt           | 수정비율    | String | N        | 20     |                                                                                 |
| bic\_inds\_tp     | 대업종구분   | String | N        | 20     |                                                                                 |
| sm\_inds\_tp      | 소업종구분   | String | N        | 20     |                                                                                 |
| stk\_infr         | 종목정보    | String | N        | 20     |                                                                                 |
| upd\_stkpc\_event | 수정주가이벤트 | String | N        | 20     |                                                                                 |
| pred\_close\_pric | 전일종가    | String | N        | 20     |                                                                                 |

Request 예시
```
{
	"stk_cd" : "005930",
	"tic_scope" : "1",
	"upd_stkpc_tp" : "1"
}
```

Response 예시
```
{
	"stk_cd":"005930",
	"stk_min_pole_chart_qry":
		[
			{
				"cur_prc":"-132500",
				"trde_qty":"1",
				"cntr_tm":"20241106141800",
				"open_pric":"-132500",
				"high_pric":"-132500",
				"low_pric":"-132500",
				"upd_stkpc_tp":"",
				"upd_rt":"",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			},
			{
				"cur_prc":"-132600",
				"trde_qty":"10",
				"cntr_tm":"20241106111100",
				"open_pric":"-132600",
				"high_pric":"-132600",
				"low_pric":"-132600",
				"upd_stkpc_tp":"",
				"upd_rt":"",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			},
			{
				"cur_prc":"-132600",
				"trde_qty":"20",
				"cntr_tm":"20241106110500",
				"open_pric":"133100",
				"high_pric":"133100",
				"low_pric":"-132600",
				"upd_stkpc_tp":"",
				"upd_rt":"",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

### 주식일봉차트조회요청 (ka10081)

Request Header

| Element               | 한글명    | Type   | Required | Length | Description                                            |
| --------------------- | ------ | ------ | -------- | ------ | ------------------------------------------------------ |
| authorization         | 접근토큰   | String | Y        | 1000   | 토큰 지정 시 토큰타입("Bearer") 붙여서 호출                          |
| 예) `Bearer Egicyx...` |        |        |          |        |                                                        |
| cont-yn               | 연속조회여부 | String | N        | 1      | 응답 Header의 연속조회여부값이 `Y`일 경우, 다음 데이터 요청 시 cont-yn 값 세팅  |
| next-key              | 연속조회키  | String | N        | 50     | 응답 Header의 연속조회여부값이 `Y`일 경우, 다음 데이터 요청 시 next-key 값 세팅 |
| api-id                | TR명    | String | Y        | 10     |                                                        |

Request Body

| Element        | 한글명    | Type   | Required | Length | Description                                            |
| -------------- | ------ | ------ | -------- | ------ | ------------------------------------------------------ |
| stk\_cd        | 종목코드   | String | Y        | 20     | 종목코드(KRX)                                            |
| base\_dt       | 기준일자   | String | Y        | 8      | 조회 기준 일자 (YYYYMMDD)                                    |
| upd\_stkpc\_tp | 수정주가구분 | String | Y        | 1      | `0` or `1`                                             |

Response Header

| Element  | 한글명    | Type   | Required | Length | Description           |
| -------- | ------ | ------ | -------- | ------ | --------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을 시 `Y` 전달   |
| next-key | 연속조회키  | String | N        | 50     | 다음 데이터가 있을 시 다음 키값 전달 |
| api-id   | TR명    | String | Y        | 10     |                       |

Response Body

| Element                   | 한글명      | Type   | Required | Length | Description  |
| ------------------------- | -------- | ------ | -------- | ------ | ------------ |
| stk\_cd                   | 종목코드     | String | N        | 6      |              |
| stk\_dt\_pole\_chart\_qry | 주식일봉차트조회 | LIST   | N        |        | 아래 필드 리스트 참조 |

stk\_dt\_pole\_chart\_qry 항목

| Element           | 한글명     | Type   | Required | Length | Description                                                                     |
| ----------------- | ------- | ------ | -------- | ------ | ------------------------------------------------------------------------------- |
| cur\_prc          | 현재가     | String | N        | 20     |                                                                                 |
| trde\_qty         | 거래량     | String | N        | 20     |                                                                                 |
| trde\_prica       | 거래대금    | String | N        | 20     |                                                                                 |
| dt                | 일자      | String | N        | 20     |                                                                                 |
| open\_pric        | 시가      | String | N        | 20     |                                                                                 |
| high\_pric        | 고가      | String | N        | 20     |                                                                                 |
| low\_pric         | 저가      | String | N        | 20     |                                                                                 |
| upd\_stkpc\_tp    | 수정주가구분  | String | N        | 20     | `1`:유상증자, `2`:무상증자, `4`:배당락, `8`:액면분할, `16`:액면병합, `32`:기업합병, `64`:감자, `256`:권리락 |
| upd\_rt           | 수정비율    | String | N        | 20     |                                                                                 |
| bic\_inds\_tp     | 대업종구분   | String | N        | 20     |                                                                                 |
| sm\_inds\_tp      | 소업종구분   | String | N        | 20     |                                                                                 |
| stk\_infr         | 종목정보    | String | N        | 20     |                                                                                 |
| upd\_stkpc\_event | 수정주가이벤트 | String | N        | 20     |                                                                                 |
| pred\_close\_pric | 전일종가    | String | N        | 20     |                                                                                 |

Request 예시
```
{
	"stk_cd" : "005930",
	"base_dt" : "20241108",
	"upd_stkpc_tp" : "1"
}
```

Response 예시
```
{
	"stk_cd":"005930",
	"stk_dt_pole_chart_qry":
		[
			{
				"cur_prc":"133600",
				"trde_qty":"0",
				"trde_prica":"0",
				"dt":"20241107",
				"open_pric":"133600",
				"high_pric":"133600",
				"low_pric":"133600",
				"upd_stkpc_tp":"",
				"upd_rt":"+0.83",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			},
			{
				"cur_prc":"133600",
				"trde_qty":"53",
				"trde_prica":"7",
				"dt":"20241106",
				"open_pric":"134205",
				"high_pric":"134205",
				"low_pric":"133600",
				"upd_stkpc_tp":"",
				"upd_rt":"-1.63",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			},
			{
				"cur_prc":"134204",
				"trde_qty":"0",
				"trde_prica":"0",
				"dt":"20241105",
				"open_pric":"134204",
				"high_pric":"134204",
				"low_pric":"134204",
				"upd_stkpc_tp":"",
				"upd_rt":"+107.83",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			},
			{
				"cur_prc":"134204",
				"trde_qty":"0",
				"trde_prica":"0",
				"dt":"20241101",
				"open_pric":"134204",
				"high_pric":"134204",
				"low_pric":"134204",
				"upd_stkpc_tp":"",
				"upd_rt":"",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

### 주식주봉차트조회요청 (ka10082)

Request Header

| Element               | 한글명    | Type   | Required | Length | Description                                            |
| --------------------- | ------ | ------ | -------- | ------ | ------------------------------------------------------ |
| authorization         | 접근토큰   | String | Y        | 1000   | 토큰 지정 시 토큰타입("Bearer") 붙여서 호출                          |
| 예) `Bearer Egicyx...` |        |        |          |        |                                                        |
| cont-yn               | 연속조회여부 | String | N        | 1      | 응답 Header의 연속조회여부값이 `Y`일 경우, 다음 데이터 요청 시 cont-yn 값 세팅  |
| next-key              | 연속조회키  | String | N        | 50     | 응답 Header의 연속조회여부값이 `Y`일 경우, 다음 데이터 요청 시 next-key 값 세팅 |
| api-id                | TR명    | String | Y        | 10     |                                                        |

Request Body

| Element        | 한글명    | Type   | Required | Length | Description                                            |
| -------------- | ------ | ------ | -------- | ------ | ------------------------------------------------------ |
| stk\_cd        | 종목코드   | String | Y        | 20     | 종목코드(KRX)                                            |
| base\_dt       | 기준일자   | String | Y        | 8      | 조회 기준 일자 (YYYYMMDD)                                    |
| upd\_stkpc\_tp | 수정주가구분 | String | Y        | 1      | `0` or `1`                                             |

Response Header

| Element  | 한글명    | Type   | Required | Length | Description           |
| -------- | ------ | ------ | -------- | ------ | --------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을 시 `Y` 전달   |
| next-key | 연속조회키  | String | N        | 50     | 다음 데이터가 있을 시 다음 키값 전달 |
| api-id   | TR명    | String | Y        | 10     |                       |

Response Body

| Element                    | 한글명      | Type   | Required | Length | Description  |
| -------------------------- | -------- | ------ | -------- | ------ | ------------ |
| stk\_cd                    | 종목코드     | String | N        | 6      |              |
| stk\_stk\_pole\_chart\_qry | 주식주봉차트조회 | LIST   | N        |        | 아래 필드 리스트 참조 |

stk\_stk\_pole\_chart\_qry 항목

| Element           | 한글명     | Type   | Required | Length | Description                                                                     |
| ----------------- | ------- | ------ | -------- | ------ | ------------------------------------------------------------------------------- |
| cur\_prc          | 현재가     | String | N        | 20     |                                                                                 |
| trde\_qty         | 거래량     | String | N        | 20     |                                                                                 |
| trde\_prica       | 거래대금    | String | N        | 20     |                                                                                 |
| dt                | 일자      | String | N        | 20     |                                                                                 |
| open\_pric        | 시가      | String | N        | 20     |                                                                                 |
| high\_pric        | 고가      | String | N        | 20     |                                                                                 |
| low\_pric         | 저가      | String | N        | 20     |                                                                                 |
| upd\_stkpc\_tp    | 수정주가구분  | String | N        | 20     | `1`:유상증자, `2`:무상증자, `4`:배당락, `8`:액면분할, `16`:액면병합, `32`:기업합병, `64`:감자, `256`:권리락 |
| upd\_rt           | 수정비율    | String | N        | 20     |                                                                                 |
| bic\_inds\_tp     | 대업종구분   | String | N        | 20     |                                                                                 |
| sm\_inds\_tp      | 소업종구분   | String | N        | 20     |                                                                                 |
| stk\_infr         | 종목정보    | String | N        | 20     |                                                                                 |
| upd\_stkpc\_event | 수정주가이벤트 | String | N        | 20     |                                                                                 |
| pred\_close\_pric | 전일종가    | String | N        | 20     |                                                                                 |

Request 예시
```
{
	"stk_cd" : "005930",
	"base_dt" : "20241108",
	"upd_stkpc_tp" : "1"
}
```

Response 예시
```
{
	"stk_cd":"005930",
	"stk_stk_pole_chart_qry":
		[
			{
				"cur_prc":"127600",
				"trde_qty":"53",
				"trde_prica":"7043700",
				"dt":"20241105",
				"open_pric":"134199",
				"high_pric":"134205",
				"low_pric":"127600",
				"upd_stkpc_tp":"",
				"upd_rt":"+106.14",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			},
			{
				"cur_prc":"134197",
				"trde_qty":"49",
				"trde_prica":"9292500",
				"dt":"20241028",
				"open_pric":"196658",
				"high_pric":"196658",
				"low_pric":"133991",
				"upd_stkpc_tp":"",
				"upd_rt":"",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			},
			{
				"cur_prc":"196658",
				"trde_qty":"340",
				"trde_prica":"65933500",
				"dt":"20241021",
				"open_pric":"193978",
				"high_pric":"196658",
				"low_pric":"193978",
				"upd_stkpc_tp":"",
				"upd_rt":"",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			},
			{
				"cur_prc":"200574",
				"trde_qty":"45",
				"trde_prica":"12362000",
				"dt":"20241014",
				"open_pric":"272105",
				"high_pric":"287771",
				"low_pric":"200574",
				"upd_stkpc_tp":"",
				"upd_rt":"",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

### 주식월봉차트조회요청 (ka10083)

Request Header

| Element               | 한글명    | Type   | Required | Length | Description                                         |
| --------------------- | ------ | ------ | -------- | ------ | --------------------------------------------------- |
| authorization         | 접근토큰   | String | Y        | 1000   | 토큰 지정 시 토큰타입("Bearer") 붙여서 호출                       |
| 예) `Bearer Egicyx...` |        |        |          |        |                                                     |
| cont-yn               | 연속조회여부 | String | N        | 1      | 응답 Header의 cont-yn 값이 `Y`일 경우, 다음 데이터 요청 시 해당 값을 설정 |
| next-key              | 연속조회키  | String | N        | 50     | 응답 Header의 next-key 값이 있을 경우, 다음 데이터 요청 시 해당 값을 설정  |
| api-id                | TR명    | String | Y        | 10     |                                                     |

Request Body

| Element        | 한글명    | Type   | Required | Length | Description                                            |
| -------------- | ------ | ------ | -------- | ------ | ------------------------------------------------------ |
| stk\_cd        | 종목코드   | String | Y        | 20     | 종목코드(KRX)                                            |
| base\_dt       | 기준일자   | String | Y        | 8      | 기준 일자 (YYYYMMDD)                                       |
| upd\_stkpc\_tp | 수정주가구분 | String | Y        | 1      | `0` 또는 `1`                                             |

Response Header

| Element  | 한글명    | Type   | Required | Length | Description          |
| -------- | ------ | ------ | -------- | ------ | -------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을 경우 `Y` 전달 |
| next-key | 연속조회키  | String | N        | 50     | 다음 데이터가 있을 경우 키값 전달  |
| api-id   | TR명    | String | Y        | 10     |                      |

Response Body

| Element                    | 한글명      | Type   | Required | Length | Description  |
| -------------------------- | -------- | ------ | -------- | ------ | ------------ |
| stk\_cd                    | 종목코드     | String | N        | 6      |              |
| stk\_mth\_pole\_chart\_qry | 주식월봉차트조회 | LIST   | N        |        | 아래 필드 리스트 참조 |

stk\_mth\_pole\_chart\_qry 항목

| Element           | 한글명     | Type   | Required | Length | Description                                                                     |
| ----------------- | ------- | ------ | -------- | ------ | ------------------------------------------------------------------------------- |
| cur\_prc          | 현재가     | String | N        | 20     |                                                                                 |
| trde\_qty         | 거래량     | String | N        | 20     |                                                                                 |
| trde\_prica       | 거래대금    | String | N        | 20     |                                                                                 |
| dt                | 일자      | String | N        | 20     |                                                                                 |
| open\_pric        | 시가      | String | N        | 20     |                                                                                 |
| high\_pric        | 고가      | String | N        | 20     |                                                                                 |
| low\_pric         | 저가      | String | N        | 20     |                                                                                 |
| upd\_stkpc\_tp    | 수정주가구분  | String | N        | 20     | `1`:유상증자, `2`:무상증자, `4`:배당락, `8`:액면분할, `16`:액면병합, `32`:기업합병, `64`:감자, `256`:권리락 |
| upd\_rt           | 수정비율    | String | N        | 20     |                                                                                 |
| bic\_inds\_tp     | 대업종구분   | String | N        | 20     |                                                                                 |
| sm\_inds\_tp      | 소업종구분   | String | N        | 20     |                                                                                 |
| stk\_infr         | 종목정보    | String | N        | 20     |                                                                                 |
| upd\_stkpc\_event | 수정주가이벤트 | String | N        | 20     |                                                                                 |
| pred\_close\_pric | 전일종가    | String | N        | 20     |                                                                                 |

Request 예시
```
{
	"stk_cd" : "005930",
	"base_dt" : "20241108",
	"upd_stkpc_tp" : "1"
}
```

Response 예시
```
{
	"stk_cd":"005930",
	"stk_mth_pole_chart_qry":
		[
			{
				"cur_prc":"127600",
				"trde_qty":"55",
				"trde_prica":"7043700",
				"dt":"20241101",
				"open_pric":"128171",
				"high_pric":"128179",
				"low_pric":"127600",
				"upd_stkpc_tp":"",
				"upd_rt":"+96.88",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			},
			{
				"cur_prc":"128169",
				"trde_qty":"455",
				"trde_prica":"87853100",
				"dt":"20241002",
				"open_pric":"264016",
				"high_pric":"274844",
				"low_pric":"127972",
				"upd_stkpc_tp":"",
				"upd_rt":"",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			},
			{
				"cur_prc":"264016",
				"trde_qty":"5101",
				"trde_prica":"1354698100",
				"dt":"20240902",
				"open_pric":"265788",
				"high_pric":"269529",
				"low_pric":"188808",
				"upd_stkpc_tp":"",
				"upd_rt":"",
				"bic_inds_tp":"",
				"sm_inds_tp":"",
				"stk_infr":"",
				"upd_stkpc_event":"",
				"pred_close_pric":""
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

### 주식년봉차트조회요청 (ka10094)

Request Header

| Element               | 한글명    | Type   | Required | Length | Description                                         |
| --------------------- | ------ | ------ | -------- | ------ | --------------------------------------------------- |
| authorization         | 접근토큰   | String | Y        | 1000   | 토큰 지정 시 토큰타입("Bearer") 붙여서 호출                       |
| 예) `Bearer Egicyx...` |        |        |          |        |                                                     |
| cont-yn               | 연속조회여부 | String | N        | 1      | 응답 Header의 cont-yn 값이 `Y`일 경우, 다음 데이터 요청 시 해당 값을 설정 |
| next-key              | 연속조회키  | String | N        | 50     | 응답 Header의 next-key 값이 있을 경우, 다음 데이터 요청 시 해당 값을 설정  |
| api-id                | TR명    | String | Y        | 10     |                                                     |

Request Body

| Element        | 한글명    | Type   | Required | Length | Description                                            |
| -------------- | ------ | ------ | -------- | ------ | ------------------------------------------------------ |
| stk\_cd        | 종목코드   | String | Y        | 20     | 종목코드(KRX)                                            |
| base\_dt       | 기준일자   | String | Y        | 8      | 기준 일자 (YYYYMMDD)                                       |
| upd\_stkpc\_tp | 수정주가구분 | String | Y        | 1      | `0` 또는 `1`                                             |

Response Header

| Element  | 한글명    | Type   | Required | Length | Description          |
| -------- | ------ | ------ | -------- | ------ | -------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을 경우 `Y` 전달 |
| next-key | 연속조회키  | String | N        | 50     | 다음 데이터가 있을 경우 키값 전달  |
| api-id   | TR명    | String | Y        | 10     |                      |

Response Body

| Element                   | 한글명      | Type   | Required | Length | Description  |
| ------------------------- | -------- | ------ | -------- | ------ | ------------ |
| stk\_cd                   | 종목코드     | String | N        | 6      |              |
| stk\_yr\_pole\_chart\_qry | 주식년봉차트조회 | LIST   | N        |        | 아래 필드 리스트 참조 |

stk\_yr\_pole\_chart\_qry 항목

| Element           | 한글명     | Type   | Required | Length | Description                                                                     |
| ----------------- | ------- | ------ | -------- | ------ | ------------------------------------------------------------------------------- |
| cur\_prc          | 현재가     | String | N        | 20     |                                                                                 |
| trde\_qty         | 거래량     | String | N        | 20     |                                                                                 |
| trde\_prica       | 거래대금    | String | N        | 20     |                                                                                 |
| dt                | 일자      | String | N        | 20     |                                                                                 |
| open\_pric        | 시가      | String | N        | 20     |                                                                                 |
| high\_pric        | 고가      | String | N        | 20     |                                                                                 |
| low\_pric         | 저가      | String | N        | 20     |                                                                                 |
| upd\_stkpc\_tp    | 수정주가구분  | String | N        | 20     | `1`:유상증자, `2`:무상증자, `4`:배당락, `8`:액면분할, `16`:액면병합, `32`:기업합병, `64`:감자, `256`:권리락 |
| upd\_rt           | 수정비율    | String | N        | 20     |                                                                                 |
| bic\_inds\_tp     | 대업종구분   | String | N        | 20     |                                                                                 |
| sm\_inds\_tp      | 소업종구분   | String | N        | 20     |                                                                                 |
| stk\_infr         | 종목정보    | String | N        | 20     |                                                                                 |
| upd\_stkpc\_event | 수정주가이벤트 | String | N        | 20     |                                                                                 |
| pred\_close\_pric | 전일종가    | String | N        | 20     |                                                                                 |

Request 예시
```
{
	"stk_cd" : "005930",
	"base_dt" : "20241212",
	"upd_stkpc_tp" : "1"
}
```

Response 예시
```
{
	"stk_cd": "005930",
	"stk_yr_pole_chart_qry": [
		{
			"cur_prc": "11510",
			"trde_qty": "83955682",
			"trde_prica": "1473889778085",
			"dt": "20240102",
			"open_pric": "38950",
			"high_pric": "39100",
			"low_pric": "10500",
			"upd_stkpc_tp": "",
			"upd_rt": "",
			"bic_inds_tp": "",
			"sm_inds_tp": "",
			"stk_infr": "",
			"upd_stkpc_event": "",
			"pred_close_pric": ""
		},
		{
			"cur_prc": "39000",
			"trde_qty": "337617963",
			"trde_prica": "16721059332050",
			"dt": "20230102",
			"open_pric": "20369",
			"high_pric": "93086",
			"low_pric": "20369",
			"upd_stkpc_tp": "1,4,256",
			"upd_rt": "-1.60",
			"bic_inds_tp": "",
			"sm_inds_tp": "",
			"stk_infr": "",
			"upd_stkpc_event": "",
			"pred_close_pric": ""
		},
		{
			"cur_prc": "20221",
			"trde_qty": "284497691",
			"trde_prica": "5829021315600",
			"dt": "20220103",
			"open_pric": "13942",
			"high_pric": "30160",
			"low_pric": "9940",
			"upd_stkpc_tp": "1,2,4,256",
			"upd_rt": "-12.54",
			"bic_inds_tp": "",
			"sm_inds_tp": "",
			"stk_infr": "",
			"upd_stkpc_event": "",
			"pred_close_pric": ""
		}
	],
	"return_code": 0,
	"return_msg": "정상적으로 처리되었습니다"
}
```