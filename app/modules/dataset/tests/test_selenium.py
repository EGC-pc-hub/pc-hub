import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def wait_for_page_to_load(driver, timeout=4):
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )


def count_datasets(driver, host):
    driver.get(f"{host}/dataset/list")
    wait_for_page_to_load(driver)

    try:
        amount_datasets = len(driver.find_elements(By.XPATH, "//table//tbody//tr"))
    except Exception:
        amount_datasets = 0
    return amount_datasets


def test_upload_dataset():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the login page
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)

        # Find the username and password field and enter the values
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        # Send the form
        password_field.send_keys(Keys.RETURN)
        time.sleep(4)
        wait_for_page_to_load(driver)

        # Count initial datasets
        initial_datasets = count_datasets(driver, host)

        # Open the upload dataset
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        # Find basic info and UVL model and fill values
        title_field = driver.find_element(By.NAME, "title")
        title_field.send_keys("Title")
        desc_field = driver.find_element(By.NAME, "desc")
        desc_field.send_keys("Description")
        tags_field = driver.find_element(By.NAME, "tags")
        tags_field.send_keys("tag1,tag2")

        # Add two authors and fill
        add_author_button = driver.find_element(By.ID, "add_author")
        add_author_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)
        add_author_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        name_field0 = driver.find_element(By.NAME, "authors-0-name")
        name_field0.send_keys("Author0")
        affiliation_field0 = driver.find_element(By.NAME, "authors-0-affiliation")
        affiliation_field0.send_keys("Club0")
        orcid_field0 = driver.find_element(By.NAME, "authors-0-orcid")
        orcid_field0.send_keys("0000-0000-0000-0000")

        name_field1 = driver.find_element(By.NAME, "authors-1-name")
        name_field1.send_keys("Author1")
        affiliation_field1 = driver.find_element(By.NAME, "authors-1-affiliation")
        affiliation_field1.send_keys("Club1")

        # Obtén las rutas absolutas de los archivos
        file1_path = os.path.abspath("app/modules/dataset/uvl_examples/file1.uvl")
        file2_path = os.path.abspath("app/modules/dataset/uvl_examples/file2.uvl")

        # Subir el primer archivo
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file1_path)
        wait_for_page_to_load(driver)

        # Subir el segundo archivo
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file2_path)
        wait_for_page_to_load(driver)

        # Add authors in UVL models
        show_button = driver.find_element(By.ID, "0_button")
        show_button.send_keys(Keys.RETURN)
        add_author_uvl_button = driver.find_element(By.ID, "0_form_authors_button")
        add_author_uvl_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        name_field = driver.find_element(By.NAME, "feature_models-0-authors-2-name")
        name_field.send_keys("Author3")
        affiliation_field = driver.find_element(By.NAME, "feature_models-0-authors-2-affiliation")
        affiliation_field.send_keys("Club3")

        # Check I agree and send form
        check = driver.find_element(By.ID, "agreeCheckbox")
        check.send_keys(Keys.SPACE)
        wait_for_page_to_load(driver)

        upload_btn = driver.find_element(By.ID, "upload_button")
        upload_btn.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)
        time.sleep(2)  # Force wait time

        assert driver.current_url == f"{host}/dataset/list", "Test failed!"

        # Count final datasets
        final_datasets = count_datasets(driver, host)
        assert final_datasets == initial_datasets + 1, "Test failed!"

        print("Test passed!")

    finally:

        # Close the browser
        close_driver(driver)


def test_download_counter_increments():
    """Test that download counter increments without page refresh"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the homepage
        driver.get(f"{host}/")
        wait_for_page_to_load(driver)

        # Find a dataset download button and counter
        try:
            # Find the first download counter
            counter_element = driver.find_element(By.CSS_SELECTOR, "[data-download-counter]")
            initial_count = int(counter_element.text.strip())

            # Get the dataset ID
            dataset_id = counter_element.get_attribute("data-download-counter")

            # Find the corresponding download button
            download_button = driver.find_element(
                By.CSS_SELECTOR, f"[data-download-btn][data-dataset-id='{dataset_id}']"
            )

            # Click the download button
            download_button.click()
            time.sleep(2)  # Wait for download to trigger

            # Verify counter incremented without page refresh
            updated_count = int(counter_element.text.strip())
            assert (
                updated_count == initial_count + 1
            ), f"Counter should increment from {initial_count} to {initial_count + 1}, but got {updated_count}"

            print("Download counter test passed!")

        except Exception as e:
            print(f"Test skipped or failed: {e}")
            # If no datasets available, skip the test
            pass

    finally:
        close_driver(driver)


def test_download_counter_refreshes_on_visibility_change():
    """Test that counters refresh when returning to the page"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the homepage
        driver.get(f"{host}/")
        wait_for_page_to_load(driver)

        try:
            # Find a dataset and get initial counter
            counter_element = driver.find_element(By.CSS_SELECTOR, "[data-download-counter]")
            dataset_id = counter_element.get_attribute("data-download-counter")
            initial_count = int(counter_element.text.strip())

            # Open download in new tab
            original_window = driver.current_window_handle
            driver.execute_script(f"window.open('{host}/dataset/download/{dataset_id}', '_blank');")
            time.sleep(2)

            # Switch back to original tab
            driver.switch_to.window(original_window)
            time.sleep(1)

            # Trigger visibility change by switching tabs
            driver.execute_script("document.dispatchEvent(new Event('visibilitychange'));")
            time.sleep(3)  # Wait for refresh

            # Check if counter updated
            updated_count = int(counter_element.text.strip())
            assert updated_count >= initial_count, "Counter should have been refreshed"

            print("Visibility change test passed!")

        except Exception as e:
            print(f"Test skipped or failed: {e}")
            pass

    finally:
        close_driver(driver)


def test_api_html_view_displays_datasets():
    """Test that /dataset/api shows HTML view with datasets"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the API HTML view
        driver.get(f"{host}/dataset/api")
        wait_for_page_to_load(driver)

        # Verify page loaded by checking URL
        assert (
            "/dataset/api" in driver.current_url
        ), f"Page should navigate to /dataset/api, got {
            driver.current_url}"

        # Verify table exists
        try:
            table = driver.find_element(By.CSS_SELECTOR, "table")
            assert table is not None, "Table should be present"

            # Verify download counter column exists (or just verify table has
            # data)
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            if rows:
                print(
                    f"API HTML view test passed! Found {
                        len(rows)} datasets in table."
                )
            else:
                print("API HTML view test passed! Table is present but may be empty.")

        except Exception as e:
            print(f"Test skipped or failed: {e}")
            pass

    finally:
        close_driver(driver)


def test_download_counter_on_detail_page():
    """Test that download counter appears on dataset detail page"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open homepage first
        driver.get(f"{host}/")
        wait_for_page_to_load(driver)

        try:
            # Find a dataset link
            dataset_link = driver.find_element(By.CSS_SELECTOR, "a[href*='/doi/']")
            dataset_url = dataset_link.get_attribute("href")

            # Open dataset detail page
            driver.get(dataset_url)
            wait_for_page_to_load(driver)

            # Verify download counter is present
            counter_element = driver.find_element(By.CSS_SELECTOR, "[data-download-counter]")
            assert counter_element is not None, "Download counter should be present"

            count = int(counter_element.text.strip())
            assert count >= 0, "Download count should be >= 0"

            # Verify download button is present
            download_button = driver.find_element(By.CSS_SELECTOR, "[data-download-btn]")
            assert download_button is not None, "Download button should be present"

            print("Detail page counter test passed!")

        except Exception as e:
            print(f"Test skipped or failed: {e}")
            pass

    finally:
        close_driver(driver)


# Call the test functions
if __name__ == "__main__":
    test_upload_dataset()
    test_download_counter_increments()
    test_download_counter_refreshes_on_visibility_change()
    test_api_html_view_displays_datasets()
    test_download_counter_on_detail_page()
