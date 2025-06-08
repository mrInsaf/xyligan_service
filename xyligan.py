import sys
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from transliterate import translit
import re

# === Настройки пользователя ===
SITE_URL = "https://aiprintgen.ru/" 
USERNAME = "vosaji4645@3dboxer.com"
PASSWORD = "lt=B93z>Re96"
CHROMEDRIVER_PATH = "chrome-win64\\chrome.exe"

# === Опции для ChromeDriver ===
chrome_opts = Options()
chrome_opts.add_argument("--disable-gpu")
chrome_opts.add_argument("--headless=new")
chrome_opts.add_argument("--disable-dev-shm-usage")  # Для стабильности в headless
chrome_opts.add_argument("--no-sandbox")             # Обход ограничений в некоторых окружениях
chrome_opts.add_argument("--disable-setuid-sandbox")
chrome_opts.add_experimental_option("prefs", {
    "download.default_directory": os.path.join(os.getcwd(), "downloads"),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

def generate_filename(prompt):
    transliterated = translit(prompt, 'ru', reversed=True).lower().replace('j', 'i')
    filename_part = re.sub(r'[^a-z0-9]+', '-', transliterated).strip('-')
    return f"aiprintgen_{filename_part}.glb"

def run_script(prompt):
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)

    driver = webdriver.Chrome(options=chrome_opts)
    driver.set_window_size(1920, 1080)
    wait = WebDriverWait(driver, 120)

    try:
        # 1) Открываем страницу
        driver.get(SITE_URL)
        
        # 2) Авторизация
        print("Авторизовываюсь")
        wait.until(EC.presence_of_element_located((By.ID, "login-email"))).send_keys(USERNAME)
        driver.find_element(By.ID, "login-password").send_keys(PASSWORD)
        driver.find_element(
            By.CSS_SELECTOR, 
            "form[action='/login'] button[type='submit'].btn-primary.btn-block"
        ).click()
        wait.until(EC.invisibility_of_element_located((By.ID, "login-email")))
        print("Авторизовывался")

        # 3) Ввод промпта
        print("Ввожу промт")
        textarea = wait.until(EC.presence_of_element_located((By.ID, "prompt")))
        textarea.clear()
        textarea.send_keys(prompt)
        print("ввел")

        print("Отправляю")
        # Отправляем
        driver.find_element(By.ID, "text_submit_btn").click()
        print("Отправил")

        # 4) Выбор формата GLB
        print("Выбираю формат")
        format_select = wait.until(EC.element_to_be_clickable((By.ID, "file_format")))
        Select(format_select).select_by_value("glb")
        print("Выбрал")

        # 5) Ожидаем кнопку «Скачать» и нажимаем
        print("Ожидаю кнопки скачать")
        download_btn = wait.until(EC.element_to_be_clickable((By.ID, "download-btn")))
        download_btn.click()
        print("Скачиваю")

        # 6) Ожидание файла
        print("Ожидаю файла")
        expected_filename = generate_filename(prompt)
        file_path = os.path.join(download_dir, expected_filename)
        
        end_time = time.time() + 120
        while time.time() < end_time:
            if os.path.exists(file_path):
                correct_name = f"{prompt}.glb"
                new_file_path = os.path.join(download_dir, correct_name)
                os.rename(file_path, new_file_path)
                print(f"Файл успешно сохранен: {new_file_path}")
                driver.quit()
                return new_file_path
            time.sleep(1)
        else:
            print("Тайм-аут: файл не найден.")
    finally:
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Не указан промт для генерации модели")
    prompt = sys.argv[1]
    run_script(prompt)