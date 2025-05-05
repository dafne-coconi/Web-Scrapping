import json
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup

options = Options()
options.headless = True
driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

base_url = "https://www.petmd.com"
start_url = f"{base_url}/dog/conditions"

driver.get(start_url)
time.sleep(5)

soup = BeautifulSoup(driver.page_source, 'html.parser')

# Obtener todos los enlaces
#card_title = 'kib-grid__item kib-grid__item--span-4@min-xs kib-grid__item--span-4@md kib-grid__item--span-4@min-lg az_list_grid_item__KWCvL'
card_title = 'div.kib-grid__item--span-4\@min-xs:nth-child(9) a'
cards = soup.select(card_title)
condition_links = [base_url + card['href'] for card in cards]

print(f"Se encontraron {len(condition_links)} condiciones. Extrayendo información...\n")

# Lista para guardar resultados
results = []

# Recorrer cada enlace
for i, url in enumerate(condition_links):
    try:
        driver.get(url)
        time.sleep(4)
        article_soup = BeautifulSoup(driver.page_source, 'html.parser')

        title = article_soup.find('h1').text.strip()

        # Buscar el contenido completo del artículo
        content_div = article_soup.find('div', class_='article-body')
        content = content_div.get_text(separator=' ', strip=True) if content_div else "Contenido no disponible"

        # Simulación básica de síntomas y recomendaciones ß
        symptom_patterns = [
            r"(?:Symptoms|Signs)(?: of [\w\s]+)?(?: include| are| may include)[:\s]+(.+?)(?:\.|\n|$)",
            r"Common symptoms(?: include| are)[:\s]+(.+?)(?:\.|\n|$)",
            r"Symptoms and Types"
        ]

        symptoms = ["síntoma no identificado"]  # Regular
        """
        for pattern in symptom_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                raw = match.group(1)  # Ej: "vomiting, lethargy, and diarrhea"
                # Separar los síntomas por comas o "and"
                symptoms = [s.strip().lower() for s in re.split(r',| and ', raw) if s.strip()]
                break
        """
        recommendations = "Consulta a un veterinario para diagnóstico profesional."

        results.append({
            "id": str(i + 1),
            "title": title,
            "symptoms": symptoms,
            "recommendations": recommendations,
            "content": content,
            "url": url
        })

        print(f"[{i + 1}] {title}")
    except Exception as e:
        print(f"Error en {url}: {e}")

# Cerrar el navegador
driver.quit()

# Guardar resultados en archivo JSON
with open("condiciones_mascotas.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nScraping finalizado. Archivo 'condiciones_mascotas.json' generado.")

