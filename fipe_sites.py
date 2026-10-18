import random
import re
import time
from decimal import ROUND_HALF_UP, Decimal

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


def _valor_numerico(texto):
    """Converte 'R$ 1.234,56' em 1234.56; valores ilegiveis valem -1."""
    limpo = re.sub(r"[^\d,]", "", texto).replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return -1.0


ACRESCIMO_VALOR_VENAL = Decimal("1.10")


def _extrair_valor_venal(soup):
    """Valor Venal (base do IPVA) da primeira ocorrencia na pagina, ou None."""
    for td in soup.find_all("td"):
        if td.get_text(strip=True).rstrip(":") == "Valor Venal":
            proximo = td.find_next_sibling("td")
            if proximo:
                bruto = re.sub(r"[^\d,]", "", proximo.get_text(strip=True))
                if bruto:
                    return Decimal(bruto.replace(",", "."))
    return None


def _formatar_moeda(valor):
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


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

    # Pode haver mais de um valor FIPE (varias versoes do modelo): coleta todos
    # os pares (modelo, valor) e fica com o de maior valor.
    candidatos = []
    for tabela in soup.select("table.fipe-mobile"):
        fipe_modelo = None
        for tr in tabela.select("tr"):
            texto = tr.get_text(" ", strip=True)
            if texto.startswith("Modelo:"):
                fipe_modelo = texto.split("Modelo:", 1)[1].strip()
            elif texto.startswith("Valor:"):
                candidatos.append((fipe_modelo, texto.split("Valor:", 1)[1].strip()))
                fipe_modelo = None

    fipe_modelo = fipe_valor = None
    if candidatos:
        fipe_modelo, fipe_valor = max(candidatos, key=lambda c: _valor_numerico(c[1]))

    if fipe_valor:
        modelo = fipe_modelo or modelo_detran or marca
        return modelo, fipe_valor

    modelo_detran_completo = " ".join(p for p in (marca, modelo_detran) if p)

    # Sem valor FIPE: usa o Valor Venal + 10% como valor de referencia.
    venal = _extrair_valor_venal(soup)
    if venal is not None:
        valor = (venal * ACRESCIMO_VALOR_VENAL).quantize(Decimal("0.01"), ROUND_HALF_UP)
        return modelo_detran_completo or config.NAO_ENCONTRADO, _formatar_moeda(valor)

    if modelo_detran_completo:
        return modelo_detran_completo, config.NAO_ENCONTRADO

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
