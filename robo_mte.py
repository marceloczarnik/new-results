import os
import time
from playwright.sync_api import sync_playwright

def capturar_cct_mte(cnpj_alvo):
    PASTA_NOVOS = r"C:\Users\marce\Desktop\Automacao_Gestao_Sindical\documentos_sindicais\Novos"
    os.makedirs(PASTA_NOVOS, exist_ok=True)
    
    cnpj_limpo = "".join(filter(str.isdigit, cnpj_alvo))
    
    print(f"🚀 [MTE BOT] Iniciando busca inteligente para o CNPJ: {cnpj_alvo}")
    
    with sync_playwright() as p:
        # Aumentamos o tempo de inicialização para dar estabilidade ao Windows
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        try:
            # 1. Acessa a URL do Mediador
            url_mte = "https://www3.mte.gov.br/sistemas/mediador/consultarinstcoletivo"
            page.goto(url_mte, timeout=60000)
            print("🌐 Página do Mediador carregada com sucesso.")
            page.wait_for_load_state("networkidle")
            
            # 2. Ativa a caixinha (checkbox) do CNPJ
            print("🔘 Ativando a caixinha de seleção do CNPJ...")
            checkbox_cnpj = page.locator("input[type='checkbox'][name*='Cnpj' i], input[type='checkbox'][id*='cnpj' i]")
            checkbox_cnpj.first.click()
            
            # 🛑 PAUSA DE SEGURANÇA: Aguarda o site do governo se recarregar após o clique
            print("⏳ Aguardando estabilização da página (pós-clique)...")
            page.wait_for_load_state("load")
            time.sleep(3) 
            
            # 3. Localiza o campo de texto e preenche o CNPJ
            print(f"✍️  Preenchendo o CNPJ: {cnpj_limpo}")
            campo_cnpj = page.locator("input[type='text'][name*='Cnpj' i], input[type='text'][id*='cnpj' i], input[name='txtCNPJ']")
            campo_cnpj.first.fill(cnpj_limpo)
            
            # Mais uma micro-pausa para garantir que o sistema computou a digitação
            time.sleep(1)
            
            # 4. Clica no botão Pesquisar (usando seletores mais explícitos do MTE)
            print("🔍 Enviando consulta... Procurando botão de pesquisa.")
            botao_pesquisar = page.locator("input[name*='Pesquisar' i], input[name*='Consultar' i], input[value='Pesquisar'], input[type='submit']")
            
            # Força o clique no primeiro botão válido que encontrar
            botao_pesquisar.first.click()
            print("📥 Consulta enviada com sucesso! Aguardando retorno do governo...")
            
            # Tempo para o servidor processar a listagem
            time.sleep(6)
            
            # 5. Captura os links de download se houver resultados
            botoes_visualizar = page.locator("a[href*='imprimir' i], input[value*='visualizar' i], img[src*='pdf' i]").all()
            
            if not botoes_visualizar:
                print("⚠️  Nenhuma CCT ativa foi encontrada para este CNPJ no Mediador.")
                return
            
            print(f"📚 {len(botoes_visualizar)} documento(s) encontrado(s). Baixando...")
            
            for idx, botao in enumerate(botoes_visualizar):
                try:
                    with page.expect_download() as download_info:
                        botao.click()
                    
                    download = download_info.value
                    nome_arquivo = f"MTE_AUTO_{cnpj_limpo}_{idx + 1}.pdf"
                    caminho_salvamento = os.path.join(PASTA_NOVOS, nome_arquivo)
                    
                    download.save_as(caminho_salvamento)
                    print(f"📥 [DOWNLOAD OK] Salvo em: documentos_sindicais/Novos/{nome_arquivo}")
                    
                except Exception as e_download:
                    print(f"❌ Falha no download da linha {idx + 1}: {e_download}")
                    
        except Exception as e:
            print(f"💥 Ocorreu um erro durante a automação: {e}")
            
        finally:
            time.sleep(5) # Deixa a janela aberta um pouco para você ver o resultado final antes de fechar
            browser.close()
            print("🔒 Sessão do navegador encerrada.")

if __name__ == "__main__":
    cnpj_teste = "17.697.908/0001-07"
    capturar_cct_mte(cnpj_teste)