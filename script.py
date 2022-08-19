
from genericpath import isdir
import os
import json
import yaml
from time import sleep
from haralyzer import HarParser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

NETWORK_COMMUNICATION_EXPORT = 'api-communication.har'
TASK_EXPORTS_DIRECTORY = 'task-exports'
TASK_BASE_URL = 'https://app.clickup.com/t/'

CLICKUP_LOGIN_URL = 'https://app.clickup.com/login'

with open('config.yml', 'r') as configFile:
    config = yaml.load(configFile, Loader=yaml.Loader)
    EMAIL = config['email']
    PASSWORD = config['password']

if not os.path.exists(TASK_EXPORTS_DIRECTORY):
        os.mkdir(TASK_EXPORTS_DIRECTORY)

# Get task IDs

taskIds = set()
taskIdSubcategoryMap = {}
NETWORK_COMMUNICATION_EXPORT = 'api-communication.har'
with open(NETWORK_COMMUNICATION_EXPORT, 'r') as networkFile:
    harParser = HarParser(json.loads(networkFile.read()))
    for entry in harParser.har_data['entries']:
        requestUrl = entry['request']['url']
        responseStatus = entry['response']['status']
        if requestUrl == "https://app.clickup.com/tasks/v2/task" and responseStatus == 200:
            tasks = json.loads(entry['response']['content']['text'])
            for task in tasks['tasks']:
                taskId = task['id']
                taskIds.add(taskId)
                subcategoryName = task['subcategory']['name']
                if taskId in taskIdSubcategoryMap.keys() and taskIdSubcategoryMap[taskId] != subcategoryName:
                    print('Warning: task {} has differing subcategories; using {}'.format(taskId, subcategoryName))
                taskIdSubcategoryMap[taskId] = subcategoryName

# Get progress data from previous runs

def getTaskIdFromFileName(fileName):
    taskId = fileName.split('_ #')[1].replace('.pdf', '')
    return taskId

processedTasks = set()
for _, _, files in os.walk(TASK_EXPORTS_DIRECTORY):
    for fileName in files:
        if fileName.endswith('.pdf'):
            taskId = getTaskIdFromFileName(fileName)
            processedTasks.add(taskId)

if len(taskIds) != len(processedTasks):

    # Get and configure chromedriver

    options = webdriver.ChromeOptions()
    settings = {
           "recentDestinations": [{
                "id": "Save as PDF",
                "origin": "local",
                "account": "",
            }],
            "selectedDestinationId": "Save as PDF",
            "version": 2
        }
    prefs = {
        'printing.print_preview_sticky_settings.appState': json.dumps(settings),
        'savefile.default_directory': os.path.join(os.getcwd(), TASK_EXPORTS_DIRECTORY)
    }
    options.add_experimental_option('prefs', prefs)
    options.add_argument('--kiosk-printing')
    driver = webdriver.Chrome(options=options)

    # Login

    driver.get(CLICKUP_LOGIN_URL)
    driver.maximize_window()
    driver.find_element(By.ID, 'login-email-input').send_keys(EMAIL)
    driver.find_element(By.ID, 'login-password-input').send_keys(PASSWORD)
    driver.find_element(By.CLASS_NAME, 'login-page-new__main-form-button').click()
    try:
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, 'cu-dashboard-table__body'))
        )
    except:
        raise('Could not login')

    # Save tasks

    for taskId in taskIds.difference(processedTasks):
        print('Saving task ' + taskId)
        driver.get(TASK_BASE_URL + taskId)
        try:
            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located((By.CLASS_NAME, 'task__body'))
            )
        except:
            print('ERROR')
            continue
        elements = driver.find_elements(By.CLASS_NAME, 'cu-task-editor__show-more-btn')
        for element in elements:
            element.click()
        sleep(5)
        driver.execute_script('window.print();')
        sleep(10)
        processedTasks.add(taskId)
    
    driver.quit()

# Categorize tasks (by boards)

for fileName in os.listdir(TASK_EXPORTS_DIRECTORY):
    if fileName.endswith('.pdf'):
        taskId = getTaskIdFromFileName(fileName)
        category = taskIdSubcategoryMap[taskId]
        categoryDirectoryPath = os.path.join(TASK_EXPORTS_DIRECTORY, category)
        if not os.path.exists(categoryDirectoryPath):
            os.mkdir(categoryDirectoryPath)
        originPath = os.path.join(TASK_EXPORTS_DIRECTORY, fileName)
        destinationPath = os.path.join(categoryDirectoryPath, fileName)
        os.rename(originPath, destinationPath)

print('Processed {} tasks in {} categories'.format(
    len(processedTasks), len(set(taskIdSubcategoryMap.values()))))
for fileName in os.listdir(TASK_EXPORTS_DIRECTORY):
    filePath = os.path.join(TASK_EXPORTS_DIRECTORY, fileName)
    if os.path.isdir(filePath):
        print('  {}: {} tasks'.format(
            fileName,
            len(os.listdir(filePath))
        ))