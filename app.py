from flask import Flask, render_template, jsonify, request

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time, random
from tqdm import tqdm

app = Flask(__name__)
headers = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

chrome_options = Options()
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
chrome_options.add_argument('--headless=new')

## HTML을 주는 부분
@app.route('/')
def home():
   return render_template('index.html')

## API 역할을 하는 부분
@app.route('/search', methods=['POST'])
def search_category():

   url = request.form['url']
   num_of_page = int(request.form['num_of_pages'])
   check = request.form.getlist('check[]')
   print(num_of_page, check)
   # if num_of_page != 0 : # beautifulsoup 네이버 막힘
   driver = webdriver.Chrome(options=chrome_options)

   driver.get(url)
   time.sleep(1)

   body = driver.find_element(By.TAG_NAME, "body")
   for i in tqdm(range(0,num_of_page),total = num_of_page, ## 전체 진행수
            desc = '상품 정보 수집중 : ', ## 진행률 앞쪽 출력 문장
            ncols =80,):
      body.send_keys(Keys.PAGE_DOWN)
      time.sleep(0.5)

      html = driver.page_source

      soup = BeautifulSoup(html, 'html.parser')
   # else :
   #    data = requests.get(url,headers=headers)
   #    soup = BeautifulSoup(data.text, 'html.parser')

   cat_result_box = list()
   name_result_box = list()
   tag_result = list()

   count = 0
   count = count + getInfo(soup,cat_result_box,name_result_box,tag_result,True,check)
   if check[0] == 'false': #광고 제외 아닐때
      count = count + getInfo(soup,cat_result_box,name_result_box,tag_result,False,check)
   if check[2] == 'false':
      name_result = nameCheck(name_result_box)
   else :
      name_result = ''

   cat_result = list()

   for cate in cat_result_box:
      if cate not in cat_result :
         cat_result.append(cate)

   if num_of_page != 0 :
      driver.close()
   print(f'=>검색한 항목 수 : {count} ({len(name_result_box)})\n')
   return jsonify({'result': 'success','categories':cat_result,'name':name_result,'tag':tag_result})

def getInfo(soup,cat_result_box,name_result_box,tag_result,noads,check):
   num_of_content = 0
   if noads:
      contents = list(soup.select('.product_item__MDtDF ')) #no광고
      desc_msg = '일반 상품 분석중 : '
   else :
      contents = list(soup.select('.adProduct_item__1zC9h')) #광고
      desc_msg = '광고 상품 분석중 : '
   for content in tqdm(contents,total = len(contents), ## 전체 진행수
              desc = desc_msg, ## 진행률 앞쪽 출력 문장
              ncols = 80,):
      if content is not None:
         num_of_content = num_of_content + 1
         if check[1] == 'false':
            if noads:
               cat_list = list(content.select('.product_category__l4FWz'))
            else:
               cat_list = list(content.select('.adProduct_category__ZIAfP'))
            cat_sum = ""
            for cat in cat_list:
               if cat == cat_list[-1]:
                  cat_sum += f'<span class="copy_texts" onclick="copy_list(\'{cat.text}\')">{cat.text}</span>'
               else:
                  cat_sum = cat_sum + f'<span class="copy_texts" onclick="copy_list(\'{cat.text}\')">{cat.text}</span> > '
            cat_result_box.append(cat_sum)
         if check[2] == 'false':
            if noads:
               name = content.select_one('.product_link__TrAac')
            else:
               name = content.select_one('.adProduct_link__NYTV9')
            name_sum = name.text.strip()
            name_result_box.append(name_sum)
         elif check[2] == 'true' and check[3] == 'false':
            if noads:
               name = content.select_one('.product_link__TrAac')
            else:
               name = content.select_one('.adProduct_link__NYTV9')

         if check[3] == 'false':
            try:
               if noads:
                  div_grade = content.select_one('.product_grade__IzyU3').text
               else:
                  div_grade = content.select_one('.adProduct_grade__C3wzo').text
            except:
               div_grade = ''
            if div_grade in ('파워', '빅파워', '프리미엄'):
                  # name_response = requests.get(name.attrs['href'],headers=headers)
                  time.sleep(random.uniform(0.2, 0.7))
                  # soup = BeautifulSoup(name_response.text, 'html.parser') # beautifulsoup 네이버 막힘
                  
                  driver2 = webdriver.Chrome(options=chrome_options)
   
                  driver2.get(name.attrs['href'])
                  time.sleep(1)

                  html = driver2.page_source

                  soup = BeautifulSoup(html, 'html.parser')
                  # print(soup)

                  # 태그 추출 위해 <meta> 태그 스크래핑 
                  try :
                     tags = soup.select_one('meta[name="keywords"]')['content']
                     if tags is not None:
                        tags = tags.split(',')
                        spanTag = list()
                        for tag in tags:
                           spanTag.append(f'<span class="copy_texts" onclick="copy_list(\'{tag}\')">{tag}</span>')
                        tags_res = " / ".join(spanTag)
                        tag_result.append(f'<span class="tag_title">제목</span> : {name.text} <br> <span class="tag_tag">태그</span> :  {tags_res}')
                  except:
                     print('\nnono\n')
                  time.sleep(random.uniform(0.3, 1))
   return num_of_content

def nameCheck(name_result_box):
   titleSets = set()
   resString = ''
   for i in tqdm(range(len(name_result_box)),total = len(name_result_box), ## 전체 진행수
              desc = '제목 중복 제거중 : ', ## 진행률 앞쪽 출력 문장
              ncols =80,): #제목 갯수 45개
        # print(i + 1, ': ', end=' ')
        tempList = name_result_box[i].split() #제목 1개를 단어 별로 잘라서 리스트에 담는다.
        wordCnt = 0
        for j in range(len(tempList)): #단어 갯수
            if tempList[j] not in titleSets: #단어가 titleSets에 없다면
                resString += tempList[j] + ' '
                wordCnt += 1
            # if tempList[j] in titleSets:
            #     for k in range(len(tempList[j])):
            #         print('*', end = ' ')
        if wordCnt == 0:
            continue
        else:
            pass
        titleSets.update(name_result_box[i].split()) #titleSets 업데이트
        resString += '\n' 
   return resString


if __name__ == '__main__':
   app.run('0.0.0.0',port=3000,debug=True)