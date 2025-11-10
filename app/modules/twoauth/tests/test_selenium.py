import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def test_twoauth_and_check_form():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()

  
        driver.get(f"{host}/login")
        time.sleep(2)
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")
        password_field.send_keys(Keys.RETURN)
        time.sleep(3)

        try:
            driver.find_element(By.XPATH, "//h5[contains(., 'Verificación en dos pasos')]")
            print("Test passed!")
        except NoSuchElementException:
            raise AssertionError("Test failed!")
    finally:
        close_driver(driver)



test_twoauth_and_check_form()

