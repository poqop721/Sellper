# Sellper
Naver shopping scraping service that provide category, tag, product name searching

네이버 쇼핑 카테고리 / 제목 / 태그 검색 프로그램

링크 : [http://sellper.shop/](http://sellper.shop/)

### 구현 목표
네이버 쇼핑에 등록된 상품들의 제목, 등록된 카테고리, 삽입된 태그들을 원하는 방식으로 수집해온다.

### 이용 방법

1. 검색어를 입력한다.
2. 카테고리, 제목, 태그 수집할 항목을 선택한다. (복수 선택 가능)
  - 광고 포함을 선택하면 광고 상품도 같이 수집되고, 해제하면 광고 상품은 제외된다.
  - 태그 기능은 많은 시간이 소요됩니다. (분석 상품 갯수 `5개 1분`, `15개 3분`, `25개 5분`, `35개 7분`, `45개 10분`정도 소요)
3. 분석할 상품 갯수를 선택한다. (분석 상품 수가 많을수록 소요 시간이 증가합니다)
4. 네이버 쇼핑에서 분석할 상품 기준을 선택한다. (네이버 랭킹순, 리뷰 많은순, 리뷰 좋은순)
5. `카테고리 & 제목 찾기` 버튼을 눌러 검색한다. (`네이버쇼핑 검색하기` 버튼은 입력한 검색어의 네이버 쇼핑 탭을 엽니다.)

> `카테고리` 검색 결과에서 각각 카테고리 이름을 클릭하면 클립보드에 복사됩니다.
> `태그` 검색 결과에서 각각 태그 이름을 클릭하면 클립보드에 복사됩니다.
> 
> `제목` 검색 결과는 중복된 키워드를 제거한 결과입니다. (예를 들어 첫번째 상품이 여행용 가방, 두번째 상품이 호신용 가방이면 결과에는 `여행용 가방 호신용` 처럼 출력됩니다.)
>
> `제목` 옆에 숫자는 각 줄의 글자 수를 의미하며, 숫자 색은 50자가 넘어가면 빨간색이 됩니다.
>
> `제목` 옆에 숫자를 클릭하면 그 줄이 복사됩니다.

### 개발 기간
2023.07.15 ~ 2023.08.05

### 기술 스택
- 언어 : `HTML`, `CSS`, `JavaScript`
- 프레임워크 : `flask`, `bootstrap`
- 라이브러리 : `jQuery`
- 웹 스크래핑 : `beautifulSoup4`, `Selenium`
- 배포 : `aws ec2 free tier`

### 마누했던 문제점과 해결
- beautifulSoup로 상품을 스크래핑 해 올때 정적인 페이지만 갖고올 수 있으므로 최대 5개 상품밖에 못 가져오는 문제가 있었다. <br>이를 해결하기 위해 selenium을 사용해서 `body.send_keys(Keys.PAGE_DOWN)` 로 여러개의 상품을 받아올 수 있게 하였다. <br>그러나 이렇게 하니 사용자가 5개의 상품만 분석을 요청하여도 selenium으로 웹드라이버를 사용해서 크롬에서 스크래핑을 해오기 때문에 비효율적이었다. <br>때문에 사용자가 5개의 상품을 요청할때는 BeautifulSoup4로 정적인 페이지만 스크래핑 해오게 수정하였다.
- 네이버 서버에서 서버의 부담을 막기 위해 사용자가 아닌 컴퓨터(BeautifulSoup4)의 접근을 막아 정보를 가져올 수 없는 문제가 있었다. <br> 이를 해결하기 위해 bs4로 요청할 때 header에 userAgent를 주어 사용자임을 알리는 방식으로 문제를 해결하였다. <br>그러나 시간이 지나고 네이버의 서버 개선으로 인해 이 방법 또한 막히게 되었다.<br>이를 해결하기 위해 `random_user_agent` 에서 랜덤 user agent 정보를 받아와서 매번 새로운 무작위의 요청 Header를 만들어 인스턴스를 리턴하는 객체를 만들어 해결하였다.
  ```python
  class RandomUserAgentTest:
      def __init__(self):
          self.get_headers()
  
      def set_user_agent(self):
          software_names = [SoftwareName.CHROME.value]
          operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
          user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
          self.user_agent = user_agent_rotator.get_random_user_agent()
  
      def get_headers(self):
          self.set_user_agent()
          self.headers = {
              "User-Agent": self.user_agent,
          }
      def ret_headers(self):
          return self.headers
  ```
- <2024/04/14 수정> 네이버의 업데이트로 위 방법으로 얻은 `user_agent` 중 일부는 막혀서 정보를 가져올 수 없는 문제가 발생하였다. 또한 막히는 `user_agent`가 어떨 땐 되고 어떨 땐 안되는 무작위한 특성이 있어서, 그 특정 `user_agent`만 제외시킨다고 해도 문제가 되었다. 때문에 10번을 반복하면서 새로운 `user_agent`를 생성하여 되는 `user_agent`를 찾을 때 까지 시도하는 방법으로 바꾸어 해결하였다.
- <2024/04/16 수정> 네이버의 업데이트로 driver.get()을 할 때 몇번은 application error가 발생하는 문제가 생겼다. 게다가 application error가 발생하면 driver.close() 도 먹히지 않아 무한 대기가 발생하여, 여러번 시도하는것 조차 되지 않는 상황이었다. 때문에 각 시도를 thread로 만들어서 timeout을 주어, 시간 초과시 thread를 join 하여 무한 대기에서 빠져나오고, 다시 반복하여 스레드를 만들어 탐색하는 방법으로 수정하였다.
  ```python
  while(True):
     if count > try_num:
        break
     thread = threading.Thread(target=self.__get_driver_t)
     thread.start()
     self.event.wait()
     if self.done == False:
        print(f'\n<failed driver.get - retrying ({count}/{try_num})>')
        thread.join() 
        count = count + 1
     else :
        break
  ```
  

### 아쉬운 점 & 개선할 점
태그 검색은 네이버 쇼핑 페이지에서 각각 상품 url을 얻어와 그 상품 안에서 태그를 검색한다. 때문에 기존 구현(2023.08)때는 각각 상품의 URl을 beautifulsoup4로 넘겨주어 정적인 페이지에서 태그를 갖고 올 수 있었으며, 이로 인해 태그 검색 소요 시간을 단축시킬 수 있었다.

하지만 현재(2024.03)는 beautifulSoup4로 각각의 상품 url을 넘겨주는 방식이 네이버에 의해 차단당했다. userAgent를 랜덤하게 매번 바꾸어 보아도 소용이 없다. 

때문에 일단은 태그 검색은 selenium을 사용하게 하여 스크래핑이 안되는 문제는 해결하였다. 하지만 이 방법은 크롬이 각각 모든 URL에 접속하여 정보를 가져오는 방법이므로 많은 시간이 소요된다. 게다가 ec2 free tier를 사용중이므로 크롬 탐색 시간이 매우 느리다. 추후 이 문제를 개선해 볼 예정이다.
