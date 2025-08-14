# ============================
# InfoJobs Scraper - Versão Profissional
# ============================

import os
import time
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ============================
# Classes para organizar dados
# ============================

@dataclass
class Vaga:
    """Representa uma vaga de emprego no InfoJobs"""
    titulo: str
    empresa: str
    link: str
    local: str
    tipo: str  # Remota, Presencial ou Híbrida
    salario: Optional[str] = None

# ============================
# Funções principais do scraper
# ============================

def configurar_driver(headless: bool = False) -> webdriver.Chrome:
    """Configura e retorna o driver do Chrome"""
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

def aceitar_cookies(driver):
    """Clica no botão de aceitar cookies do site"""
    try:
        botao_cookies = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        )
        botao_cookies.click()
        print("✅ Cookies aceitos")
    except TimeoutException:
        print("⚠️ Botão de cookies não encontrado (ou já aceito)")

def buscar_vagas(driver, palavra_chave: str):
    """Realiza a busca de vagas no site"""
    input_busca = driver.find_element(By.ID, "keywordsCombo")
    input_busca.clear()
    input_busca.send_keys(palavra_chave)
    time.sleep(1)  # Pequena pausa para digitação
    botao_buscar = driver.find_element(By.CSS_SELECTOR, ".btn.btn-primary.btn-d-block.js_buttonloading.jsButton")
    botao_buscar.click()
    print(f"🔍 Buscando vagas para: {palavra_chave}")

def extrair_vagas(driver, quantidade: int) -> List[Vaga]:
    """Extrai informações das vagas exibidas na página"""
    vagas_elementos = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[starts-with(@id,'vacancy')]"))
    )
    
    vagas = []
    for vaga_elem in vagas_elementos[:quantidade]:
        try:
            titulo = vaga_elem.find_element(By.TAG_NAME, "h2").text
            empresa = vaga_elem.find_element(By.CSS_SELECTOR, "div.text-body > a").text
            link = vaga_elem.find_element(By.CSS_SELECTOR, "a.text-decoration-none").get_attribute("href")
            local = vaga_elem.find_element(By.CSS_SELECTOR, "div.mb-8").text

            # Determina se é remota ou presencial
            tipo = "Remota" if vaga_elem.find_elements(By.CSS_SELECTOR, "div.icon-user-home") else "Presencial"

            vagas.append(Vaga(titulo, empresa, link, local, tipo))
            print(f"✅ Vaga encontrada: {titulo} - {empresa}")
        except Exception as e:
            print(f"⚠️ Erro ao processar vaga: {e}")
            continue

    return vagas

def salvar_excel(vagas: List[Vaga], nome_arquivo: str = None):
    """Salva as vagas em um arquivo Excel na Área de Trabalho"""
    if not nome_arquivo:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"vagas_infojobs_{timestamp}.xlsx"

    caminho = Path.home() / "Desktop" / nome_arquivo

    df = pd.DataFrame([{
        "Título": v.titulo,
        "Empresa": v.empresa,
        "Local": v.local,
        "Tipo": v.tipo,
        "Link": v.link
    } for v in vagas])

    with pd.ExcelWriter(caminho, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Vagas")
        workbook = writer.book
        worksheet = writer.sheets["Vagas"]

        # Ajuste de largura das colunas
        worksheet.set_column("A:A", 50)
        worksheet.set_column("B:B", 30)
        worksheet.set_column("C:C", 25)
        worksheet.set_column("D:D", 15)
        worksheet.set_column("E:E", 60)

        # Formatação do cabeçalho
        cabecalho = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        for col_num, valor in enumerate(df.columns.values):
            worksheet.write(0, col_num, valor, cabecalho)

    print(f"💾 Arquivo Excel salvo na Área de Trabalho: {caminho}")

# ============================
# Execução principal
# ============================

def main():
    palavra_chave = "Programador Java"
    quantidade_vagas = 10
    driver = configurar_driver(headless=False)
    driver.get("https://www.infojobs.com.br/")

    aceitar_cookies(driver)
    buscar_vagas(driver, palavra_chave)
    vagas = extrair_vagas(driver, quantidade_vagas)
    salvar_excel(vagas)

    driver.quit()
    print("🎉 Scraping concluído com sucesso!")

if __name__ == "__main__":
    main()
