def fmt_data(dt):
    if not dt: return '-'
    return dt.strftime('%d/%m/%Y %H:%M:%S')

def fmt_duracao(segundos):
    if segundos is None: return '-'
    return f'{int(segundos)}s'

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import session

from app.db.connection import Database
from app.services.raia_service import *
from app.services.cartao_service import *
from app.services.quadro_service import *
from app.services.usuario_service import *
from app.services.usuariocartao_service import *
from app.services.usuarioquadro_service import *


app = Flask(
    __name__,
    template_folder='app/templates',
    static_folder='app/static'
)

app.secret_key = "teste"

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        usuario = UsuarioService().obter_usuario_por_email(email)
        if usuario and usuario.senha == senha:
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            return redirect(url_for('projetos'))
        return render_template('login.html')
    return render_template('login.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        sobrenome = request.form.get('sobrenome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmar = request.form.get('confirmar', '')
        if senha != confirmar:
            return render_template('cadastro.html')
        nome_completo = f"{nome} {sobrenome}".strip() if nome or sobrenome else ''
        if nome_completo and email and senha:
            usuario = UsuarioService().criar_usuario(nome=nome_completo, email=email, senha=senha)
            if usuario:
                session['usuario_id'] = usuario.id
                return redirect(url_for('projetos'))
        return render_template('cadastro.html')
    return render_template('cadastro.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.errorhandler(404)
def pagina_nao_encontrada(error):
    return redirect(url_for('login'))


# ──────────────────────────────────────────────
# PROJETOS
# ──────────────────────────────────────────────

@app.route('/projetos')
def projetos():
    usuario_id = session.get('usuario_id')
    if usuario_id:
        usuario = UsuarioService().obter_usuario(usuario_id)
        if usuario:
            session['usuario_nome'] = usuario.nome
    quadros_raw = QuadroService().listar_quadros_por_usuario(usuario_id)
    quadros = []
    for q in quadros_raw:
        quadros.append({
            'id': q.id,
            'nome': q.nome,
            'empresa': q.descricao or '',
            'cor': None,
            'tag': 'Dev',
            'progresso': 0,
            'concluidas': 0,
            'total': 0,
        })

    workspaces_padrao = [
        {'nome': 'NovaTech', 'sigla': 'N', 'cor': '#7c3aed', 'descricao': 'Workspace de tecnologia'},
        {'nome': 'DesignLab', 'sigla': 'D', 'cor': '#ec4899', 'descricao': 'Workspace de design'},
        {'nome': 'Pessoal', 'sigla': 'P', 'cor': '#10b981', 'descricao': 'Workspace pessoal'},
    ]
    db = Database()
    workspaces = []
    for ws in workspaces_padrao:
        db.cursor.execute("SELECT COUNT(*) FROM QUADRO WHERE DESCRICAO = %s", (ws['nome'],))
        num_boards = db.cursor.fetchone()[0]
        db.cursor.execute("SELECT ID_QUADRO FROM QUADRO WHERE DESCRICAO = %s LIMIT 1", (ws['nome'],))
        row = db.cursor.fetchone()
        db.cursor.execute("""
            SELECT COUNT(DISTINCT UQ.ID_USUARIO)
            FROM USUARIO_QUADRO UQ
            JOIN QUADRO Q ON Q.ID_QUADRO = UQ.ID_QUADRO
            WHERE Q.DESCRICAO = %s
        """, (ws['nome'],))
        num_membros = db.cursor.fetchone()[0]
        workspaces.append({
            'nome': ws['nome'],
            'sigla': ws['sigla'],
            'descricao': ws['descricao'],
            'cor': ws['cor'],
            'cor_btn': '',
            'cor_btn_texto': '',
            'plano': 'Free',
            'num_boards': num_boards,
            'num_membros': num_membros,
            'membros': [],
            'quadro_principal_id': row[0] if row else None,
        })
    db.close()
    return render_template('projetos.html', quadros=quadros, workspaces=workspaces)

@app.route('/quadro/novo', methods=['POST'])
def criar_quadro():
    nome = request.form.get('nome')
    descricao = request.form.get('empresa', '')
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return redirect(url_for('projetos'))
    quadro = QuadroService().criar_quadro(nome, descricao, datetime.now())
    if not quadro:
        return redirect(url_for('projetos'))
    quadro_id = quadro.id
    associar_usuario_quadro(usuario_id, quadro_id, tipo_acesso='DONO', data_associacao=datetime.now())
    col_wip = {'A FAZER': 10, 'FAZENDO': 5, 'FEITO': 10}
    db = Database()
    for nome_col in ['A FAZER', 'FAZENDO', 'FEITO']:
        db.cursor.execute("INSERT INTO COLUNA (NOME, ID_QUADRO, QTD_MAX) VALUES (%s, %s, %s)", (nome_col, quadro_id, col_wip[nome_col]))
    db.cursor.execute("INSERT INTO RAIA (QTD_MAX, NOME, ID_QUADRO, ORDEM) VALUES (10, 'Geral', %s, 0)", (quadro_id,))
    db.commit()
    db.close()
    return redirect(url_for('kanban', quadro_id=quadro_id))

@app.route('/quadro/<int:quadro_id>/excluir', methods=['POST'])
def excluir_quadro(quadro_id):
    db = Database()
    db.cursor.execute("DELETE FROM USUARIO_CARTAO WHERE ID_CARTAO IN (SELECT C.ID_CARTAO FROM CARTAO C JOIN RAIA R ON R.ID_RAIA = C.ID_RAIA WHERE R.ID_QUADRO = %s)", (quadro_id,))
    db.cursor.execute("DELETE FROM CARTAO WHERE ID_RAIA IN (SELECT ID_RAIA FROM RAIA WHERE ID_QUADRO = %s)", (quadro_id,))
    db.cursor.execute("DELETE FROM RAIA WHERE ID_QUADRO = %s", (quadro_id,))
    db.cursor.execute("DELETE FROM USUARIO_QUADRO WHERE ID_QUADRO = %s", (quadro_id,))
    db.commit()
    db.close()
    QuadroService().deletar_quadro(quadro_id)
    return redirect(url_for('projetos'))

@app.route('/quadro/<int:quadro_id>/editar', methods=['POST'])
def editar_quadro(quadro_id):
    nome = request.form.get('nome', '').strip()
    empresa = request.form.get('empresa', '')
    db = Database()
    if nome:
        db.cursor.execute(
            "UPDATE QUADRO SET NOME = %s, DESCRICAO = %s WHERE ID_QUADRO = %s",
            (nome, empresa, quadro_id)
        )
        db.commit()
    db.close()
    return redirect(url_for('kanban', quadro_id=quadro_id))


# ──────────────────────────────────────────────
# KANBAN
# ──────────────────────────────────────────────

@app.route('/kanban/<int:quadro_id>')
def kanban(quadro_id):
    usuario_id = session.get('usuario_id')
    if usuario_id:
        usuario = UsuarioService().obter_usuario(usuario_id)
        if usuario:
            session['usuario_nome'] = usuario.nome
    quadro_raw = QuadroService().obter_quadro(quadro_id)
    if not quadro_raw:
        return redirect(url_for('projetos'))
    mapa_cor_workspace = {
        'NovaTech': '#7c3aed',
        'DesignLab': '#ec4899',
        'Pessoal': '#10b981',
    }
    ws_empresa = quadro_raw.descricao or ''
    quadro = {
        'id': quadro_raw.id,
        'nome': quadro_raw.nome,
        'empresa': ws_empresa,
        'cor': mapa_cor_workspace.get(ws_empresa, '#8b5cf6'),
    }

    membros = []
    cores = ['#f59e0b', '#7c3aed', '#ec4899', '#14b8a6', '#3b82f6', '#22c55e', '#ef4444', '#8b5cf6']
    for i, u in enumerate(UsuarioService().listar_usuarios()):
        iniciais = ''.join(p[0].upper() for p in u.nome.split() if p)[:2]
        membros.append({
            'id': u.id,
            'nome': u.nome,
            'iniciais': iniciais,
            'cor': cores[i % len(cores)],
        })

    db = Database()
    db.cursor.execute(
        "SELECT UC.ID_CARTAO, UC.ID_USUARIO, U.NOME FROM USUARIO_CARTAO UC JOIN USUARIO U ON U.ID_USUARIO = UC.ID_USUARIO"
    )
    resp_map = {}
    for rc_id_cartao, rc_id_usuario, rc_nome in db.cursor.fetchall():
        rc_iniciais = ''.join(p[0].upper() for p in rc_nome.split() if p)[:2]
        rc_cor = '#7c3aed'
        for m in membros:
            if m['id'] == rc_id_usuario:
                rc_cor = m['cor']
                break
        resp_map[rc_id_cartao] = {
            'id': rc_id_usuario,
            'iniciais': rc_iniciais,
            'cor': rc_cor,
        }

    db.cursor.execute("SELECT ID_COLUNA, NOME, QTD_MAX FROM COLUNA WHERE ID_QUADRO = %s ORDER BY ID_COLUNA", (quadro_id,))
    coluna_cores = {'A FAZER': '#a78bfa', 'FAZENDO': '#3b82f6', 'FEITO': '#10b981'}
    colunas = [{'id': r[0], 'nome': r[1], 'cor': coluna_cores.get(r[1], '#a78bfa'), 'qtd_max': r[2]} for r in db.cursor.fetchall()]

    swimlanes_raw = RaiaService.listar_raias_por_quadro(quadro_id)

    agora = datetime.now()

    db.cursor.execute("""
        SELECT C.ID_CARTAO, C.NOME, C.DATA_FINAL, C.PRIORIDADE, C.DESCRICAO,
               C.DATA_CRIACAO, C.DATA_ENTRADA_FAZENDO, C.DATA_ENTRADA_FEITO,
               C.ID_RAIA, C.ID_COLUNA, C.ORDEM
        FROM CARTAO C
        WHERE C.ID_RAIA IN (SELECT ID_RAIA FROM RAIA WHERE ID_QUADRO = %s)
        ORDER BY C.ORDEM, C.ID_CARTAO
    """, (quadro_id,))

    cards_by_raia = {}
    for sw in swimlanes_raw:
        cards_by_raia[sw.id] = {col['id']: [] for col in colunas}

    for row in db.cursor.fetchall():
        cid, nome, data_final, prio, desc, criacao, ent_faz, ent_feito, rid, cid_col, ordem = row
        if rid not in cards_by_raia:
            cards_by_raia[rid] = {col['id']: [] for col in colunas}
        if cid_col not in cards_by_raia[rid]:
            cid_col = colunas[0]['id']
        resp = resp_map.get(cid, {'id': None, 'iniciais': '?', 'cor': '#7c3aed'})

        # Métricas por card baseadas no nome da coluna (via id_coluna)
        col_nome = ''
        for c in colunas:
            if c['id'] == cid_col:
                col_nome = c['nome'].lower()
                break
        em_feito = 'feito' in col_nome
        em_fazendo = 'fazendo' in col_nome
        iniciou = ent_faz is not None or em_fazendo
        concluiu = ent_feito is not None or em_feito

        lead_seg = None
        feito_end = ent_feito or (agora if em_feito else None)
        if feito_end and criacao:
            lead_seg = (feito_end - criacao).total_seconds()

        cycle_seg = None
        if ent_faz:
            ciclo_fim = ent_feito or (agora if em_fazendo else None)
            if ciclo_fim:
                cycle_seg = (ciclo_fim - ent_faz).total_seconds()
        elif concluiu and not ent_faz:
            ciclo_fim = ent_feito or (agora if em_feito else None)
            if ciclo_fim and criacao:
                cycle_seg = (ciclo_fim - criacao).total_seconds()

        card_dict = {
            'id': cid,
            'titulo': nome,
            'prazo': data_final.strftime('%Y-%m-%d') if data_final else '',
            'prioridade': prio or 'Media',
            'cor': None,
            'tags': [],
            'descricao': desc or '',
            'responsavel_id': resp['id'],
            'responsavel_iniciais': resp['iniciais'],
            'responsavel_cor': resp['cor'],
            'id_coluna': cid_col,
            'id_raia': rid,
            'criado_em': fmt_data(criacao),
            'iniciado_em': fmt_data(ent_faz),
            'concluido_em': fmt_data(ent_feito),
            'lead_time': int(lead_seg) if lead_seg else None,
            'lead_time_str': fmt_duracao(lead_seg),
            'cycle_time': int(cycle_seg) if cycle_seg else None,
            'cycle_time_str': fmt_duracao(cycle_seg),
        }
        cards_by_raia[rid][cid_col].append(card_dict)

    db.close()

    # Construir estrutura de swimlanes para o template
    swimlanes = []
    for sw in swimlanes_raw:
        celulas = cards_by_raia.get(sw.id, {col['id']: [] for col in colunas})
        swimlanes.append({
            'id': sw.id,
            'nome': sw.nome,
            'qtd_max': sw.qtd_max,
            'celulas': celulas,
        })

    return render_template('kanban.html', quadro=quadro, colunas=colunas, swimlanes=swimlanes, membros=membros)


# ──────────────────────────────────────────────
# SWIMLANES (RAIA) CRUD
# ──────────────────────────────────────────────

@app.route('/quadro/<int:quadro_id>/raia/nova', methods=['POST'])
def criar_raia(quadro_id):
    nome = request.form.get('nome', '').strip()
    if not nome:
        return redirect(url_for('kanban', quadro_id=quadro_id))
    prox_ordem = RaiaService.obter_proxima_ordem(quadro_id)
    RaiaService.criar_raia(10, nome, quadro_id, ordem=prox_ordem)
    return redirect(url_for('kanban', quadro_id=quadro_id))

@app.route('/raia/<int:raia_id>/excluir', methods=['POST'])
def excluir_raia(raia_id):
    raia = RaiaService.obter_raia(raia_id)
    if not raia:
        return redirect(url_for('projetos'))
    quadro_id = raia.id_quadro
    total = RaiaService.contar_raias_por_quadro(quadro_id)
    if total <= 1:
        return redirect(url_for('kanban', quadro_id=quadro_id))
    db = Database()
    db.cursor.execute("SELECT ID_CARTAO FROM CARTAO WHERE ID_RAIA = %s", (raia_id,))
    tem_cartoes = db.cursor.fetchone() is not None
    if tem_cartoes:
        db.cursor.execute("SELECT ID_RAIA FROM RAIA WHERE ID_QUADRO = %s AND ID_RAIA != %s ORDER BY ORDEM LIMIT 1", (quadro_id, raia_id))
        dest = db.cursor.fetchone()
        if dest:
            db.cursor.execute("UPDATE CARTAO SET ID_RAIA = %s WHERE ID_RAIA = %s", (dest[0], raia_id))
    db.cursor.execute("DELETE FROM RAIA WHERE ID_RAIA = %s", (raia_id,))
    db.commit()
    db.close()
    return redirect(url_for('kanban', quadro_id=quadro_id))

@app.route('/raia/<int:raia_id>/editar', methods=['POST'])
def editar_raia(raia_id):
    raia = RaiaService.obter_raia(raia_id)
    if not raia:
        return redirect(url_for('projetos'))
    quadro_id = raia.id_quadro
    nome = request.form.get('nome')
    if nome:
        RaiaService.atualizar_raia(raia_id, nome=nome)
    return redirect(url_for('kanban', quadro_id=quadro_id))


# ──────────────────────────────────────────────
# COLUNA WIP LIMIT
# ──────────────────────────────────────────────

@app.route('/coluna/<int:coluna_id>/wip', methods=['POST'])
def atualizar_wip_coluna(coluna_id):
    qtd_max = request.form.get('qtd_max', type=int)
    db = Database()
    db.cursor.execute("SELECT ID_QUADRO FROM COLUNA WHERE ID_COLUNA = %s", (coluna_id,))
    row = db.cursor.fetchone()
    if not row:
        db.close()
        return redirect(url_for('projetos'))
    quadro_id = row[0]
    if qtd_max and qtd_max > 0:
        db.cursor.execute("UPDATE COLUNA SET QTD_MAX = %s WHERE ID_COLUNA = %s", (qtd_max, coluna_id))
    db.commit()
    db.close()
    return redirect(url_for('kanban', quadro_id=quadro_id))


# ──────────────────────────────────────────────
# CARTÕES (JSON)
# ──────────────────────────────────────────────

@app.route('/cartao/criar', methods=['POST'])
def criar_cartao():
    d = request.get_json()
    usuario_id = session.get('usuario_id')
    coluna_id = d.get('coluna_id')
    raia_id = d.get('raia_id')
    if not coluna_id or not raia_id:
        return jsonify({'ok': False, 'erro': 'coluna_id e raia_id obrigatorios'})

    db = Database()
    col_nome = None
    db.cursor.execute("SELECT NOME, QTD_MAX FROM COLUNA WHERE ID_COLUNA = %s", (coluna_id,))
    rowc = db.cursor.fetchone()
    if rowc:
        col_nome = rowc[0]
        qtd_max_col = rowc[1]
        if qtd_max_col is not None:
            db.cursor.execute("SELECT COUNT(*) FROM CARTAO WHERE ID_COLUNA = %s", (coluna_id,))
            count_atual = db.cursor.fetchone()[0]
            if count_atual >= qtd_max_col:
                db.close()
                return jsonify({'ok': False, 'erro': f'WIP limit de {qtd_max_col} atingido no {col_nome}'})
    db.close()

    db = Database()
    db.cursor.execute("""
        INSERT INTO CARTAO (DATA_INICIO, DATA_FINAL, DATA_CRIACAO, NOME, ORDEM, ID_RAIA, ID_COLUNA, DESCRICAO, PRIORIDADE, ID_USUARIO)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING ID_CARTAO
    """, (d.get('prazo'), d.get('prazo'), datetime.now(), d['titulo'], 0, raia_id, coluna_id,
          d.get('descricao', ''), d.get('prioridade', 'Media'), usuario_id))
    cartao_id = db.cursor.fetchone()[0]

    if col_nome:
        nc = col_nome.lower()
        if 'fazendo' in nc:
            db.cursor.execute("UPDATE CARTAO SET DATA_ENTRADA_FAZENDO = NOW() WHERE ID_CARTAO = %s", (cartao_id,))
        if 'feito' in nc:
            db.cursor.execute("UPDATE CARTAO SET DATA_ENTRADA_FEITO = NOW() WHERE ID_CARTAO = %s", (cartao_id,))
    db.commit()
    db.close()

    responsavel_id = d.get('responsavel_id') or usuario_id
    if responsavel_id:
        db2 = Database()
        db2.cursor.execute(
            "INSERT INTO USUARIO_CARTAO (ID_USUARIO, ID_CARTAO, TIPO_ACESSO) VALUES (%s, %s, %s)",
            (responsavel_id, cartao_id, 'DONO')
        )
        db2.cursor.execute("SELECT ID_QUADRO FROM RAIA WHERE ID_RAIA = %s", (raia_id,))
        row_raia = db2.cursor.fetchone()
        if row_raia:
            qid = row_raia[0]
            db2.cursor.execute("SELECT 1 FROM USUARIO_QUADRO WHERE ID_USUARIO = %s AND ID_QUADRO = %s", (responsavel_id, qid))
            if not db2.cursor.fetchone():
                db2.cursor.execute("INSERT INTO USUARIO_QUADRO (ID_USUARIO, ID_QUADRO, TIPO_ACESSO) VALUES (%s, %s, %s)", (responsavel_id, qid, 'EDITOR'))
        db2.commit()
        db2.close()
        return jsonify({'ok': True, 'id': cartao_id})
    return jsonify({'ok': False, 'id': None})

@app.route('/cartao/<int:cartao_id>/editar', methods=['POST'])
def editar_cartao(cartao_id):
    d = request.get_json()
    db = Database()

    updates = []
    params = []
    if d.get('titulo'):
        updates.append("NOME = %s"); params.append(d['titulo'])
    if 'prazo' in d:
        updates.append("DATA_FINAL = %s"); params.append(d['prazo'])
    if 'descricao' in d:
        updates.append("DESCRICAO = %s"); params.append(d.get('descricao', ''))
    if 'prioridade' in d:
        updates.append("PRIORIDADE = %s"); params.append(d['prioridade'])

    nova_coluna_id = d.get('coluna_id')
    if nova_coluna_id:
        updates.append("ID_COLUNA = %s"); params.append(nova_coluna_id)

    nova_raia_id = d.get('raia_id')
    if nova_raia_id:
        updates.append("ID_RAIA = %s"); params.append(nova_raia_id)

    if nova_coluna_id:
        db.cursor.execute("SELECT NOME, QTD_MAX FROM COLUNA WHERE ID_COLUNA = %s", (nova_coluna_id,))
        rowc = db.cursor.fetchone()
        if rowc and rowc[1] is not None:
            col_nome, qtd_max = rowc
            db.cursor.execute("SELECT COUNT(*) FROM CARTAO WHERE ID_COLUNA = %s AND ID_CARTAO != %s", (nova_coluna_id, cartao_id))
            count_atual = db.cursor.fetchone()[0]
            if count_atual >= qtd_max:
                db.close()
                return jsonify({'ok': False, 'erro': f'WIP limit de {qtd_max} atingido no {col_nome}'})

    if updates:
        params.append(cartao_id)
        db.cursor.execute(f"UPDATE CARTAO SET {', '.join(updates)} WHERE ID_CARTAO = %s", params)

    # Atualizar timestamps com base no nome da coluna
    col_id_atual = nova_coluna_id or None
    if col_id_atual:
        db.cursor.execute("SELECT NOME FROM COLUNA WHERE ID_COLUNA = %s", (col_id_atual,))
        row_col = db.cursor.fetchone()
        if row_col:
            nc = row_col[0].lower()
            if 'fazendo' in nc:
                db.cursor.execute("UPDATE CARTAO SET DATA_ENTRADA_FAZENDO = COALESCE(DATA_ENTRADA_FAZENDO, NOW()) WHERE ID_CARTAO = %s", (cartao_id,))
            if 'feito' in nc:
                db.cursor.execute("UPDATE CARTAO SET DATA_ENTRADA_FEITO = COALESCE(DATA_ENTRADA_FEITO, NOW()) WHERE ID_CARTAO = %s", (cartao_id,))

    db.commit()

    responsavel_id = d.get('responsavel_id')
    if responsavel_id:
        db.cursor.execute("DELETE FROM USUARIO_CARTAO WHERE ID_CARTAO = %s", (cartao_id,))
        db.cursor.execute("INSERT INTO USUARIO_CARTAO (ID_USUARIO, ID_CARTAO, TIPO_ACESSO) VALUES (%s, %s, %s)", (responsavel_id, cartao_id, 'DONO'))
        db.cursor.execute("SELECT ID_QUADRO FROM RAIA WHERE ID_RAIA = (SELECT ID_RAIA FROM CARTAO WHERE ID_CARTAO = %s)", (cartao_id,))
        row_raia = db.cursor.fetchone()
        if row_raia:
            qid = row_raia[0]
            db.cursor.execute("SELECT 1 FROM USUARIO_QUADRO WHERE ID_USUARIO = %s AND ID_QUADRO = %s", (responsavel_id, qid))
            if not db.cursor.fetchone():
                db.cursor.execute("INSERT INTO USUARIO_QUADRO (ID_USUARIO, ID_QUADRO, TIPO_ACESSO) VALUES (%s, %s, %s)", (responsavel_id, qid, 'EDITOR'))
        db.commit()
    db.close()
    return jsonify({'ok': True})

@app.route('/cartao/<int:cartao_id>/excluir', methods=['POST'])
def excluir_cartao(cartao_id):
    ok = CartaoService.deletar_cartao(cartao_id)
    return jsonify({'ok': ok})

@app.route('/cartao/<int:cartao_id>/mover', methods=['POST'])
def mover_cartao(cartao_id):
    d = request.get_json()
    db = Database()

    coluna_id = d.get('coluna_id')
    raia_id = d.get('raia_id')

    if coluna_id:
        db.cursor.execute("SELECT NOME FROM COLUNA WHERE ID_COLUNA = %s", (coluna_id,))
        rowc = db.cursor.fetchone()
        if rowc:
            nc = rowc[0].lower()
            if 'fazendo' in nc:
                db.cursor.execute("UPDATE CARTAO SET DATA_ENTRADA_FAZENDO = COALESCE(DATA_ENTRADA_FAZENDO, NOW()) WHERE ID_CARTAO = %s", (cartao_id,))
            if 'feito' in nc:
                db.cursor.execute("UPDATE CARTAO SET DATA_ENTRADA_FEITO = COALESCE(DATA_ENTRADA_FEITO, NOW()) WHERE ID_CARTAO = %s", (cartao_id,))
        db.cursor.execute("UPDATE CARTAO SET ID_COLUNA = %s WHERE ID_CARTAO = %s", (coluna_id, cartao_id))

    if raia_id:
        db.cursor.execute("SELECT QTD_MAX FROM RAIA WHERE ID_RAIA = %s", (raia_id,))
        row_wip = db.cursor.fetchone()
        if row_wip and row_wip[0] is not None:
            qtd_max = row_wip[0]
            db.cursor.execute("SELECT COUNT(*) FROM CARTAO WHERE ID_RAIA = %s AND ID_CARTAO != %s", (raia_id, cartao_id))
            count_atual = db.cursor.fetchone()[0]
            if count_atual >= qtd_max:
                db.close()
                return jsonify({'ok': False, 'erro': 'WIP limit atingido na swimlane de destino'})
        db.cursor.execute("UPDATE CARTAO SET ID_RAIA = %s WHERE ID_CARTAO = %s", (raia_id, cartao_id))

    db.commit()
    db.close()
    return jsonify({'ok': True})

@app.route('/api/metricas/<int:quadro_id>')
def metricas_quadro(quadro_id):
    try:
        db = Database()
        # WIP: cartoes na coluna FAZENDO
        db.cursor.execute("""
            SELECT COUNT(*) FROM CARTAO C
            JOIN COLUNA CL ON CL.ID_COLUNA = C.ID_COLUNA
            WHERE CL.ID_QUADRO = %s AND LOWER(CL.NOME) LIKE '%%fazendo%%'
        """, (quadro_id,))
        row = db.cursor.fetchone()
        wip = row[0] if row else 0

        db.cursor.execute("""
            SELECT COUNT(*) FROM CARTAO C
            JOIN COLUNA CL ON CL.ID_COLUNA = C.ID_COLUNA
            WHERE CL.ID_QUADRO = %s AND LOWER(CL.NOME) LIKE '%%feito%%'
        """, (quadro_id,))
        row = db.cursor.fetchone()
        concluidos = row[0] if row else 0

        db.cursor.execute("""
            SELECT COUNT(*) FROM QUADRO Q
            JOIN RAIA R ON R.ID_QUADRO = Q.ID_QUADRO
            JOIN CARTAO C ON C.ID_RAIA = R.ID_RAIA
            WHERE Q.ID_QUADRO = %s
        """, (quadro_id,))
        row = db.cursor.fetchone()
        total = row[0] if row else 0

        db.cursor.execute("""
            SELECT
                CASE
                    WHEN COUNT(*) > 0 AND MIN(C.DATA_ENTRADA_FEITO) IS NOT NULL
                    THEN COUNT(*)::float / GREATEST(EXTRACT(EPOCH FROM (MAX(C.DATA_ENTRADA_FEITO) - MIN(C.DATA_ENTRADA_FEITO))) / 86400, 1)
                    ELSE 0
                END
            FROM CARTAO C
            JOIN COLUNA CL ON CL.ID_COLUNA = C.ID_COLUNA
            WHERE CL.ID_QUADRO = %s AND C.DATA_ENTRADA_FEITO IS NOT NULL
        """, (quadro_id,))
        row = db.cursor.fetchone()
        throughput = round(row[0], 2) if row else 0

        db.close()
        return jsonify({
            'wip': wip,
            'throughput': throughput,
            'concluidos': concluidos,
            'total': total,
        })
    except Exception as e:
        print(f"Erro metricas: {e}")
        return jsonify({'wip': 0, 'throughput': 0, 'concluidos': 0, 'total': 0})


if __name__ == '__main__':
    app.run(debug=True)
