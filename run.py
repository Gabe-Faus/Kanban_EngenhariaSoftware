import os
import time
from app.services.usuario_service import UsuarioService
from app.services.quadro_service import QuadroService
from app.services.raia_service import RaiaService
from app.services.cartao_service import CartaoService
from app.services.usuarioquadro_service import criar_quadro_com_usuario
from datetime import datetime, date


def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')


def pressione_enter():
    input('\nPressione Enter para voltar ao menu...')
    limpar_tela()


def mostrar_temporario(texto, segundos=1.5):
    print(texto)
    time.sleep(segundos)
    limpar_tela()


def prompt_int(prompt_text, default=None):
    try:
        val = input(f"{prompt_text}")
        if val == "" and default is not None:
            return default
        return int(val)
    except Exception:
        return None


def prompt_str(prompt_text, default=None):
    val = input(f"{prompt_text}")
    if val == "" and default is not None:
        return default
    return val


if __name__ == "__main__":
    qs = QuadroService()
    rs = RaiaService
    cs = CartaoService
    us = UsuarioService()

    limpar_tela()

    while True:
        print('=== KANBAN CLI ===')
        print('1) Listar todos os quadros')
        print('2) Listar quadros por usuário')
        print('3) Criar novo quadro (e associar usuário)')
        print('4) Ver detalhes do quadro (raias e cartões)')
        print('5) Criar raia (swimlane)')
        print('6) Criar cartão')
        print('7) Sair')

        choice = input('Escolha uma opção: ').strip()

        if choice == '1':
            quadros = qs.listar_quadros()
            if not quadros:
                print('Nenhum quadro encontrado.')
            else:
                print('\nQuadros encontrados:')
                for q in quadros:
                    print(f" - {q.id}: {q.nome} ({q.descricao})")
            pressione_enter()

        elif choice == '2':
            uid = prompt_int('Digite o id do usuário: ')
            if uid is None:
                print('Id de usuário inválido.')
                pressione_enter()
                continue
            quadros = qs.listar_quadros_por_usuario(uid)
            if not quadros:
                print('Nenhum quadro encontrado para esse usuário.')
            else:
                print(f'\nQuadros do usuário {uid}:')
                for q in quadros:
                    print(f" - {q.id}: {q.nome} ({q.descricao})")
            pressione_enter()

        elif choice == '3':
            uid = prompt_int('Digite o id do usuário proprietário: ')
            if uid is None:
                print('Id de usuário inválido.')
                pressione_enter()
                continue
            nome = prompt_str('Nome do quadro: ')
            descricao = prompt_str('Descrição (opcional): ', default='')
            resultado = criar_quadro_com_usuario(uid, nome, descricao, datetime.now(), tipo_acesso='DONO')
            if resultado:
                mostrar_temporario('✅ Quadro criado e usuário associado com sucesso!')
            else:
                mostrar_temporario('✗ Falha ao criar o quadro.')

        elif choice == '4':
            qid = prompt_int('Digite o id do quadro: ')
            if qid is None:
                print('Id de quadro inválido.')
                pressione_enter()
                continue
            quadro = qs.obter_quadro(qid)
            if not quadro:
                print('Quadro não encontrado.')
                pressione_enter()
                continue
            print(f"\nQuadro {quadro.id}: {quadro.nome}\nDescrição: {quadro.descricao}")
            raiais = rs.listar_raias_por_quadro(quadro.id)
            if not raiais:
                print(' Nenhuma raia encontrada.')
            else:
                for r in raiais:
                    print(f"\n Raia {r.id}: {r.nome} (qtd_max={r.qtd_max})")
                    cartoes = cs.listar_cartoes_por_raia(r.id)
                    if not cartoes:
                        print('   Nenhum cartão nesta raia.')
                    else:
                        for c in cartoes:
                            print(f"   Cartão {c.id}: {c.nome} (ordem={c.ordem}) - {c.descricao}")
            pressione_enter()

        elif choice == '5':
            qid = prompt_int('Digite o id do quadro: ')
            if qid is None:
                print('Id de quadro inválido.')
                pressione_enter()
                continue
            nome = prompt_str('Nome da raia: ')
            qtd = prompt_int('Qtd máxima (int): ')
            if qtd is None:
                print('Quantidade máxima inválida.')
                pressione_enter()
                continue
            r = rs.criar_raia(qtd, nome, qid)
            if r:
                mostrar_temporario(f'✅ Raia criada com id {r.id}.')
            else:
                mostrar_temporario('✗ Falha ao criar a raia.')

        elif choice == '6':
            rid = prompt_int('Digite o id da raia: ')
            if rid is None:
                print('Id de raia inválido.')
                pressione_enter()
                continue
            nome = prompt_str('Nome do cartão: ')
            descricao = prompt_str('Descrição (opcional): ', default='')
            ordem = prompt_int('Ordem (int, padrão 0): ', default=0)
            start = date.today()
            end = date.today()
            c = cs.criar_cartao(start, end, datetime.now(), nome, ordem, rid, None, descricao)
            if c:
                mostrar_temporario(f'✅ Cartão criado com id {c.id}.')
            else:
                mostrar_temporario('✗ Falha ao criar o cartão.')

        elif choice == '7':
            mostrar_temporario('Saindo... Até mais!', segundos=1.2)
            break

        else:
            print('Opção desconhecida.')
            pressione_enter()