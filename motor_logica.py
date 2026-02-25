import pandas as pd
import unicodedata
import os
import requests
from io import StringIO
import difflib

class MotorJogo:
    def __init__(self, data_path="data/jogadores.csv"):
        self.data_path = data_path
        self.df_jogadores = self._carregar_dados()
        
        # Pontuação base
        self.pontos_categoria = {
            "LENDA": 10,
            "FOLCLORICO/HISTORICO": 5,
            "JOGADOR BASE": 2
        }
        self.mapa_letras = self.mapear_raridade(self.df_jogadores)

    def mapear_raridade(self, df):
        # Apenas a letra do NOME OFICIAL importa para saber quais letras sortear
        import string
        dados = []
        for index, row in df.iterrows():
            nome_oficial = self._normalizar_texto(str(row.get('nome', '')))
            if nome_oficial:
                letra_inicial = nome_oficial[0].upper()
                # Apenas letras puras, ignorar números (ex: 8) ou símbolos
                if letra_inicial in string.ascii_uppercase:
                    dados.append({
                        'posicao': row['posicao'],
                        'letra_inicial': letra_inicial,
                        'id_jogador': index
                    })
        
        if not dados:
            return pd.DataFrame()
            
        df_exp = pd.DataFrame(dados)
        # Cria uma tabela de contagem de jogadores únicos: Letra Inicial vs Posição
        mapa = df_exp.groupby(['posicao', 'letra_inicial'])['id_jogador'].nunique().unstack(fill_value=0)
        return mapa

    def sortear_letra_valida(self, posicao_atual):
        import string, random
        if self.mapa_letras.empty or posicao_atual not in self.mapa_letras.index:
            return random.choice(string.ascii_uppercase)
            
        # Filtra apenas letras onde a contagem é maior que zero para aquela posição
        letras_disponiveis = self.mapa_letras.columns[self.mapa_letras.loc[posicao_atual] > 0].tolist()
        
        if not letras_disponiveis:
            return random.choice(string.ascii_uppercase)
            
        return random.choice(letras_disponiveis)

    def _carregar_dados(self):
        if self.data_path.startswith("http://") or self.data_path.startswith("https://"):
            try:
                response = requests.get(self.data_path)
                response.raise_for_status()
                try:
                    csv_data = StringIO(response.text)
                    df = pd.read_csv(csv_data)
                except Exception:
                    response.encoding = 'iso-8859-1'
                    csv_data = StringIO(response.text)
                    df = pd.read_csv(csv_data)
            except Exception as e:
                raise Exception(f"Erro ao baixar dados da URL: {e}")
        else:
            if not os.path.exists(self.data_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {self.data_path}")
            
            # Tenta diferentes encodings comuns (Excel, Bloco de Notas, Windows)
            encodings = ['utf-8', 'iso-8859-1', 'cp1252', 'latin1']
            df = None
            for enc in encodings:
                try:
                    df_temp = pd.read_csv(self.data_path, sep=",", encoding=enc, header=None)
                    
                    # Verifica se a primeira linha (index 0) tem "nome" ou "posicao" para inferir se é cabeçalho
                    primeira_linha = [str(x).strip().lower() for x in df_temp.iloc[0].values]
                    tem_cabecalho = any(col in primeira_linha for col in ['nome', 'name', 'posicao', 'posição'])
                    
                    if tem_cabecalho:
                        df = df_temp.copy()
                        df.columns = df.iloc[0]
                        df = df[1:].reset_index(drop=True)
                    else:
                        df = df_temp.copy()
                        colunas_padrao = ['nome', 'posicao', 'categoria', 'sinonimos']
                        if len(df.columns) > 4:
                            colunas_padrao.extend([f"extra_{i}" for i in range(len(df.columns) - 4)])
                        df.columns = colunas_padrao[:len(df.columns)]
                        
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise Exception("Falha ao ler o arquivo CSV. Formato de codificação não suportado.")
            
        # Normaliza nomes das colunas
        df.columns = df.columns.str.lower().str.strip()
        
        # Tolerar variações do nome da coluna de sinônimos/apelidos
        if 'sinonimos' not in df.columns:
            for col in df.columns:
                if 'sinonimo' in col or 'apelido' in col:
                    df.rename(columns={col: 'sinonimos'}, inplace=True)
                    break
                    
        # Garante a existência da coluna
        if 'sinonimos' not in df.columns:
            df['sinonimos'] = ""
            
        df.fillna("", inplace=True)
        # Limpar espaços em branco extras (ex: 'LAT ' -> 'LAT')
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
                
        # Remove linhas que não possuem um nome definido para evitar crashes
        df = df[df['nome'] != ""]
        df.reset_index(drop=True, inplace=True)
        return df

    def _normalizar_texto(self, texto):
        """Remove acentos e converte para minúsculas para comparação."""
        if not isinstance(texto, str):
            return ""
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
        return texto.lower().strip()

    def _nomes_validos(self, row):
        """Retorna uma lista de nomes válidos (nome principal + sinônimos + partes) normalizados."""
        nomes_brutos = [self._normalizar_texto(row.get('nome', ''))]
        if row.get('sinonimos'):
            nomes_brutos.extend([self._normalizar_texto(s) for s in str(row.get('sinonimos', '')).split(";")])
            
        nomes_finais = set()
        for nome in nomes_brutos:
            nomes_finais.add(nome)
            partes = nome.split(" ")
            if len(partes) > 1:
                for parte in partes:
                    if len(parte) >= 2: # Ignora iniciais caso a pessoa se chame "J C" 
                        nomes_finais.add(parte)
        return list(nomes_finais)

    def validar_palpite(self, palpite, letra_atual, posicao_alvo, categorias_usadas=None, modo_jogo="Time Attack"):
        """
        Verifica se o palpite é um jogador válido para a posição que comece com a letra.
        categorias_usadas: dict contendo a quantidade de vezes que a categoria já foi pontuada (global ou local).
        modo_jogo: "Time Attack", "X1", ou "Battle Royale".
        """
        if categorias_usadas is None:
            categorias_usadas = {"LENDA": 0, "FOLCLORICO/HISTORICO": 0, "JOGADOR BASE": 0}
            
        palpite_norm = self._normalizar_texto(palpite)
        letra_norm = self._normalizar_texto(letra_atual)[0]

        jogador_posicao_errada = None
        jogador_letra_errada = None

        for index, row in self.df_jogadores.iterrows():
            # Pegamos os nomes aceitos para comparar o palpite
            nomes_aceitos = self._nomes_validos(row)
            is_match = False
            for n in nomes_aceitos:
                if palpite_norm == n:
                    is_match = True
                    break
                seq = difflib.SequenceMatcher(None, palpite_norm, n)
                if seq.ratio() >= 0.85:
                    is_match = True
                    break
                if palpite_norm in n or n in palpite_norm:
                    if len(palpite_norm) >= 5 and (palpite_norm in n or n in palpite_norm):
                        is_match = True
                        break

            # SÓ analisa regras de Letra e Posição se o nome estiver correto!
            if is_match:
                # Regra 1: O NOME OFICIAL deve começar com a letra correta
                nome_oficial = self._normalizar_texto(str(row.get('nome', '')))
                inicia_com_letra = nome_oficial.startswith(letra_norm)
                
                if inicia_com_letra:
                    if row['posicao'] == posicao_alvo:
                        categoria = row['categoria']
                        
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
                            pontos_base = 10
                        
                        # Bônus de Raridade
                        letra_upper = letra_norm.upper()
                        qtd_possivel = 0
                        if not self.mapa_letras.empty and posicao_alvo in self.mapa_letras.index and letra_upper in self.mapa_letras.columns:
                            qtd_possivel = self.mapa_letras.loc[posicao_alvo, letra_upper]
                        
                        bonus_raridade = 0
                        if qtd_possivel == 1:
                            bonus_raridade = 50
                        elif 2 <= qtd_possivel <= 3:
                            bonus_raridade = 20
                            
                        pontos_totais = pontos_base + bonus_raridade
                        
                        msg = f"Jogador {row['nome']} ({categoria}) (+{pontos_base})"
                        if bonus_raridade > 0:
                            msg += f" | 💎 BÔNUS DE RARIDADE (Apenas {int(qtd_possivel)} na BD): +{bonus_raridade} pts!"
                            
                        return "ACERTO", msg, pontos_totais, row
                    else:
                        jogador_posicao_errada = row
                else:
                    jogador_letra_errada = row

        if jogador_posicao_errada is not None:
             row = jogador_posicao_errada
             return "ERRO_POSICAO", f"ERRO DE TÁTICA: O jogador {row['nome']} atua como {row['posicao']} e não como {posicao_alvo}.", 0, None

        if jogador_letra_errada is not None:
             row = jogador_letra_errada
             return "ERRO_LETRA", f"O jogador {row['nome']} não atende a regra da letra {letra_atual.upper()}.", 0, None

        return "NAO_ENCONTRADO", "Jogador não reconhecido.", 0, None

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
