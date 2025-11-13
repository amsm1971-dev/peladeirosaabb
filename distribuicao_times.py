def distribuir_times(grupo):
    time_azul = [None] * 8
    time_branco = [None] * 8
    usados = set()

    posicoes_fixas = ['Zagueiro', 'Lateral 1', 'Lateral 2', 'Meio Campo 1',
                      'Meio Campo 2', 'Meio Campo 3', 'Atacante 1', 'Atacante 2']

    def criar_jogador(jogador, posicao_forcada):
        return {'id': jogador[0], 'nome': jogador[1], 'pontos': jogador[4], 'posicao': posicao_forcada}

    def separar_por_posicao(grupo, posicao_nome):
        pri = [j for j in grupo if j[2].strip().lower() == posicao_nome and j[0] not in usados]
        sec = [j for j in grupo if j[3].strip().lower() == posicao_nome and j[0] not in usados]
        todos = pri + sec

        # ⚡️ Remover duplicados (caso o jogador tenha posição 1 e 2 iguais)
        jogadores_unicos = []
        vistos = set()
        for j in todos:
            if j[0] not in vistos:
                jogadores_unicos.append(j)
                vistos.add(j[0])

        jogadores_unicos.sort(key=lambda x: -x[4])
        return jogadores_unicos

    def alocar_em_posicao(time, index, jogador, posicao_nome):
        time[index] = criar_jogador(jogador, posicao_nome)
        usados.add(jogador[0])

    # 1️⃣ Alocar Zagueiros
    zagueiros = separar_por_posicao(grupo, 'zagueiro')
    if len(zagueiros) >= 1:
        alocar_em_posicao(time_azul, 0, zagueiros[0], 'Zagueiro')
    if len(zagueiros) >= 2:
        alocar_em_posicao(time_branco, 0, zagueiros[1], 'Zagueiro')

    # 2️⃣ Alocar Laterais
    laterais = separar_por_posicao(grupo, 'lateral')
    ordem_laterais = [(time_branco, 1), (time_azul, 1), (time_branco, 2), (time_azul, 2)]

    for idx, (time, pos_idx) in enumerate(ordem_laterais):
        if idx < len(laterais):
            alocar_em_posicao(time, pos_idx, laterais[idx], f'Lateral {pos_idx}')

    # 3️⃣ Alocar Meio Campo
    meios = separar_por_posicao(grupo, 'meio campo')
    ordem_meio = [(time_azul, 3), (time_branco, 3), (time_branco, 4), (time_azul, 4), (time_branco, 5), (time_azul, 5)]

    for idx, (time, pos_idx) in enumerate(ordem_meio):
        if idx < len(meios):
            alocar_em_posicao(time, pos_idx, meios[idx], f'Meio Campo {pos_idx - 2}')

    # 4️⃣ Alocar Atacantes
    atacantes = separar_por_posicao(grupo, 'atacante')
    ordem_atacante = [(time_branco, 6), (time_azul, 6), (time_azul, 7), (time_branco, 7)]

    for idx, (time, pos_idx) in enumerate(ordem_atacante):
        if idx < len(atacantes):
            alocar_em_posicao(time, pos_idx, atacantes[idx], f'Atacante {pos_idx - 5}')

    # 🔥 Jogadores restantes (filtrando pelo controle de usados)
    restantes = [j for j in grupo if j[0] not in usados]

    # 5️⃣ Completar posições vazias com jogadores restantes
    for i in range(8):
        if time_azul[i] is None and restantes:
            jogador = restantes.pop(0)
            alocar_em_posicao(time_azul, i, jogador, posicoes_fixas[i])

        if time_branco[i] is None and restantes:
            jogador = restantes.pop(0)
            alocar_em_posicao(time_branco, i, jogador, posicoes_fixas[i])

    # Garantir que todas as posições estejam preenchidas (mesmo que com jogadores vazios)
    for i in range(8):
        if time_azul[i] is None:
            time_azul[i] = {'id': 0, 'nome': '', 'pontos': 0, 'posicao': posicoes_fixas[i]}
        if time_branco[i] is None:
            time_branco[i] = {'id': 0, 'nome': '', 'pontos': 0, 'posicao': posicoes_fixas[i]}

    total_azul = sum(j['pontos'] for j in time_azul)
    total_branco = sum(j['pontos'] for j in time_branco)

    return time_azul, time_branco, total_azul, total_branco, usados  # 🔥 Corrigido: agora está retornando os 5 elementos

import re

POSICOES_FIXAS = [
    'Zagueiro',
    'Lateral 1', 'Lateral 2',
    'Meio Campo 1', 'Meio Campo 2', 'Meio Campo 3',
    'Atacante 1', 'Atacante 2'
]

DISTRIBUICAO = [
    ("Zagueiro", 1),
    ("Lateral", 2),
    ("Meio Campo", 3),
    ("Atacante", 2)
]

def normalizar_posicao(p):
    """Remove números e hifens para agrupar por posição principal"""
    if not p:
        return None
    p = p.strip().title()
    p = re.sub(r"\s*\d+$", "", p)   # remove numeração tipo "Atacante 1"
    p = p.replace("-", " ")         # unifica "Meio-Campo"
    return p

def distribuir_times_4(jogadores):
    nomes_times = ["Time A", "Time B", "Time C", "Time D"]
    times = {t: {"titulares": [], "reservas": [], "total_titulares": 0, "total_reservas": 0} for t in nomes_times}

    # Separar jogadores por posição_1 normalizada
    jogadores_por_posicao = {p: [] for p, _ in DISTRIBUICAO}
    for j in jogadores:
        pos1 = normalizar_posicao(j[1])
        if pos1 in jogadores_por_posicao:
            jogadores_por_posicao[pos1].append(j)

    # Ordenar por pontos (desc)
    for p in jogadores_por_posicao:
        jogadores_por_posicao[p].sort(key=lambda x: -x[3])

    usados = set()
    sentido = 1

    # Distribuir titulares
    for pos, qtd in DISTRIBUICAO:
        lista = jogadores_por_posicao[pos]
        idx = 0
        for i in range(qtd):
            ordem_times = nomes_times if sentido == 1 else list(reversed(nomes_times))
            for t in ordem_times:
                if idx < len(lista):
                    jogador = lista[idx]
                    posicao_fixa = f"{pos} {i+1}" if qtd > 1 else pos
                    times[t]["titulares"].append({
                        "nome": jogador[0],
                        "pontos": jogador[3],
                        "posicao": posicao_fixa
                    })
                    times[t]["total_titulares"] += jogador[3]
                    usados.add(jogador[0])
                    idx += 1
        sentido *= -1

    # Jogadores não usados vão para reservas
    reservas = [j for j in jogadores if j[0] not in usados]
    for idx, j in enumerate(reservas):
        t_name = nomes_times[idx % 4]
        times[t_name]['reservas'].append({
            'nome': j[0],
            'pontos': j[3],
            'posicao': 'Reserva'
        })
        times[t_name]['total_reservas'] += j[3]

    return times


# Função para sortear jogos
def sortear_jogos():
    jogos = [
        ("Time A", "Time B"),
        ("Time A", "Time C"),
        ("Time A", "Time D"),
        ("Time B", "Time C"),
        ("Time B", "Time D"),
        ("Time C", "Time D")
    ]
    random.shuffle(jogos)
    return jogos
