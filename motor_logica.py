import unicodedata
import os
import requests
from io import StringIO
import difflib
import csv
import string

class MotorJogo:
    def __init__(self, data_path="data/jogadores.csv"):
        self.data_path = data_path
        # self.db = { Letra_Inicial: { Posicao: [ {jogador1}, {jogador2} ] } }
        self.db = {} 
        self.jogadores_lista_plana = [] # Para facilitar iterações quando a letra não bate
        self.mapa_letras = {} # { Posicao: { Letra: qtd_jogadores } }
        
        self._carregar_dados()
        self._construir_mapa_raridade()
        
        # Pontuação base
        self.pontos_categoria = {
            "LENDA": 10,
            "FOLCLORICO/HISTORICO": 5,
            "JOGADOR BASE": 0
        }

    def _normalizar_texto(self, texto):
        """Remove acentos e converte para minúsculas para comparação."""
        if not isinstance(texto, str):
            return ""
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
        return texto.lower().strip()

    def _carregar_dados(self):
        """Lê o CSV localmente ou via web, construindo o Banco de Dados JSON estruturado em RAM."""
        texto_csv = ""
        if self.data_path.startswith("http://") or self.data_path.startswith("https://"):
            try:
                response = requests.get(self.data_path)
                response.raise_for_status()
                texto_csv = response.text
            except Exception as e:
                raise Exception(f"Erro ao baixar dados da URL: {e}")
        else:
            if not os.path.exists(self.data_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {self.data_path}")
            
            encodings = ['utf-8', 'iso-8859-1', 'cp1252', 'latin1']
            for enc in encodings:
                try:
                    with open(self.data_path, 'r', encoding=enc) as f:
                        texto_csv = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if not texto_csv:
                raise Exception("Falha ao ler o arquivo CSV. Formato de codificação não suportado.")

        # Parsing manual com bibliotecas core (CSV) para evitar peso do Pandas
        leitor = csv.reader(StringIO(texto_csv), delimiter=',')
        linhas = list(leitor)
        
        if not linhas:
            return

        # Inferência de Cabeçalho Tolerante
        primeira_linha = [str(col).strip().lower() for col in linhas[0]]
        tem_cabecalho = any(c in primeira_linha for c in ['nome', 'name', 'posicao', 'posição'])
        
        cabecalho = primeira_linha if tem_cabecalho else ['nome', 'posicao', 'categoria', 'sinonimos']
        dados_uteis = linhas[1:] if tem_cabecalho else linhas
        
        # Encontra os índices das colunas pra poder ler independente da ordem que o usuário escreveu
        idx_nome = next((i for i, c in enumerate(cabecalho) if 'nome' in c or 'name' in c), 0)
        idx_posicao = next((i for i, c in enumerate(cabecalho) if 'posicao' in c or 'posição' in c), 1)
        idx_categoria = next((i for i, c in enumerate(cabecalho) if 'categoria' in c or 'category' in c), 2)
        idx_sinonimo = next((i for i, c in enumerate(cabecalho) if 'sinonimo' in c or 'apelido' in c), 3)

        # Estrutura inicial do DB
        for letra in string.ascii_uppercase:
            self.db[letra] = {}

        for row in dados_uteis:
            if not row or len(row) <= idx_nome or not str(row[idx_nome]).strip():
                continue # Pula linhas vazias
                
            nome_oficial = str(row[idx_nome]).strip()
            
            # Limpeza
            posicao = str(row[idx_posicao]).strip().upper() if len(row) > idx_posicao else ""
            categoria = str(row[idx_categoria]).strip().upper() if len(row) > idx_categoria else "JOGADOR BASE"
            sinonimos = str(row[idx_sinonimo]).strip() if len(row) > idx_sinonimo else ""
            
            if not self._normalizar_texto(nome_oficial):
                continue
            
            jogador_record = {
                "nome": nome_oficial,
                "posicao": posicao,
                "categoria": categoria,
                "sinonimos": sinonimos
            }
            
            self.jogadores_lista_plana.append(jogador_record)
            
            nomes_aceitos = self._nomes_validos(jogador_record)
            iniciais_unicas = set()
            for n in nomes_aceitos:
                if n and n[0].upper() in string.ascii_uppercase:
                    iniciais_unicas.add(n[0].upper())
                    
            if not iniciais_unicas:
                continue
                
            for letra_inicial in iniciais_unicas:
                if letra_inicial not in self.db:
                    self.db[letra_inicial] = {}
                if posicao not in self.db[letra_inicial]:
                    self.db[letra_inicial][posicao] = []
                self.db[letra_inicial][posicao].append(jogador_record)

    def _construir_mapa_raridade(self):
        """Mapeia quantas opções existem por letra vs posição para o Sorteio e Proporcionalidade."""
        for letra, posicoes in self.db.items():
            for posicao, jogadores in posicoes.items():
                if posicao not in self.mapa_letras:
                    self.mapa_letras[posicao] = {}
                self.mapa_letras[posicao][letra] = len(jogadores)

    def sortear_letra_valida(self, posicao_atual, letras_usadas=None):
        import string, random
        if letras_usadas is None:
            letras_usadas = set()
            
        if not self.mapa_letras or posicao_atual not in self.mapa_letras:
            opcoes = [l for l in string.ascii_uppercase if l not in letras_usadas]
            return random.choice(opcoes) if opcoes else random.choice(string.ascii_uppercase)
            
        letras_disponiveis = [letra for letra, qtd in self.mapa_letras[posicao_atual].items() if qtd > 0]
        letras_filtradas = [l for l in letras_disponiveis if l not in letras_usadas]
        
        # Se todas as letras válidas para esta posição já foram usadas, relaxa a regra
        if not letras_filtradas:
            letras_filtradas = letras_disponiveis
            
        if not letras_filtradas:
            return random.choice(string.ascii_uppercase)
            
        return random.choice(letras_filtradas)

    def _nomes_validos(self, row):
        """Retorna uma lista de nomes válidos (nome principal + sinônimos) normalizados."""
        nomes_brutos = [self._normalizar_texto(row.get('nome', ''))]
        if row.get('sinonimos'):
            nomes_brutos.extend([self._normalizar_texto(s) for s in str(row.get('sinonimos', '')).split(";")])
            
        nomes_finais = set(nomes_brutos)
        # Filtra strings vazias caso existam
        return [n for n in list(nomes_finais) if n]

    def validar_palpite(self, palpite, letra_atual, posicao_alvo, categorias_usadas=None, modo_jogo="Time Attack"):
        """
        Verifica se o palpite é válido. O(1) de acesso às gavetas locais + Fuzzy Matching para erros de digitação.
        """
        if categorias_usadas is None:
            categorias_usadas = {"LENDA": 0, "FOLCLORICO/HISTORICO": 0, "JOGADOR BASE": 0}
            
        palpite_norm = self._normalizar_texto(palpite)
        letra_norm = self._normalizar_texto(letra_atual)[0].upper()
        
        # Filtro Anti-Loteria 1: Blacklist de Nomes Comuns de uma só palavra
        palpite_palavras = palpite_norm.split()
        if len(palpite_palavras) == 1:
            nomes_comuns_proibidos = {"joao", "jose", "carlos", "lucas", "pedro", "silva", "santos", "oliveira", "souza", "costa", "rodrigues", "ferreira", "alves", "marcos", "paulo"}
            if palpite_norm in nomes_comuns_proibidos:
                return "ERRO_NOME_COMUM", f"O nome '{palpite.title()}' é muito comum ou genérico. Por favor, forneça um Sobrenome ou Apelido completo.", 0, None

        match_encontrado = None
        jogador_posicao_errada = None
        jogador_letra_errada = None

        # 1. Busca Super-Rápida (O(1)): Olhar direto na Gaveta da Letra e da Posição Alvo
        if letra_norm in self.db and posicao_alvo in self.db[letra_norm]:
            candidatos_perfeitos = self.db[letra_norm][posicao_alvo]
            
            # Pass 1: Busca por Match Exato
            for comp in candidatos_perfeitos:
                nomes_aceitos = self._nomes_validos(comp)
                for n in nomes_aceitos:
                    if palpite_norm == n and n.startswith(letra_norm.lower()):
                        match_encontrado = comp.copy()
                        match_encontrado['nome_usado'] = n
                        break
                if match_encontrado:
                    break
                    
            # Pass 2: Busca Aproximada (Fuzzy e Substring) apenas se não achou exato
            if not match_encontrado:
                for comp in candidatos_perfeitos:
                    nomes_aceitos = self._nomes_validos(comp)
                    for n in nomes_aceitos:
                        # Fuzzy Matching (Busca por Similaridade)
                        seq = difflib.SequenceMatcher(None, palpite_norm, n)
                        
                        # Filtro Anti-Loteria 2: Rigor na aceitação do Substring/Fuzzy
                        is_valid = False
                        
                        if seq.ratio() >= 0.85:
                            is_valid = True
                        elif len(palpite_norm) >= 5 and (palpite_norm in n or n in palpite_norm):
                            # Se for uma substring, só aceitamos se for uma palavra exata do nome original completo (ex: "silva" tem que ser "Silva" oficial)
                            # ou se a similaridade de pelo menos uma das palavras bater alta.
                            if len(palpite_palavras) == 1:
                                nomes_split = n.split()
                                if palpite_norm in nomes_split:
                                    is_valid = True
                                else:
                                    # Para nomes únicos de dígito curto dentro de longos, exige 95% de aprovação (quase perfeito)
                                    if difflib.SequenceMatcher(None, palpite_norm, n).ratio() >= 0.95:
                                        is_valid = True
                            else:
                                is_valid = True # Se tiver mais de uma palavra, tá liberado o len > 5 na string
                                
                        if is_valid and n.startswith(letra_norm.lower()):
                            match_encontrado = comp.copy()
                            match_encontrado['nome_usado'] = n
                            break
                    if match_encontrado:
                        break

        # SUCESSO: O jogador existe, está na posição certa e começa com a letra certa!
        if match_encontrado:
            categoria = match_encontrado['categoria']
            
            # Motor de Pontuação Proporcional
            usos_globais = categorias_usadas.get(categoria, 0)
            
            if modo_jogo == "Time Attack":
                usos = 0
            elif modo_jogo == "X1":
                usos = 3 if usos_globais >= 1 else 0
            else: # Battle Royale
                usos = usos_globais
                
            pontos_base = 1
            
            if categoria == "LENDA":
                tabela = [50, 45, 40]
                pontos_base = tabela[usos] if usos < len(tabela) else 1
            elif categoria == "FOLCLORICO/HISTORICO":
                tabela = [30, 25, 20]
                pontos_base = tabela[usos] if usos < len(tabela) else 1
            elif categoria == "JOGADOR BASE" or categoria == "BASE":
                pontos_base = 0
            
            # Bônus de Raridade
            qtd_possivel = 0
            if posicao_alvo in self.mapa_letras and letra_norm in self.mapa_letras[posicao_alvo]:
                qtd_possivel = self.mapa_letras[posicao_alvo][letra_norm]
            
            bonus_raridade = 0
            if qtd_possivel == 1:
                bonus_raridade = 50
            elif 2 <= qtd_possivel <= 3:
                bonus_raridade = 20
                
            pontos_totais = pontos_base + bonus_raridade
            
            nome_display = match_encontrado['nome']
            nome_usado = match_encontrado.get('nome_usado', '').title()
            
            # Formatar o nome do display para incluir o apelido usado caso seja diferente do nome oficial
            if nome_usado and nome_usado.lower() != nome_display.lower():
                 nome_display = f'{nome_usado} "{nome_display}"'
                 
            match_encontrado['nome_display'] = nome_display
            
            # Se o palpite norm for muito diferente, é pq validou por Fuzzy Mode
            seq = difflib.SequenceMatcher(None, palpite_norm, self._normalizar_texto(nome_display))
            match_tipo = ""
            if seq.ratio() < 0.99 and seq.ratio() >= 0.85:
                match_tipo = " 🪄"
            
            msg = f"Jogador {nome_display}{match_tipo} ({categoria}) (+{pontos_base})"
            if bonus_raridade > 0:
                msg += f" | 💎 BÔNUS DE RARIDADE (Apenas {int(qtd_possivel)} na BD): +{bonus_raridade} pts!"
                
            return "ACERTO", msg, pontos_totais, match_encontrado

        # 2. Resolução de Erros: Se não encontrou o acerto, foi Erro de Posição, Letra ou Inexistente?
        # Fazemos um scan na DB completa apenas em caso de Erro, para tentar dar feedback ao jogador.
        
        # Pass 1 (Erro): Identificar se o nome existe de forma Exata (evita falsos positivos com Fuzzy)
        for jogador in self.jogadores_lista_plana:
            nomes_aceitos = self._nomes_validos(jogador)
            for n in nomes_aceitos:
                if palpite_norm == n:
                    inicia_com_letra = n.startswith(letra_norm.lower())
                    
                    if jogador['posicao'] != posicao_alvo:
                        jogador_posicao_errada = jogador
                        break
                    
                    if not inicia_com_letra:
                        jogador_letra_errada = jogador
                        break
                    
        # Pass 2 (Erro): Busca Fuzzy caso não haja match exato gerando erro
        if not jogador_posicao_errada and not jogador_letra_errada:
            for jogador in self.jogadores_lista_plana:
                nomes_aceitos = self._nomes_validos(jogador)
                is_match = False
                n_match = ""
                for n in nomes_aceitos:
                    if difflib.SequenceMatcher(None, palpite_norm, n).ratio() >= 0.85 or (len(palpite_norm) >= 5 and (palpite_norm in n or n in palpite_norm)):
                        is_match = True
                        n_match = n
                        break
                
                if is_match:
                    inicia_com_letra = n_match.startswith(letra_norm.lower())
                    
                    if jogador['posicao'] != posicao_alvo:
                        jogador_posicao_errada = jogador
                        break
                    
                    if not inicia_com_letra:
                        jogador_letra_errada = jogador
                        break

        if jogador_posicao_errada is not None:
             row = jogador_posicao_errada
             return "ERRO_POSICAO", f"O jogador {row['nome']} atua como {row['posicao']}.", 0, None

        if jogador_letra_errada is not None:
             row = jogador_letra_errada
             return "ERRO_LETRA", f"O jogador {row['nome']} não atende a regra da letra {letra_atual.upper()}.", 0, None

        return "NAO_ENCONTRADO", f"Não existe jogador com o nome '{palpite}' nesta posição.", 0, None

    def processar_pulo(self, pulos_usados):
        """
        Processa os pontos a deduzir de acordo com os pulos já usados.
        Retorna a dedução e a nova quantidade de pulos.
        """
        if pulos_usados == 0:
            return 0, 1, "1º Pulo grátis"
        elif pulos_usados == 1:
            return -2, 2, "2º Pulo: Amarelo (-2 pts)"
        elif pulos_usados == 2:
            return -5, 3, "3º Pulo: Vermelho (-5 pts)"
        else:
            return -10, pulos_usados + 1, "4º+ Pulo: Nova Tentativa (-10 pts)"
