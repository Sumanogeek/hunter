import time
import json
from bs4 import BeautifulSoup
from datetime import datetime
import yaml
import re
import os, sys
from pymongo import MongoClient
from getpass import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import selenium.webdriver.support.ui as ui
from selenium.common.exceptions import TimeoutException
from pyvirtualdisplay import Display

restart_pg = 0  # <--- set the restart page
stop_pg = 25    # <--- set the stop page

# dev_run = False; prod_run = True  # <--- uncomment for Prod Run
dev_run = True ; prod_run = False   # <--- uncomment for Dev Run

time_stamp = datetime.now()
sysout_File = "output/logs" + str(time_stamp) + ".txt"
error_File = "output/error" + str(time_stamp) + ".txt"
result_File = "output/result" + str(time_stamp) + ".txt"

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open(sysout_File, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass    

def connect_DB():
    print ("connect_DB")

    global huntCol

    try:
        with open('config.yml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            DBuser = config["DBuser"]
            DBpass = config["DBpass"]
    except FileNotFoundError:
        DBuser = input("Enter MongoDB User Id: ")
        DBpass = getpass(prompt='Enter MongoDB password: ')
        config = {}
        config["DBuser"] = DBuser
        config["DBpass"] = DBpass
        with open('config.yml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
    #MONGODB_URL = "mongodb+srv://{0}:{1}@clusterar3-dgymc.mongodb.net/test?retryWrites=true&w=majority".format(DBuser, DBpass)
    MONGODB_URL = "mongodb+srv://{0}:{1}@clusterhunt-9868q.mongodb.net/test?retryWrites=true&w=majority".format(DBuser, DBpass)
    client = MongoClient(MONGODB_URL)
    huntDB = client["hunt"]
    huntCol = huntDB["jobs"]

    return

def get_job_links():
    print ("get_job_links")

    soup_level0=BeautifulSoup(browser.page_source, 'html5lib')
    links = soup_level0.findAll('a', {'id':'jdUrl'})
    link_list = []

    for item in links:
        #print ("item: ", item)
        job_id = item.find_parent('div')['id']
        link_list.append([job_id,item['href']])

    return link_list

def scrape_link(page_source, link):
    print ("scrape_link")

    with open('template.yml', 'r') as f:
        template = yaml.load(f, Loader=yaml.FullLoader)

    rec = {}
    skillSum = []
    soup_level1=BeautifulSoup(page_source, 'html5lib')
    
    rec["job_id"] = link[0]
    rec["link"] = link[1]
    rec["search_category"] = 9
    rec["timestamp"] = datetime.now()

    uniqueFlag = True
    if (soup_level1.find('div', attrs = {'class':'leftSec'})):
        rec["type"] = "regular"
        index = 0
        soup_level2=soup_level1.find('div', attrs = {'class':'leftSec'}) 
    elif (soup_level1.find('div', attrs = {'class':'flex_column'})):
        rec["type"] = "av-special"
        index = 1
        soup_level2=soup_level1.find('div', attrs = {'class':'flex_column'}) 
    elif (soup_level1.find('div', attrs = {'id':'jdDiv'})):
        uniqueFlag = False
        rec["type"] = "id->jdDiv"
        index = 2
        soup_level2=soup_level1.find('div', attrs = {'id':'jdDiv'})
        rec["title"] = soup_level2.find('h1').text
        rec["company"] = soup_level2.find('h4', {'class':'jobCompanyProfileHeading'}).findNext().text
        jobAttr = soup_level2.find('div', {'class':'f14'}).findAll('p')
        rec["experience"] = jobAttr[0].text
        rec["salary"] = jobAttr[2].text
        rec["location"] = jobAttr[1].text
        rec["job_description"] = soup_level2.find('div', {'class':'disc-li'}).text
        skills = soup_level2.find('div', {'class':'skills-section'}).findAll('a')
        for skill in skills:
            skillSum.append(skill.text)
        rec["key_skill"] = skillSum
    else:
        print ("new template: ", link)
 
    if uniqueFlag:
        rec["title"] = soup_level2.find(template[index]["title"][0], attrs = {template[index]["title"][1]:template[index]["title"][2]}).text
        rec["company"] = soup_level2.find(template[index]["company"][0], attrs = {template[index]["company"][1]:template[index]["company"][2]}).text
        rec["experience"] = soup_level2.find(template[index]["experience"][0], attrs = {template[index]["experience"][1]:template[index]["experience"][2]}).text
        rec["salary"] = soup_level2.find(template[index]["salary"][0], attrs = {template[index]["salary"][1]:template[index]["salary"][2]}).text
        rec["location"] = soup_level2.find(template[index]["location"][0], attrs = {template[index]["location"][1]:template[index]["location"][2]}).text
        rec["stats"] = soup_level2.find(template[index]["stats"][0], attrs = {template[index]["stats"][1]:template[index]["stats"][2]}).text
        rec["job_description"] = soup_level2.find(template[index]["job_description"][0], attrs = {template[index]["job_description"][1]:template[index]["job_description"][2]}).text
        skills = soup_level2.find(template[index]["key_skill"][0], attrs = {template[index]["key_skill"][1]:template[index]["key_skill"][2]}).findAll('a')
        for skill in skills:
            skillSum.append(skill.text)
        rec["key_skill"] = skillSum
                
    return rec

def click_links(link_list):
    print ("click_links")

    pg_master = []
    pg_error = []
    count = 0
    for link in link_list:
        count += 1
        print ("count {0} - link {1}".format(count, link))
        browser.get(link[1])
        time.sleep(1)
        try:
            rec = scrape_link(browser.page_source, link)
            pg_master.append(rec)
        except:
            pg_error.append(link)
            print ("Write an error: ", link)
        browser.execute_script("window.history.go(-1)")
        time.sleep(1)

        # if count > 2 and dev_run:   # <-- To be removed for production run
        #     break                   # <-- To be removed for production run

    return pg_master, pg_error

def main():
    print ("main")

    global browser

    path = r'/Users/sumanbalu/chromeDrive/chromedriver'
    if prod_run:
        path = r'/usr/bin/chromedriver'                # <--- uncomment for production
        display = Display(visible=0, size=(800, 800))  # <--- uncomment for production
        display.start()                                # <--- uncomment for production
    browser = webdriver.Chrome(executable_path = path)

    browser.get('https://www.naukri.com/')

    time.sleep(60)

    browser.find_element_by_xpath('/html/body/div[4]/div[3]/div[1]/div[1]/span[2]').click()

    browser.find_element_by_xpath('/html/body/div[4]/div[3]/div[3]/div[1]/form/div[2]/a').click()

    time.sleep(3)
    browser.execute_script("document.getElementById('dd_adv_workExp_yearHid').value='9'")
    browser.execute_script("document.getElementById('hid_ddAdvIndusrty').value='[\"25\"]'")
    browser.execute_script("document.getElementById('dd_adv_jobCategoryHid').value='24'")

    browser.find_element_by_xpath('/html/body/div[10]/div[3]/div[3]/form/div[8]/div[2]/div/div[2]/a').click()
    browser.find_element_by_xpath('/html/body/div[10]/div[3]/div[3]/form/div[9]/button').click()

    time.sleep(2)
    browser.execute_script("document.getElementById('#2').click()")

    time.sleep(2)

    master =[]
    error = []
    finished = False

    breaker = 0
    while not finished:

        breaker += 1    
        print ("breaker: {0}, restart:{1}, stop:{2} ".format(breaker, restart_pg, stop_pg))  
        if breaker >= restart_pg and breaker <= stop_pg:

            # if breaker > 2 and dev_run:   # <-- To be removed for production run
            #     break                     # <-- To be removed for production run

            link_list = get_job_links()
            #print ("link_list: ", link_list)

            pg_master, pg_error  =  click_links(link_list)

            inserts = 0
            updates = 0
            for item in pg_master:
                print ("item[link]: ", item["link"])
                #writeDB = huntCol.update_one({"job_id":item["job_id"]},{'$set':item},upsert=True)
                response = huntCol.update_one({"job_id":item["job_id"]},{'$set':item},upsert=True)
                print ("Update: ", response._UpdateResult__raw_result["updatedExisting"])
                if response._UpdateResult__raw_result["updatedExisting"] == False:
                    inserts += 1
                else:
                    updates += 1

            if dev_run or prod_run:
                with open(result_File, "a") as f: 
                    for item in pg_master:
                        f.write("%s\n" % item)  

                with open(error_File, "a") as f: 
                    for item in pg_error:
                        f.write("%s\n" % item)     

            # master.extend(pg_master)
            # error.extend(pg_error)
            print ("updates: {0}, inserts{1}".format(updates, inserts))
            if inserts == 0:
                print ("Breaking due to all duplicate links")
                break
            elif updates/inserts >= 9  :
                print ("Breaking due to many duplicate links")
                break

        time.sleep(2)

        sys.stdout.flush()

        navigate = browser.find_elements_by_class_name("grayBtn")
        
        if len(navigate) == 1:
            if navigate[0].get_attribute("innerText") == "Next":
                browser.execute_script("document.querySelector('button.grayBtn').click()")
            else:
                finished = True
        else:
            browser.execute_script("document.querySelectorAll('button.grayBtn')[1].click()")

    browser.quit()

    return master, error
    
if __name__ == "__main__":

    sys.stdout = Logger()

    connect_DB()

    # sys.stdout = open(sysout_File, 'w')

    print (" *** Start *** ", )
    master, error = main()

    # path = r'/Users/sumanbalu/chromeDrive/chromedriver'
    # browser = webdriver.Chrome(executable_path = path)
    # link_list = [
    #     'https://www.naukri.com/job-listings-Java-J2Ee-Developer-CTC-upto-18lpa-G9-Bengaluru-5-to-10-years-261219011779?src=cluster&sid=15780499725199&xp=2&px=1',
    #     'https://www.naukri.com/job-listings-HSBC-Hiring-Senior-Business-Consultant-payments-Domain-HSBC-electronic-data-processing-india-pvt-ltd-Bengaluru-Hyderabad-9-to-14-years-030120007509?src=jobsearchDesk&sid=15780609552133&xp=21&px=4',
    #     'https://www.naukri.com/job-listings-Senior-Front-end-Web-Developer-Liventus-Inc-Bengaluru-7-to-10-years-290319007660?src=cluster&sid=15780452651755&xp=1&px=1'
    #     ]
    # master, error  =  click_links(link_list)
    # browser.quit()

    #print ("master: ", master)
    #writeDB = huntCol.insert_many(master)
    
    # for item in master:
    #     print ("item[link]: ", item["link"])
    #     writeDB = huntCol.update_one({"job_id":item["job_id"]},{'$set':item},upsert=True)

    # if dev_run or prod_run:
    #     with open(result_File, "w") as f: 
    #         for item in master:
    #             f.write("%s\n" % item)  

    #     with open(error_File, "w") as f: 
    #         for item in error:
    #             f.write("%s\n" % item)     

    print (" *** End *** ")