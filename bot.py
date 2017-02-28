import telegram
import configparser
from selenium import webdriver
#from pyvirtualdisplay import Display


kaist_url = 'https://cs.kaist.ac.kr/board/list?menu=175&bbs_id=recruit'
snu_url = 'http://cse.snu.ac.kr/department-notices?c%5B%5D=40&keys='

def set_config():
    try:
        global config
        config = configparser.ConfigParser()
        config.read('config.ini')
    except Exception as e:
        print('이 파일과 같은 위치에 config.ini파일을 위치시켜주세요.')
        raise e

    try:
        global my_token, kaist_latest_num, snu_latest_num, chrome_driver_directory
        my_token = config.get('setting','token')
        kaist_latest_num = config.get('setting','kaist_latest_num')
        snu_latest_num = config.get('setting','snu_latest_num')
        chrome_driver_directory = config.get('setting','chrome_driver_directory')
        
    except Exception as e:
        print('setting.ini 인자설정을 다시해주세요.')
        raise e

def get_latest_posts_kaist(kaist_latest_num):
    """
    역할 : 카이스트 취업정보 게시판을 조회하여 새로 생긴 게시물의 제목을 수집하여 리트스로 반환
    input : 직전에 크롤링했을 때 가장 최신 게시물의 게시물 번호
    output : input으로 들어온 게시물 번호보다 최신 게시물들의 제목을 리스트형태로 반환
    """
    chrome_driver = webdriver.Chrome(chrome_driver_directory)
    chrome_driver.get(kaist_url)
    chrome_driver.implicitly_wait(10)

    board = chrome_driver.find_element_by_class_name('bbs_no_border')
    posts_row = board.find_elements_by_xpath('./tbody/tr')

    latest_list = []
    latest_flag = False
    latest_num = kaist_latest_num
    for index, post_row in enumerate(posts_row): # 게시물마다 제목을 수집하여 리스트에 append시킴
        if index == 0: # 공지게시글이 항상 처음으로 나타남(이 게시물은 필요없음)
            continue
        try:
            post_num = int(post_row.find_element_by_xpath('./td[1]').text)
        except:
            print('게시물형태가 이상함')
            continue
        if kaist_latest_num == post_num :
            break
        elif latest_flag == False: # 가장 최근게시물 번호 저장(플래그 사용)
            latest_num = post_num
            latest_flag = True

        post_title = post_row.find_element_by_xpath('./td[2]').text
        latest_list.append(post_title)

    chrome_driver.close()
    return latest_list, str(latest_num)


def get_latest_posts_snu(snu_latest_num):
    """
    역할 : 서울대 취업정보 게시판을 조회하여 새로 생긴 게시물의 제목을 수집하여 리스트로 반환
    input : 직전에 크롤링했을 때 가장 최신 게시물의 게시물 제목(서울대 게시판은 번호가 없음)
    output : input으로 들어온 게시물 번호보다 최신 게시물들의 제목을 리스트형태로 반환
    """
    chrome_driver = webdriver.Chrome(chrome_driver_directory)
    chrome_driver.get(snu_url)
    chrome_driver.implicitly_wait(10)   
    
    posts_row = chrome_driver.find_elements_by_css_selector('td.views-field.views-field-title')

    latest_posts = []
    latest_flag = False
    latest_title = snu_latest_num
    for index, post in enumerate(posts_row):

        if index == 0:
            continue

        if snu_latest_num == post.text:
            break
        elif latest_flag == False:
            latest_title = post.text
            latest_flag = True
        latest_posts.append(post.text)

    chrome_driver.close()
    return latest_posts, latest_title


def send_message(my_token, latest_posts, friends_list, school):
    """
    역할 : 게시물 제목 리스트를 입력으로 받아 텔레그램으로 메세지 전송
    input
        - my_token : Telegram bot을 식별하는 토큰
        - latest_posts : 게시물 제목이 들어있는 리트스
        - school : 카이스트,서울대 각각 보내는 메세지 형태가 다르기 때문에 구별하는 인자
    output : 리턴값은 없음. 메세지 전송
    """
    bot = telegram.Bot(token = my_token)
    if school == 'kaist':
        for friend in friends_list:
            if len(latest_posts) == 0:
                bot.sendMessage(chat_id=friend, text='[KAIST]\n새로올라온 게시글이 없습니다.')
            else :
                for post in latest_posts:
                    bot.sendMessage(chat_id=friend, text='[KAIST]\n' + post + '\n' +\
                    'https://cs.kaist.ac.kr/board/list?menu=175&bbs_id=recruit')
    elif school == 'snu':
        for friend in friends_list:
            if len(latest_posts) == 0:
                bot.sendMessage(chat_id=friend, text='[SNU]\n새로올라온 게시글이 없습니다.')
            else:
                for post in latest_posts:
                    bot.sendMessage(chat_id=friend, text='[SNU]\n' + post + '\n' +\
                    'http://cse.snu.ac.kr/department-notices?c%5B%5D=40&c%5B%5D=107&keys=')

def get_friends_list(my_token):
    chat_id_list = []
    chat_id_file = open("chat_id_list.txt","r")
    for chat_id in chat_id_file:
        chat_id_list.append(chat_id)
    bot = telegram.Bot(token = my_token)
    updates = bot.getUpdates()
    for update in updates:
        chat_id_list.append(update.message['chat']['id'])
    chat_id_file.close()
    return set(chat_id_list)

def set_friends_list(chat_id_list):
    try:
        chat_id_file = open("chat_id_list.txt","w")
        for chat_id in chat_id_list:
            chat_id_file.write(str(chat_id)+"\n")
        chat_id_file.close()
    except Exception as e:
        raise e
    return True

def main():
    set_config() # 설정파일 읽기

#    display = Display(visible=0, size=(800,600))
#    display.start()

    friends_list = get_friends_list(my_token)
    snu_latest_posts, snu_latest = get_latest_posts_snu(snu_latest_num) # 서울대학교 게시판 업데이트
    kaist_latest_posts, kaist_latest = get_latest_posts_kaist(int(kaist_latest_num)) # 카이스트 게시판 업데이트
    send_message(my_token, kaist_latest_posts, friends_list, 'kaist') # 업데이트된 카이스트 게시물 메시지 전송
    send_message(my_token, snu_latest_posts, friends_list, 'snu') # 업데이트된 서울대 게시물 전송

    # 가장 최신글을 저장하여 다음 크롤링시 사용(최신게시물만 크롤링하기위한 기준)
    config.set('setting', 'snu_latest_num', str(snu_latest))
    config.set('setting','kaist_latest_num', str(kaist_latest))
    with open('config.ini','w') as configfile:
        config.write(configfile) # config파일에 저장

    set_friends_list(friends_list) 
#    display.stop()

if __name__ == '__main__':
    main()
