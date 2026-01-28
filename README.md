# IntuitiveCare-Teste

1.1. Acesso à API de Dados Abertos da ANS
Arquitetura e Organização: Criei uma pasta services e a classe AnsDataClient para garantir a Separação de Responsabilidades. Isso evita misturar a lógica de conexão com o fluxo principal, tornando o código mais fácil de manter e escalar.

Escolha de Ferramentas (KISS): Escolhi a biblioteca BeautifulSoup4 (BS4) ao invés de alternativas como Selenium ou Regex puro.

Por que não Selenium? O Selenium é muito pesado para uma página estática e violaria o princípio KISS (Keep It Simple).

Por que não Regex puro? Regex é frágil para fazer parsing de tags HTML e poderia quebrar facilmente com mudanças no site. O BS4 é a solução mais equilibrada.

Pensamento Crítico (Regex): Como os nomes dos arquivos variam bastante entre os anos (ex: 1T2025 vs dados_2023_1_trim), precisei desenvolver uma Expressão Regular (Regex) robusta que atendesse a todos os casos sem "hardcode". Essa foi a parte mais desafiadora desta etapa (ver método _detect_quarter em src/services/ans_cliente.py).

Performance: No download, priorizei a eficiência de recursos utilizando stream=True e shutil.copyfileobj. Essa abordagem processa o download em partes (chunks), evitando carregar arquivos ZIP grandes inteiros na memória RAM. Isso previne que a aplicação crashe em servidores com memória limitada.