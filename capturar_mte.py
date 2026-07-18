import os
import time
from playwright.sync_api import sync_playwright

def capturar_cct_mte(cnpj_alvo):
    # Define caminhos absolutos baseados na sua estrutura
    PASTA_NOVOS = r"C:\Users\marce\Desktop\Automacao_Gestao_Sindical\Novos"
    
    # Garante que a pasta Novos existe
    os.makedirs(PASTA_NOVOS, exist_ok=True)
    
    # Limpa formatação do CNPJ (deixa apenas números)
    cnpj_limpo = "".join(filter(str.isdigit, cnpj_alvo))
    
    print(f"🚀 [MTE BOT] Iniciando busca para o CNPJ: {cnpj_alvo}")
    
    with sync_playwright() as p:
        # headless=False permite que você veja a janela do navegador abrindo e trabalhando
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        try:
            # 1. Acessa a página de consulta do Mediador
            url_mte = "http://mediador.mte.gov.br/mediador/consultarInstrumentoColetivo"
            page.goto(url_mte, timeout=60000)
            print("🌐 Página do Mediador carregada.")
            
            # 2. Localiza e preenche o campo de CNPJ
            # O campo padrão do MTE geralmente responde pelo ID ou Name 'txtCNPJ' ou similar
            # Usamos seletores flexíveis para garantir o mapeamento
            campo_cnpj = page.locator("input[name*='Cnpj'], input[name*='cnpj'], input[id*='cnpj']")
            campo_cnpj.first.fill(cnpj_limpo)
            print(f"✍️  CNPJ {cnpj_limpo} inserido no formulário.")
            
            # 3. Clica no botão de Pesquisar / Consultar
            botao_pesquisar = page.locator("input[type='submit'], input[value*='Pesquisar'], input[value*='Consultar']")
            botao_pesquisar.first.click()
            print("🔍 Pesquisa disparada. Aguardando retorno do servidor...")
            
            # Pausa para o servidor do governo responder e processar a tabela
            time.sleep(5)
            
            # 4. Localiza os botões/links de visualização ou impressão (geralmente ícones de PDF ou links 'Imprimir')
            botoes_visualizar = page.locator("a[href*='imprimir'], input[value*='Visualizar'], img[src*='pdf']").all()
            
            if not botoes_visualizar:
                print("⚠️  Nenhuma Convenção Coletiva ativa ou pendente foi encontrada para este CNPJ.")
                return
            
            print(f"📚 Encontrado(s) {len(botoes_visualizar)} instrumento(s) coletivo(s). Iniciando downloads...")
            
            # 5. Loop para baixar cada um dos documentos encontrados
            for idx, botao in enumerate(botoes_visualizar):
                try:
                    # Prepara o Playwright para capturar o evento de download gerado pelo clique
                    with page.expect_download() as download_info:
                        botao.click()
                    
                    download = download_info.value
                    
                    # Define o nome do arquivo final salvo na pasta 'Novos'
                    nome_arquivo = f"MTE_CAPTURA_{cnpj_limpo}_{idx + 1}.pdf"
                    caminho_salvamento = os.path.join(PASTA_NOVOS, nome_arquivo)
                    
                    # Salva o arquivo fisicamente
                    download.save_as(caminho_salvamento)
                    print(f"✅ [DOWNLOAD SUCESSO] Salvo em: {nome_arquivo}")
                    
                except Exception as e_download:
                    print(f"❌ Falha ao baixar o documento {idx + 1}: {e_download}")
                    
        except Exception as e:
            print(f"💥 Ocorreu um erro durante a automação: {e}")
            
        finally:
            # Aguarda um momento e fecha o navegador de testes
            time.sleep(2)
            browser.close()
            print("🔒 Sessão do navegador encerrada.")

if __name__ == "__main__":
    # Testando com o CNPJ da Holding de Maringá que você informou
    cnpj_teste = "17.697.908/0001-07"
    capturar_cct_mte(cnpj_teste)