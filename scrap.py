import time
import json
from bs4 import BeautifulSoup
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import selenium.webdriver.support.ui as ui
from selenium.common.exceptions import TimeoutException

def get_job_links():
    print ("get_job_links")

    links = browser.find_elements_by_id('jdUrl')
    link_list = []

    for item in links:
        link_list.append(item.get_attribute('href'))

    return link_list

def click_links(link_list):
    print ("click_links")

    count = 0
    for link in link_list:
        count += 1
        print ("count {0} - link {1}".format(count, link))
        browser.get(link)
        time.sleep(1)
        browser.execute_script("window.history.go(-1)")
        time.sleep(1)
        if count > 1 :   # <-- To be removed for production run
            break

    return

def main():
    print ("main")

    global browser

    path = r'/Users/sumanbalu/chromeDrive/chromedriver'
    browser = webdriver.Chrome(executable_path = path)

    browser.get('https://www.naukri.com/')

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

    finished = False

    breaker = 0
    while not finished:

        breaker += 1
        if breaker > 1:   # <-- To be removed for production run
            break

        link_list = get_job_links()

        click_links(link_list)
            
        time.sleep(2)

        navigate = browser.find_elements_by_class_name("grayBtn")
        
        if len(navigate) == 1:
            if navigate[0].get_attribute("innerText") == "Next":
                browser.execute_script("document.querySelector('button.grayBtn').click()")
            else:
                finished = True
        else:
            browser.execute_script("document.querySelectorAll('button.grayBtn')[1].click()")

    #browser.close()
    browser.quit()
    
if __name__ == "__main__":

    print (" *** Start *** ", )
    main()
    print (" *** End *** ")
