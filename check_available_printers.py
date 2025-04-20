# Replace with user-defined threshold
MATERIAL_THRESHOLD = 0.5

# Replace with recipient email address
EMAIL_TO = "jc750@duke.edu"

# Printers to exclude
# If you want to exclude more than one type of printers, do something like this instead:
# exclude = "Wilson|TEC B-11"
exclude = "Wilson" # Exclude all Wilson printers

# Check interval in seconds
CHECK_INTERVAL = 300  # Check printer availability every 5 minutes

# Import modules
import time

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import pandas

# User credentials
USERNAME = "baughlab-globus"
PASSWORD = "3fBoHubxkYxTWeXLtFhkUWso"
LOGIN_URL = "https://duke.3dprinteros.com/#/projects"  # Replace with the actual login page

# Email settings
EMAIL_FROM = "printer.notif@zohomail.com"
EMAIL_PASSWORD = "_N5mM8WqaBL29Fx"
EMAIL_SUBJECT = "3D Printer Availability Notification"
SMTP_SERVER = "smtp.zoho.com"
SMTP_PORT = 587

while True:
    # Open Chrome WebDriver silently
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(chrome_options)
    
    # 1. Log in to the website
    driver.get(LOGIN_URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "j_username")))

    driver.find_element(By.ID, "j_username").send_keys(USERNAME)
    driver.find_element(By.ID, "j_password").send_keys(PASSWORD, Keys.RETURN)
    
    # 2. Click "Projects"
    driver.find_element(By.XPATH, '//*[@id="app"]/div/div[1]/section/div/section/div[1]/div[1]/button[2]').click()
    
    # 3. Use explicit waits to ensure the "Print" button is visible or clickable before interacting
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#__BVID__158__BV_button_"))).click()
    
    # 4. Find all printers whose status is idle, excluding maintenance (idle)
    time.sleep(10) # wait for all printers to load
    idle_printers = driver.find_elements(By.CSS_SELECTOR, ".printer-badge-medium.bg-green:not(.bg-maintenance)")
    
    # Set up metrics you want to retrieve
    cols = ['PrinterName', 'Material']
    lst = []

    # Loop through idle printers
    for printer in idle_printers:
        # Get printer name
        parent_element = printer.find_element(By.XPATH, './..')
        printer_name = parent_element.find_element(By.CLASS_NAME, 'ml-3').find_element(By.CLASS_NAME, 'printer-details-title')
    
        # Get row id
        row_attributes = driver.execute_script('var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;', parent_element.find_element(By.XPATH, './../../..'))
        row_id = row_attributes['id']
    
        # Get printer's remaining materal (in gram)
        grams = driver.find_element(By.XPATH, f'//*[@id="{row_id}"]/td[3]/p/div[1]/div[2]').text.split('g')[0]
    
        # Get queue time
        queue_time = driver.find_element(By.XPATH, f'//*[@id="{row_id}"]/td[2]/span')
    
        if len(queue_time.text) == 0:
            lst.append([printer_name.text, grams]) # Exclude printers that require a queue time

    df = pandas.DataFrame(lst, columns = cols) 
    
    # Exclude some printers
    df = df[~df.PrinterName.str.contains(exclude)] # Tilde(~) sign works as a NOT(!) operator
    
    # Keep printers that pass the material threshold
    df.Material = pandas.to_numeric(df.Material)
    df = df[df.Material > MATERIAL_THRESHOLD]
    
    printer_found = False
    
    if df.shape[0] > 0:
        printer_found = True
        
        # Send email
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        msg["Subject"] = EMAIL_SUBJECT
    
        # Get all available printer names in one string
        available_printers = ' and '.join(df.PrinterName)

        body = f"Available 3D Printer(s) with at least {MATERIAL_THRESHOLD} grams of material:\n{available_printers}"
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        server.quit()
        print("Notification email sent successfully.")
        
        break
    else:
        print("No available printers met the criteria. Retrying in 5 minutes.")

    driver.quit()
    if not printer_found:
        time.sleep(CHECK_INTERVAL)




