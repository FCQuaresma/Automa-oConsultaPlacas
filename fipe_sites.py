import random
import time

import requests
from bs4 import BeautifulSoup

import config

NAO_ENCONTRADO_MARCADORES = (
    "não foram encontrados",
    "nao foram encontrados",
)


class ConsultaError(Exception):
    pass


def _session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": config.USER_AGENT,
        "Accept-Language": "pt-BR,pt;q=0.9",
    })
    return s


ESPERA_MAXIMA = 30  # segundos - acima disso, desiste em vez de travar o script


def _get_com_retry(session, url, tentativas=3):
    espera = 5
    for tentativa in range(1, tentativas + 1):
        resp = session.get(url, timeout=config.REQUEST_TIMEOUT)
        corpo = resp.text
        desafio = "<title>Just a moment" in corpo or "Access denied" in corpo
        if resp.status_code == 200 and not desafio:
            return corpo

        retry_after_hdr = resp.headers.get("Retry-After")
        retry_after = float(retry_after_hdr) if retry_after_hdr else None
        if retry_after and retry_after > ESPERA_MAXIMA:
            raise ConsultaError(
                f"site bloqueou temporariamente (pede espera de {int(retry_after)}s, "
                "tente novamente mais tarde)"
            )
        if tentativa == tentativas:
            raise ConsultaError(
                f"bloqueado/instavel apos {tentativas} tentativas "
                f"(status={resp.status_code}, desafio={desafio})"
            )
        time.sleep(retry_after if retry_after else espera)
        espera *= 2
    raise ConsultaError("nao foi possivel obter resposta")


def _parse_resultado(html):
    soup = BeautifulSoup(html, "html.parser")

    marca = modelo_detran = None
    for tr in soup.select("table tr"):
        cols = tr.find_all("td")
        if len(cols) == 2:
            rotulo = cols[0].get_text(strip=True).rstrip(":")
            valor_txt = cols[1].get_text(strip=True)
            if rotulo == "Marca":
                marca = valor_txt
            elif rotulo == "Modelo":
                modelo_detran = valor_txt

    corpo_lower = soup.get_text(" ", strip=True).lower()
    fipe_nao_encontrada = any(m in corpo_lower for m in NAO_ENCONTRADO_MARCADORES)

    fipe_modelo = fipe_valor = None
    tabela_mobile = soup.select_one("table.fipe-mobile")
    if tabela_mobile:
        for tr in tabela_mobile.select("tr"):
            texto = tr.get_text(" ", strip=True)
            if texto.startswith("Modelo:"):
                fipe_modelo = texto.split("Modelo:", 1)[1].strip()
            elif texto.startswith("Valor:"):
                fipe_valor = texto.split("Valor:", 1)[1].strip()

    if fipe_valor:
        modelo = fipe_modelo or modelo_detran or marca
        return modelo, fipe_valor

    if marca or modelo_detran:
        modelo = " ".join(p for p in (marca, modelo_detran) if p)
        return modelo, config.NAO_ENCONTRADO

    if fipe_nao_encontrada:
        return config.NAO_ENCONTRADO, config.NAO_ENCONTRADO

    raise ConsultaError("Formato de pagina inesperado, nao foi possivel extrair dados")


def consultar_placa(base_url, placa):
    session = _session()
    url = f"{base_url}/placa/{placa}"
    html = _get_com_retry(session, url)
    return _parse_resultado(html)


def aguardar_entre_consultas():
    time.sleep(random.uniform(*config.DELAY_BETWEEN_REQUESTS))
