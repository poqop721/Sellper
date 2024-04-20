import threading
from flask import Flask, render_template, jsonify, request
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time, random
from tqdm import tqdm
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from multiprocessing import Process

app = Flask(__name__)


# HTML
@app.route('/')
def home():
   return render_template('index.html')

# search main
@app.route('/search', methods=['POST'])
def search_category():

   try :
      # 파라미터 받기
      url = request.form['url']
      num_of_page = int(request.form['num_of_pages'])
      check = request.form.getlist('check[]')

      # url에 대한 soup 받아오기
      soup = Soup.get_soup(url, num_of_page)
      if soup == None:
         raise ValueError("soup is None")

      # 일반 상품과 광고 상품 데이터 분석
      analyze_instance = AnalyzeData(soup, check)
      analyze_instance.get_info() 

      # 데이터 후처리
      analyze_instance.after_process()
      returnJson = analyze_instance.make_json()
      del analyze_instance
   except ValueError:
      print()
      return jsonify({'result': 'failed'})


   return returnJson


class ChromeDriver:
   def __init__(self, url):
      self.event = threading.Event()

class Soup:
   @staticmethod
   def get_soup(url, num_of_page):
      # 분석 상품 갯수가 5개일 때
      if num_of_page == 0 : 
         count_exit = 0
         while(count_exit < 11): # 총 10번 시도
            data = requests.get(url,headers=Soup.__get_headers())
            soup = BeautifulSoup(data.text, 'html.parser')
            try: # userAgent 실패시
               if list(soup.select('.head'))[0].text == '부적절한 요청입니다.':
                  count_exit += 1
                  time.sleep(random.uniform(0.7, 1.5))
                  print(f'\n<failed user-agent - retrying : {count_exit} / 10>')
            except: # userAgent 성공시
               break
      # 분석 상품 갯수가 15 이상일 때
      else :
         driver = ChromeDriver(url)
         soup = driver.driver_get_soup(True,num_of_page,10)
         del driver
      return soup
   
   @staticmethod
   def __get_headers():
      software_names = [SoftwareName.CHROME.value]
      operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
      user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
      user_agent = user_agent_rotator.get_random_user_agent()
      return {"User-Agent": user_agent}
   

class AnalyzeData:
   def __init__(self,soup,check):
      # 분석한 데이터(카테고리, 제목, 태그)를 담을 리스트들
      self.cat_result_box = list()
      self.name_result_box = list()
      self.tag_result_box = list()
      self.cat_result = list()
      self.name_result = ''
      self.soup = soup
      self.check = check
      self.num_of_content = 0

   def get_info(self):
      self.__get_info_checking_ad(False) #일반상품
      if self.check[0] == 'false': 
         self.__get_info_checking_ad(True) #광고상품

   def __get_info_checking_ad(self,ad):
      if ad:
         contents = list(self.soup.select('.adProduct_item__1zC9h')) #광고
         desc_msg = '광고 상품 분석중 : '
      else :
         contents = list(self.soup.select('.product_item__MDtDF ')) #no광고
         desc_msg = '일반 상품 분석중 : '

      for content in tqdm(contents,total = len(contents), ## 전체 진행수
               desc = desc_msg, ## 진행률 앞쪽 출력 문장
               ncols = 80,):
         if content is not None:
            self.num_of_content += 1
            name = ''
            
            if self.check[1] == 'false': # 카테고리 검색시
               self.__get_category(content,ad)

            if self.check[2] == 'false': # 제목 검색시
               name = self.__get_name(content, ad)

            if self.check[3] == 'false': # 태그 검색시
               self.__get_tag(content, ad, name)

   def __get_category(self,content, ad):
      if ad:
         cat_list = list(content.select('.adProduct_category__ZIAfP'))
      else:
         cat_list = list(content.select('.product_category__l4FWz'))
      cat_sum = ""
      for cat in cat_list:
         if cat == cat_list[-1]:
            cat_sum += f'<span class="copy_texts" onclick="copy_list(\'{cat.text}\')">{cat.text}</span>'
         else:
            cat_sum = cat_sum + f'<span class="copy_texts" onclick="copy_list(\'{cat.text}\')">{cat.text}</span> > '
      self.cat_result_box.append(cat_sum)

   def __get_name(self,content, ad) : 
      if ad:
         name = content.select_one('.adProduct_link__NYTV9')
      else:
         name = content.select_one('.product_link__TrAac')
      name_sum = name.text.strip()
      self.name_result_box.append(name_sum)
      return name

   def __get_tag(self,content, ad, name):
      if self.check[2] == 'true' and self.check[3] == 'false': # 제목 검색 x, 태그검색 o
         if ad:
            name = content.select_one('.adProduct_link__NYTV9')
         else:
            name = content.select_one('.product_link__TrAac')

      try:
         if ad:
            div_grade = content.select_one('.adProduct_grade__C3wzo').text
         else:
            div_grade = content.select_one('.product_grade__IzyU3').text
      except:
         div_grade = ''
         
      if div_grade in ('파워', '빅파워', '프리미엄'):
         self.__handle_meta_tag(name)

   def __handle_meta_tag(self,name):
      driver = ChromeDriver(name.attrs['href'])
      soup = driver.driver_get_soup(False,None,2)
      del driver
      # 태그 추출 위해 <meta> 태그 스크래핑 
      try :
         tags = soup.select_one('meta[name="keywords"]')['content']
         if tags is not None:
            tags = tags.split(',')
            spanTag = list()
            for tag in tags:
               spanTag.append(f'<span class="copy_texts" onclick="copy_list(\'{tag}\')">{tag}</span>')
            tags_res = " / ".join(spanTag)
            self.tag_result_box.append(f'<span class="tag_title">제목</span> : {name.text} <br> <span class="tag_tag">태그</span> :  {tags_res}')
      except:
         print('\n<tag crwal unavailable product : passing>')

   def after_process(self):
      if self.check[1] == 'false': # 카테고리 검색시
         for cate in self.cat_result_box:
            if cate not in self.cat_result :
               self.cat_result.append(cate)

      if self.check[2] == 'false': #제목 검색시 중복 제거
         self.name_check()

      print(f'=>검색한 항목 수 : {self.num_of_content} ({len(self.name_result_box)})\n')

   def name_check(self):
      titleSets = set()
      resString = ''
      for i in tqdm(range(len(self.name_result_box)),total = len(self.name_result_box), ## 전체 진행수
               desc = '제목 중복 제거중 : ', ## 진행률 앞쪽 출력 문장
               ncols =80,): #제목 갯수 45개
         tempList = self.name_result_box[i].split() #제목 1개를 단어 별로 잘라서 리스트에 담는다.
         wordCnt = 0
         for j in range(len(tempList)): #단어 갯수
               if tempList[j] not in titleSets: #단어가 titleSets에 없다면
                  resString += tempList[j] + ' '
                  wordCnt += 1
         if wordCnt == 0:
               continue
         else:
               pass
         titleSets.update(self.name_result_box[i].split()) #titleSets 업데이트
         resString += '\n' 
      self.name_result = resString

   def make_json(self):
      return jsonify({'result': 'success','categories':self.cat_result,'name':self.name_result,'tag':self.tag_result_box})


class ChromeDriver:
   def __init__(self, url):
      self.event = threading.Event()
      self.driver = None
      self.done = False
      self.url = url
      chrome_options = Options()
      chrome_options.add_argument("--disable-extensions")
      chrome_options.add_argument("--disable-gpu")
      chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
      chrome_options.add_argument('--headless=new')
      chrome_options.add_argument('--no-sandbox')
      self.chrome_options = chrome_options

   def driver_get_soup(self,scroll,num_of_page,try_num):
      self.__driver_get(try_num)
      if self.done == True :
         return self.__get_soup_from_driver(num_of_page, scroll)
      else:
         return None

   def __driver_get(self,try_num):
      count = 1
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
            thread.join()
            break

   def __get_driver_t(self):
      driver = webdriver.Chrome(options=self.chrome_options)
      driver.set_page_load_timeout(7)
      try :
         driver.get(self.url)
         time.sleep(1)
         driver.refresh()
         self.driver = driver
         self.done = True
         self.event.set()
      except :
         driver.close()
         self.done = False
         self.event.set()
   
   def __get_soup_from_driver(self,num_of_page,scroll):
      driver = self.driver
      try :
         if(scroll):
            body = driver.find_element(By.TAG_NAME, "body")
            for i in tqdm(range(0,num_of_page),total = num_of_page, ## 전체 진행수
                     desc = '상품 정보 수집중 : ', ## 진행률 앞쪽 출력 문장
                     ncols =80,):
               body.send_keys(Keys.PAGE_DOWN)
               time.sleep(1)
         html = driver.page_source
         soup = BeautifulSoup(html, 'html.parser')
         driver.close()
         return soup
      except :
         return None
      

if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)
   