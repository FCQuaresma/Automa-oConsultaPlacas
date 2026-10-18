import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from fipe_sites import ConsultaError, _parse_resultado, _valor_numerico


def _fipe(modelo, valor):
    return (
        '<table class="fipe-mobile">'
        f"<tr><td>Modelo: {modelo}</td></tr>"
        f"<tr><td>Valor: {valor}</td></tr>"
        "</table>"
    )


DETRAN = (
    "<table>"
    "<tr><td>Marca:</td><td>VOLVO</td></tr>"
    "<tr><td>Modelo:</td><td>FH 460</td></tr>"
    "</table>"
)


VENAL = (
    "<table><tr><td>Valor Venal:</td><td>{}</td></tr>"
    "<tr><td>Aliquota:</td><td>2,00 %</td></tr></table>"
)


class ValorNumericoTest(unittest.TestCase):
    def test_converte_formato_brasileiro(self):
        self.assertEqual(_valor_numerico("R$ 1.234,56"), 1234.56)

    def test_milhao(self):
        self.assertEqual(_valor_numerico("R$ 1.250.000,00"), 1250000.0)

    def test_ilegivel_vale_menos_um(self):
        self.assertEqual(_valor_numerico("sem valor"), -1.0)


class ParseResultadoTest(unittest.TestCase):
    def test_um_valor(self):
        html = _fipe("FH 460", "R$ 350.000,00")
        self.assertEqual(_parse_resultado(html), ("FH 460", "R$ 350.000,00"))

    def test_varios_valores_traz_o_maior(self):
        html = (
            _fipe("FH 460", "R$ 350.000,00")
            + _fipe("FH 540", "R$ 1.250.000,00")
            + _fipe("FH 400", "R$ 99.000,00")
        )
        self.assertEqual(_parse_resultado(html), ("FH 540", "R$ 1.250.000,00"))

    def test_maior_compara_numero_e_nao_texto(self):
        # Como texto, "R$ 99.000,00" > "R$ 100.000,00"; como numero, nao.
        html = _fipe("A", "R$ 99.000,00") + _fipe("B", "R$ 100.000,00")
        self.assertEqual(_parse_resultado(html), ("B", "R$ 100.000,00"))

    def test_varios_valores_na_mesma_tabela(self):
        html = (
            '<table class="fipe-mobile">'
            "<tr><td>Modelo: A</td></tr><tr><td>Valor: R$ 10.000,00</td></tr>"
            "<tr><td>Modelo: B</td></tr><tr><td>Valor: R$ 20.000,00</td></tr>"
            "</table>"
        )
        self.assertEqual(_parse_resultado(html), ("B", "R$ 20.000,00"))

    def test_sem_modelo_fipe_usa_modelo_detran(self):
        html = DETRAN + '<table class="fipe-mobile"><tr><td>Valor: R$ 1,00</td></tr></table>'
        self.assertEqual(_parse_resultado(html), ("FH 460", "R$ 1,00"))

    def test_so_detran_sem_fipe_nem_venal(self):
        self.assertEqual(
            _parse_resultado(DETRAN), ("VOLVO FH 460", config.NAO_ENCONTRADO)
        )

    def test_sem_fipe_usa_valor_venal_mais_10_porcento(self):
        html = DETRAN + VENAL.format("R$ 123.540,00")
        self.assertEqual(_parse_resultado(html), ("VOLVO FH 460", "R$ 135.894,00"))

    def test_valor_venal_sem_espaco_apos_rs(self):
        html = DETRAN + VENAL.format("R$123.540,00")
        self.assertEqual(_parse_resultado(html)[1], "R$ 135.894,00")

    def test_valor_venal_arredonda_centavos(self):
        html = DETRAN + VENAL.format("R$ 100,05")
        self.assertEqual(_parse_resultado(html)[1], "R$ 110,06")

    def test_fipe_tem_prioridade_sobre_valor_venal(self):
        html = _fipe("FH 460", "R$ 350.000,00") + VENAL.format("R$ 123.540,00")
        self.assertEqual(_parse_resultado(html), ("FH 460", "R$ 350.000,00"))

    def test_nao_encontrado_na_fipe_com_valor_venal(self):
        html = (
            "<p>Não foram encontrados veículos na Tabela FIPE</p>"
            + VENAL.format("R$ 1.000,00")
        )
        self.assertEqual(
            _parse_resultado(html), (config.NAO_ENCONTRADO, "R$ 1.100,00")
        )

    def test_mensagem_nao_encontrado(self):
        html = "<p>Não foram encontrados dados para esta placa</p>"
        self.assertEqual(
            _parse_resultado(html), (config.NAO_ENCONTRADO, config.NAO_ENCONTRADO)
        )

    def test_pagina_inesperada_levanta_erro(self):
        with self.assertRaises(ConsultaError):
            _parse_resultado("<html><body>nada</body></html>")


if __name__ == "__main__":
    unittest.main()
