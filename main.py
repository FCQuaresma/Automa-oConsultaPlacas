import sys

import config
import excel_io
from fipe_sites import ConsultaError, aguardar_entre_consultas, consultar_placa


def salvar_com_aviso(wb):
    try:
        excel_io.salvar(wb)
    except PermissionError:
        print(
            f"\nATENCAO: nao foi possivel salvar {config.EXCEL_PATH}.\n"
            "Feche o arquivo no Excel e pressione ENTER para tentar salvar de novo."
        )
        input()
        excel_io.salvar(wb)


def main():
    print(f"Abrindo planilha: {config.EXCEL_PATH}")
    wb, ws = excel_io.abrir()
    placas = excel_io.listar_placas(ws)
    print(f"{len(placas)} placa(s) encontrada(s) na planilha.\n")

    total_ok = 0
    total_nao_encontrado = 0
    total_erro = 0

    for linha, placa in placas:
        for site in config.SITES:
            if not excel_io.precisa_consultar(ws, linha, site):
                continue

            print(f"[{placa}] consultando {site['name']}...", end=" ", flush=True)
            try:
                modelo, valor = consultar_placa(site["base_url"], placa)
                excel_io.gravar_resultado(ws, linha, site, modelo, valor)
                salvar_com_aviso(wb)
                if valor == config.NAO_ENCONTRADO:
                    total_nao_encontrado += 1
                    print("nao encontrado")
                else:
                    total_ok += 1
                    print(f"OK - {modelo} - {valor}")
            except ConsultaError as e:
                total_erro += 1
                print(f"ERRO ({e})")
            except Exception as e:
                total_erro += 1
                print(f"ERRO inesperado ({e})")

            aguardar_entre_consultas()

    print("\nResumo:")
    print(f"  OK: {total_ok}")
    print(f"  Nao encontrado: {total_nao_encontrado}")
    print(f"  Erros: {total_erro}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario. Progresso ja salvo foi mantido.")
        sys.exit(0)
