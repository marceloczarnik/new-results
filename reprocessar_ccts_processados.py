import os
import sys


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from processar_pdf import PASTA_PROCESSADOS, processar_pasta


if __name__ == "__main__":
    processar_pasta(PASTA_PROCESSADOS, mover_para_processados=False)
