import json
import time
import re
import sys
import os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup

def GetSections(content_div, **kwargs):
    list_section = []
    header_section = ''
    options = {'section' : '',
                'section2' : '', }
    options.update(kwargs)
    #print(f"\n KWARGS{kwargs}")
    #print(f"\n options {options}")
    #second_name_sec = kwargs.pop('second_name_sec','')
    #print(options)
    if len(kwargs) > 1:
        header_section = content_div.find(lambda tag: tag.name in ['h2', 'h3', 'h4'] and ((options['section'] in tag.text) or (options['section2'] in tag.text)))
    else:
        header_section = content_div.find(lambda tag: tag.name in ['h2', 'h3', 'h4'] and options['section'] in tag.text)

    #print(f"\n header_section {header_section}")

    if header_section:
        # 4. Extraer el siguiente hermano (párrafo, lista, etc.)
        next_element = header_section.find_next_sibling()
        #print(next_element)
        
        while next_element and next_element.name not in ['h1', 'h2', 'h3', 'h4']:
            #print(next_element.name)
            if next_element.name == 'p' and len(next_element.get_text(strip=True)) > 0:
                text_paragraph = next_element.get_text(strip=True)
                list_section.append(text_paragraph.replace('\t',''))
            elif next_element.name == 'ul':
                list_section.extend([li.get_text(strip=True).replace('\t', '') for li in next_element.find_all('li')])
            next_element = next_element.find_next_sibling()
        
        #print(f"\n {section} encontradas: {list_section}")
    
    return list_section

options = Options()
options.headless = True
driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

base_url = "https://www.petmd.com"
start_url = f"{base_url}/cat/conditions"

driver.get(start_url)
time.sleep(4)

soup = BeautifulSoup(driver.page_source, 'html.parser')

# Obtener todos los enlaces
condition_links = []

for num_card in range(8, 510):
    #div.kib-grid__item--span-4\@min-xs:nth-child(8)
    #div.kib-grid__item--span-4\@md:nth-child(5)
    card_title = f'div.kib-grid__item--span-4\@md:nth-child({num_card}) a'
    #card_title = f'div.kib-grid__item--span-4\@min-xs:nth-child({num_card}) a'
    #card_title = f'div.kib-grid__item:nth-child({num_card}) a'
    cards = soup.select(card_title)
    if len(cards) > 0:
        #print(num_card)
        condition_links.append(base_url + cards[0]['href'])

#print(f"Se encontraron {len(condition_links)} condiciones. Extrayendo información...\n")

# Lista para guardar resultados
results = []

# Recorrer cada enlace
for i, url in enumerate(condition_links):
    try:
        if 'conditions' not in url:
            continue

        driver.get(url)
        time.sleep(4)
        article_soup = BeautifulSoup(driver.page_source, 'html.parser')
        section = ''
        section2 = ''

        title = article_soup.find('h1').text.strip()
        print(f'title {title}')

        # Buscar el contenido completo del artículo
        content_div = article_soup.find('div', class_='article_content_article_body__GQzms')
        content = content_div.get_text(separator=' ', strip=True) if content_div else "Contenido no disponible"
        #print(content_div)

        # ----- RESUMEN --------
        paragraph = content_div.find_next_sibling('h2')
        
        if paragraph:
            summary = paragraph.get_text()
        else: 
            summary = f'The sickness is called {title}'

        # ----- SÍNTOMAS --------
        symptoms = GetSections(content_div, section = 'Symptoms')
        if len(symptoms) < 1:
            symptoms = ["Síntoms not identified"]  # Regular

        # ----------- CAUSAS -------------------
        causes = GetSections(content_div, section = 'Causes')
        if len(causes) < 1:
            causes = ["Review with your veterinarian about possible causes"]  # Regular

        # ----------- DIAGNOSIS ----------------
        diagnosis = GetSections(content_div, section = 'Diagnose', section2 ='Diagnosis')
        if len(diagnosis) < 1:
            diagnosis = ["Review with your veterinarian about the diagnosis"]  # Regular

        # -------- MANEJO DE ENFERMEDAD --------
        recommendations = GetSections(content_div, section = 'Management')
        if len(recommendations) < 1:
            recommendations = "Review with your veterinarian for a professional diagnosis and recommendations."
        
        # ---------- JSON FILE -------------
        results.append({
            "id": str(i + 1),
            "title": title,
            "summary": summary,
            "causes": causes,
            "symptoms": symptoms,
            "diagnosis": diagnosis,
            "recommendations": recommendations,
            "content": content[:200],
            "url": url
        })

        print(f"[{i + 1}] {title}")
    except Exception as e:
        print(f"Error en {url}: {e}")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        

# Cerrar el navegador
driver.quit()

# Guardar resultados en archivo JSON
with open("condiciones_gatos_Final2.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nScraping finalizado. Archivo 'condiciones_mascotas.json' generado.")

