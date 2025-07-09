from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, WebDriverException
from selenium.webdriver.firefox.options import Options
import time

# ========== PARSER ==========
def parse_abogado_info_2(texto: str) -> dict:
    lines = [line.strip() for line in texto.strip().split("\n") if line.strip()]
    data = {}

    field_map = {
        "Número de Colegiación:": "colegiacion",
        "RUA:": "rua",
        "Correo Electrónico": "correo",
        "Tel. Residencial": "tel_residencial",
        "Tel. Oficina": "tel_oficina",
        "Tel. Celular": "tel_celular",
        "Otro": "otro",
        "Especialidades": "especialidades",
        "Delegación:": "delegacion",
    }

    all_labels = set(field_map.keys())

    data["nombre"] = lines[0] if lines else ""
    i = 1
    while i < len(lines):
        line = lines[i].strip()
        matched = False

        for label, key in field_map.items():
            if label.endswith(":") and line.startswith(label):
                value = line[len(label):].strip()
                data[key] = value
                matched = True
                break

            elif line.lower() == label.lower():
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if (next_line in all_labels) or any(next_line.startswith(lab) for lab in all_labels):
                    data[key] = ""
                else:
                    data[key] = next_line
                    i += 1
                matched = True
                break

        i += 1
    return data

# ========== DRIVER UTILS ==========
def crear_driver():
    options = Options()
    driver = webdriver.Firefox(options=options)
    return driver

def obtener_rows(driver):
    for intento in range(5):
        try:
            shadow_host = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/div'))
            )
            shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)

            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script(
                    """
                    const root = arguments[0].shadowRoot;
                    return root && root.querySelectorAll('div.row').length > 0;
                    """, shadow_host)
            )

            rows = driver.execute_script(
                "return Array.from(arguments[0].shadowRoot.querySelectorAll('div.row'));",
                shadow_host
            )
            return rows

        except StaleElementReferenceException:
            print(f"⚠️ Intento {intento + 1}: DOM cambió, reintentando...")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Error inesperado al obtener Shadow DOM: {e}")
            return []

    raise Exception("⛔ No se pudo acceder a los rows del Shadow DOM tras múltiples intentos.")

# ========== SCRAPER PRINCIPAL ==========

def main_scraper():
    base_url = "https://capr.org/account/#app/member-directory/?name=&last=&license=&especialidad=&delegacion=&searching=true"
    list_datos = []
    driver = crear_driver()

    try:
        for i in range(30):
            url_actual = base_url if i == 0 else f"{base_url}&page={i}"
            print(f"🌐 Iteración {i}, accediendo a: {url_actual}")

            try:
                driver.set_page_load_timeout(15)
                driver.get(url_actual)
                rows = obtener_rows(driver)

                for j in range(1, len(rows), 2):
                    text_data = rows[j].text
                    parsed = parse_abogado_info_2(text_data)
                    list_datos.append(parsed)

            except TimeoutException:
                print("⏰ Timeout al cargar la página")
                continue
            except WebDriverException as e:
                print(f"🔁 Reiniciando driver por error: {e}")
                driver.quit()
                driver = crear_driver()
                continue

    finally:
        driver.quit()

    return list_datos

# ========== EJECUCIÓN ==========

if __name__ == "__main__":
    datos = main_scraper()
    print(f"✅ Scrapeo finalizado. Total registros: {len(datos)}")
    for d in datos[:3]:
        print(d)  # Mostrar los primeros 3 como muestra