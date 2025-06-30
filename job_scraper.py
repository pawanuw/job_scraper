from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import time
import pandas as pd

def load_inputs():
    with open("inputs.json", "r") as file:
        return json.load(file)

def login(driver, email, password):
    print("Starting login process...")
    
    try:
        # Try multiple selectors for email field
        email_selectors = [
            'session_key',
            'username',
            'login-email',
            'email'
        ]
        
        email_field = None
        for selector in email_selectors:
            try:
                email_field = driver.find_element(By.ID, selector)
                print(f"Found email field with ID: {selector}")
                break
            except:
                continue
        
        if not email_field:
            # Try by name attribute
            try:
                email_field = driver.find_element(By.NAME, 'session_key')
                print("Found email field by name")
            except:
                # Try by input type
                email_field = driver.find_element(By.CSS_SELECTOR, 'input[type="email"]')
                print("Found email field by type")
        
        email_field.clear()
        email_field.send_keys(email)
        print("Email entered")
        
        # Try multiple selectors for password field
        password_selectors = [
            'session_password',
            'password',
            'login-password'
        ]
        
        password_field = None
        for selector in password_selectors:
            try:
                password_field = driver.find_element(By.ID, selector)
                print(f"Found password field with ID: {selector}")
                break
            except:
                continue
        
        if not password_field:
            try:
                password_field = driver.find_element(By.NAME, 'session_password')
                print("Found password field by name")
            except:
                password_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
                print("Found password field by type")
        
        password_field.clear()
        password_field.send_keys(password)
        print("Password entered")
        
        # Try multiple selectors for submit button
        submit_selectors = [
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(text(), 'Sign in')]",
            "//button[contains(text(), 'Log in')]",
            ".btn-primary"
        ]
        
        submit_button = None
        for selector in submit_selectors:
            try:
                if selector.startswith("//"):
                    submit_button = driver.find_element(By.XPATH, selector)
                else:
                    submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"Found submit button with selector: {selector}")
                break
            except:
                continue
        
        if submit_button:
            submit_button.click()
            print("Login button clicked")
        else:
            print("Could not find submit button")
            raise Exception("Submit button not found")
        
        time.sleep(5)
        print("Login completed")
        
    except Exception as e:
        print(f"Login failed: {e}")
        print(f"Current page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        raise

def extract_job_details(driver):
    print("Extracting job details...")
    
    # Try different selectors for job cards
    job_card_selectors = [
        ".job-card-container",
        ".jobs-search-results__list-item",
        ".job-card-list",
        "[data-testid='job-card']",
        ".jobs-search-results-list__item"
    ]
    
    job_details = []
    
    for card_selector in job_card_selectors:
        try:
            job_cards = driver.find_elements(By.CSS_SELECTOR, card_selector)
            if job_cards:
                print(f"Found {len(job_cards)} job cards using selector: {card_selector}")
                
                for card in job_cards:
                    try:
                        job_info = extract_single_job_details(card)
                        if job_info and job_info['title']:  # Only add if we found a title
                            job_details.append(job_info)
                    except Exception as e:
                        print(f"Error extracting from individual card: {e}")
                        continue
                break
        except Exception as e:
            print(f"Error with card selector {card_selector}: {e}")
            continue
    
    if not job_details:
        print("No job details found. Trying to get page source length...")
        print(f"Page source length: {len(driver.page_source)}")
    else:
        print(f"Successfully extracted {len(job_details)} job listings")
    
    return job_details

def extract_single_job_details(job_card):
    """Extract details from a single job card"""
    job_info = {
        'title': '',
        'company': '',
        'location': '',
        'date_posted': ''
    }
    
    # Extract job title
    title_selectors = [
        ".job-card-list__title",
        "h3 a",
        ".job-card-container__link",
        "h3.job-card-list__title",
        "[data-testid='job-title']",
        ".job-card-list__title-link",
        "h3",
        "a[data-control-name='job_search_job_title']"
    ]
    
    for selector in title_selectors:
        try:
            title_element = job_card.find_element(By.CSS_SELECTOR, selector)
            job_info['title'] = title_element.text.strip()
            if job_info['title']:
                break
        except:
            continue
    
    # Extract company name
    company_selectors = [
        ".job-card-container__primary-description",
        ".job-card-list__company-name",
        "h4 a",
        ".job-card-container__company-name",
        "[data-testid='job-company']",
        "h4",
        "a[data-control-name='job_search_company_name']",
        ".artdeco-entity-lockup__subtitle"
    ]
    
    for selector in company_selectors:
        try:
            company_element = job_card.find_element(By.CSS_SELECTOR, selector)
            job_info['company'] = company_element.text.strip()
            if job_info['company']:
                break
        except:
            continue
    
    # Extract location
    location_selectors = [
        ".job-card-container__metadata-item",
        ".job-card-list__location",
        "[data-testid='job-location']",
        ".artdeco-entity-lockup__caption",
        ".job-card-container__metadata-wrapper span"
    ]
    
    for selector in location_selectors:
        try:
            location_elements = job_card.find_elements(By.CSS_SELECTOR, selector)
            for element in location_elements:
                text = element.text.strip()
                # Check if this looks like a location (contains common location indicators)
                if text and any(indicator in text.lower() for indicator in [
                    'remote', 'hybrid', 'on-site', 'city', 'state', 'country', ','
                ]) or len(text.split()) <= 4:  # Locations are usually short
                    job_info['location'] = text
                    break
            if job_info['location']:
                break
        except:
            continue
    
    # Extract date posted
    date_selectors = [
        ".job-card-list__footer-wrapper time",
        "time",
        ".job-card-container__footer-item time",
        "[data-testid='job-date']",
        ".job-card-list__footer time"
    ]
    
    for selector in date_selectors:
        try:
            date_element = job_card.find_element(By.CSS_SELECTOR, selector)
            # Try to get datetime attribute first, then text
            date_posted = date_element.get_attribute('datetime') or date_element.text.strip()
            if date_posted:
                job_info['date_posted'] = date_posted
                break
        except:
            continue
    
    # If no specific date found, look for text patterns
    if not job_info['date_posted']:
        try:
            card_text = job_card.text
            date_patterns = ['ago', 'day', 'week', 'month', 'hour', 'minute']
            lines = card_text.split('\n')
            for line in lines:
                if any(pattern in line.lower() for pattern in date_patterns):
                    job_info['date_posted'] = line.strip()
                    break
        except:
            pass
    
    return job_info

def save_to_csv(job_details, job_search_term):
    if job_details:
        df = pd.DataFrame(job_details)
        # Reorder columns
        df = df[['title', 'company', 'location', 'date_posted']]
        # Rename columns for better readability
        df.columns = ['Job Title', 'Company', 'Location', 'Date Posted']
        
        filename = f"job_details_{job_search_term.replace(' ', '_')}.csv"
        df.to_csv(filename, index=False)
        print(f"Scraped {len(job_details)} job listings and saved to {filename}")
        
        # Print summary
        print("\nSummary of extracted data:")
        print(f"Total jobs: {len(job_details)}")
        print(f"Jobs with titles: {sum(1 for job in job_details if job['title'])}")
        print(f"Jobs with companies: {sum(1 for job in job_details if job['company'])}")
        print(f"Jobs with locations: {sum(1 for job in job_details if job['location'])}")
        print(f"Jobs with dates: {sum(1 for job in job_details if job['date_posted'])}")
    else:
        print("No job details found")

def main():
    print("Starting job scraper...")
    
    inputs = load_inputs()
    email = inputs["email"]
    password = inputs["password"]
    job_title = inputs["jobTitle"]
    
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print(f"Navigating to LinkedIn login...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(3)
        
        # Debug: Print available input elements
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"Found {len(inputs)} input elements:")
        for i, inp in enumerate(inputs):
            print(f"  Input {i}: id='{inp.get_attribute('id')}', name='{inp.get_attribute('name')}', type='{inp.get_attribute('type')}'")
        
        login(driver, email, password)
        
        print(f"Navigating to jobs search for: {job_title}")
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title.replace(' ', '%20')}"
        driver.get(search_url)
        time.sleep(8)
        
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        job_details = extract_job_details(driver)
        save_to_csv(job_details, job_title)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Current URL when error occurred: {driver.current_url}")
    finally:
        driver.quit()
        print("Browser closed")

if __name__ == "__main__":
    main()