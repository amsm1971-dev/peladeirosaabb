from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random

from distribuicao_times import distribuir_times, distribuir_times_4, sortear_jogos

app = Flask(__name__)
app.secret_key = 'chave_secreta_segura'
DB_PATH = 'banco_futebol.db'


# --------- Banco ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jogadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            posicao_1 TEXT,
            posicao_2 TEXT,
            pontos INTEGER DEFAULT 1,
            presente INTEGER DEFAULT 0,
            a_partir_do_jogo INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()


# --------- Rotas ----------
@app.route('/')
def index():
    jogadores = get_jogadores()
    return render_template('index.html', jogadores=jogadores)


def get_jogadores():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, presente, a_partir_do_jogo FROM jogadores ORDER BY nome")
    jogadores = cursor.fetchall()
    conn.close()
    return jogadores


@app.route('/adicionar_jogador', methods=['GET', 'POST'])
def adicionar_jogador():
    if request.method == 'POST':
        nome = request.form['nome']
        posicao_1 = request.form['posicao_1']
        posicao_2 = request.form['posicao_2']
        pontos = int(request.form['pontos'])

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jogadores (nome, posicao_1, posicao_2, pontos, presente, a_partir_do_jogo)
            VALUES (?, ?, ?, ?, 0, 1)
        """, (nome, posicao_1, posicao_2, pontos))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('adicionar_jogador.html')


@app.route('/editar_jogador/<int:id>', methods=['GET', 'POST'])
def editar_jogador(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        posicao_1 = request.form['posicao_1']
        posicao_2 = request.form['posicao_2']
        pontos = int(request.form['pontos'])

        cursor.execute("""
            UPDATE jogadores
            SET nome = ?, posicao_1 = ?, posicao_2 = ?, pontos = ?
            WHERE id = ?
        """, (nome, posicao_1, posicao_2, pontos, id))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    cursor.execute("SELECT id, nome, posicao_1, posicao_2, pontos FROM jogadores WHERE id = ?", (id,))
    jogador = cursor.fetchone()
    conn.close()

    if jogador:
        return f'''
        <h2>Editar Jogador</h2>
        <form method="POST">
            Nome: <input type="text" name="nome" value="{jogador[1]}" required><br>
            Posição 1: <input type="text" name="posicao_1" value="{jogador[2]}" required><br>
            Posição 2: <input type="text" name="posicao_2" value="{jogador[3]}" required><br>
            Pontos: <input type="number" name="pontos" value="{jogador[4]}" required><br><br>
            <button type="submit">Salvar Alterações</button>
        </form>
        <br>
        <a href="/">Voltar à Lista de Presença</a>
        '''
    else:
        return "Jogador não encontrado."


@app.route('/excluir_jogador/<int:id>')
def excluir_jogador(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jogadores WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/presenca', methods=['POST'])
def presenca():
    presencas = request.form.getlist('presente')
    jogos = request.form

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE jogadores SET presente = 0, a_partir_do_jogo = 1")

    for jogador_id in presencas:
        a_partir_do_jogo = int(jogos.get(f"jogo_{jogador_id}", 1))
        cursor.execute("UPDATE jogadores SET presente = 1, a_partir_do_jogo = ? WHERE id = ?", (a_partir_do_jogo, jogador_id))

    conn.commit()
    conn.close()
    return redirect(url_for('confirmar_presenca'))


@app.route('/confirmar_presenca')
def confirmar_presenca():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, posicao_1, posicao_2, pontos, a_partir_do_jogo
        FROM jogadores
        WHERE presente = 1
        ORDER BY nome
    """)
    todos_presentes = cursor.fetchall()
    conn.close()

    if not todos_presentes:
        return "Nenhum jogador presente no momento."

    # 1) Embaralha todos (ordem base do sorteio)
    random.shuffle(todos_presentes)

    # 2) Prepara lista de resultado com slots vazios (None)
    n = len(todos_presentes)
    result = [None] * n

    # função auxiliar: calcula intervalo de slots para "a partir do jogo X"
    def bloco_range(a_partir):
        start = (a_partir - 1) * 16
        end = start + 16
        # limitar ao tamanho da lista
        return range(start, min(end, n))

    # 3) Percorre a lista embaralhada e insere cada jogador no primeiro slot
    #    livre do bloco correspondente. Se o bloco estiver cheio, coloca no
    #    primeiro slot livre após o bloco.
    for jogador in todos_presentes:
        a_partir = int(jogador[5]) if jogador[5] and isinstance(jogador[5], int) else 1
        placed = False

        # tenta colocar dentro do bloco desejado (preserva ordem do shuffle)
        for i in bloco_range(a_partir):
            if i < n and result[i] is None:
                result[i] = jogador
                placed = True
                break

        # se não foi possível (bloco cheio ou índices fora), coloca no primeiro
        # slot livre depois do fim do bloco
        if not placed:
            # posição inicial para busca: fim do bloco
            pos = (a_partir - 1) * 16 + 16
            if pos >= n:
                pos = 0  # se bloco inicial muito alto, varre desde o começo
            # varre circularmente procurando slot livre
            for j in range(pos, pos + n):
                idx = j % n
                if result[idx] is None:
                    result[idx] = jogador
                    placed = True
                    break

        # por segurança, se não colocado (caso raro), anexa ao final (deveria não ocorrer)
        if not placed:
            for idx in range(n):
                if result[idx] is None:
                    result[idx] = jogador
                    placed = True
                    break

    # 4) Remove eventuais None (se houver) e monta lista final mantendo ordem
    jogadores_presentes_ajustados = [j for j in result if j is not None]

    # 5) Guarda na sessão e inicializa estados
    session['jogadores_presentes'] = jogadores_presentes_ajustados
    session['ordem_inicial'] = [j[1] for j in jogadores_presentes_ajustados]
    session['ordem_usados'] = []
    session['jogos'] = []
    session['jogo_extra_confirmados'] = []

    return redirect(url_for('formar_todos_os_jogos'))


@app.route('/formar_todos_os_jogos')
def formar_todos_os_jogos():
    jogadores = session.get('jogadores_presentes', [])
    jogos = []
    grupo_restante = jogadores.copy()
    jogo_atual = 1

    while True:
        elegiveis = [j for j in grupo_restante if j[5] <= jogo_atual]
        if len(elegiveis) < 16:
            break

        grupo = elegiveis[:16]
        time_azul, time_branco, total_azul, total_branco, ids_usados = distribuir_times(grupo)

        jogos.append({
            'time_azul': time_azul,
            'time_branco': time_branco,
            'total_azul': total_azul,
            'total_branco': total_branco
        })

        grupo_restante = [j for j in grupo_restante if j[0] not in ids_usados]
        jogo_atual += 1

    session['jogos'] = jogos
    session['restantes'] = grupo_restante

    return redirect(url_for('mostrar_resultado'))


@app.route('/mostrar_resultado')
def mostrar_resultado():
    return render_template('sorteio_resultado.html',
                           ordem=session.get('ordem_inicial', []),
                           jogos=session.get('jogos', []),
                           jogadores_restantes=session.get('restantes', []))


@app.route('/formar_proximo_jogo')
def formar_proximo_jogo():
    todos_presentes = session.get('jogadores_presentes', [])
    ordem = session.get('ordem_inicial', [])
    usados = session.get('ordem_usados', [])
    confirmados = session.get('jogo_extra_confirmados', [])
    restantes = session.get('restantes', [])

    disponiveis = confirmados + [j for j in restantes if j[1] not in usados]

    if len(disponiveis) < 16:
        for nome in ordem:
            if nome not in usados and nome not in [j[1] for j in confirmados]:
                session['proximo_para_perguntar'] = nome
                return redirect(url_for('confirmar_jogo_extra'))

        return "Não há jogadores suficientes para formar um novo jogo."

    grupo = disponiveis[:16]
    time_azul, time_branco, total_azul, total_branco, ids_usados = distribuir_times(grupo)

    novo_jogo = {
        'time_azul': time_azul,
        'time_branco': time_branco,
        'total_azul': total_azul,
        'total_branco': total_branco
    }

    session['jogos'].append(novo_jogo)

    for jogador in grupo:
        if jogador[1] not in usados:
            usados.append(jogador[1])

    session['ordem_usados'] = usados
    session['jogo_extra_confirmados'] = []
    session['restantes'] = [j for j in restantes if j[0] not in ids_usados]

    return redirect(url_for('mostrar_resultado'))


@app.route('/confirmar_jogo_extra')
def confirmar_jogo_extra():
    jogador = session.get('proximo_para_perguntar')
    if not jogador:
        return redirect(url_for('mostrar_resultado'))
    return render_template('confirmar_jogo_extra.html', jogador=jogador)


@app.route('/responder_jogo_extra', methods=['POST'])
def responder_jogo_extra():
    resposta = request.form.get('resposta')
    jogador = session.get('proximo_para_perguntar')
    confirmados = session.get('jogo_extra_confirmados', [])
    usados = session.get('ordem_usados', [])

    usados.append(jogador)
    if resposta == 'sim':
        for j in session.get('jogadores_presentes', []):
            if j[1] == jogador:
                confirmados.append(j)
                break

    session['jogo_extra_confirmados'] = confirmados
    session['ordem_usados'] = usados
    session.pop('proximo_para_perguntar', None)

    return redirect(url_for('formar_proximo_jogo'))


@app.route('/adicionar_atrasado', methods=['GET', 'POST'])
def adicionar_atrasado():
    if request.method == 'POST':
        ids_selecionados = request.form.getlist('jogadores_atrasados')
        restantes = session.get('restantes', [])

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        placeholders = ','.join('?' for _ in ids_selecionados)
        cursor.execute(f"""
            SELECT id, nome, posicao_1, posicao_2, pontos, a_partir_do_jogo
            FROM jogadores
            WHERE id IN ({placeholders})
        """, ids_selecionados)
        jogadores_atrasados = cursor.fetchall()

        cursor.executemany("""
            UPDATE jogadores
            SET presente = 1, a_partir_do_jogo = 1
            WHERE id = ?
        """, [(j[0],) for j in jogadores_atrasados])

        conn.commit()
        conn.close()

        restantes.extend(jogadores_atrasados)
        session['restantes'] = restantes

        return redirect(url_for('mostrar_resultado'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM jogadores WHERE presente = 0")
    jogadores = cursor.fetchall()
    conn.close()

    return render_template('adicionar_atrasado.html', jogadores=jogadores)


@app.route('/torneio', methods=['POST'])
def torneio():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT nome, posicao_1, posicao_2, pontos FROM jogadores WHERE presente = 1")
    jogadores = c.fetchall()
    conn.close()

    from distribuicao_times import distribuir_times_4

    times = distribuir_times_4(jogadores)  # retorna dict com titulares e reservas

    return render_template(
        "torneio.html",
        times=times,
        enumerate=enumerate  # disponibiliza enumerate no template
    )

import webbrowser
import threading
import time

def abrir_navegador():
    """Abre o navegador automaticamente após o servidor iniciar."""
    time.sleep(1)  # pequena pausa para garantir que o Flask iniciou
    webbrowser.open("http://127.0.0.1:5000")

from flask import request
import os
import signal

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Encerra o servidor Flask e fecha o navegador."""
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        # fallback para encerrar o processo quando for .exe
        os.kill(os.getpid(), signal.SIGINT)
        return "Servidor encerrado."
    func()
    return "Servidor encerrado com sucesso."

if __name__ == '__main__':
    # Inicia uma thread que abrirá o navegador em paralelo
    threading.Thread(target=abrir_navegador).start()

    # Inicia o servidor Flask normalmente
    app.run(debug=False)



