import flet as ft
import pg8000.dbapi as psycopg2
from datetime import datetime, timedelta

def conectar_banco():
    return psycopg2.connect(
        host="db.xrneftgkfboveqxpzmve.supabase.co",
        port=5432,
        database="postgres",
        user="postgres",
        password="27032016MateusJúnio!"
    )

def main(page: ft.Page):
    page.title = "Controle de Estoque e Perfumaria"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = ft.Colors.WHITE

    container_principal = ft.Container(expand=True)
    page.add(container_principal)

    def tela_padrao(conteudo, com_cartao=True, largura=360):
        meio = ft.Container(
            content=conteudo, 
            bgcolor=ft.Colors.WHITE80 if com_cartao else ft.Colors.TRANSPARENT, 
            padding=20, 
            border_radius=15, 
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12) if com_cartao else None, 
            width=largura
        )
        
        # A SOLUÇÃO DEFINITIVA:
        # left, right, top e bottom = 0 (Amarrado nas 4 bordas para sumir com o fundo branco)
        # fit="fill" (Amassa/Estica a imagem para não dar zoom gigante)
        return ft.Stack([
            ft.Image(src="fundo.jpg", fit="fill", opacity=0.85, left=0, right=0, top=0, bottom=0),
            ft.Container(content=meio, alignment=ft.Alignment(0, 0), padding=10, left=0, right=0, top=0, bottom=0)
        ], expand=True)

    def navegar(conteudo, com_cartao=True, largura=360):
        container_principal.content = tela_padrao(conteudo, com_cartao, largura)
        page.update()

    # --- FUNÇÕES DE LÓGICA ---
    def mostrar_consulta(e=None):
        conn = conectar_banco(); cursor = conn.cursor()
        cursor.execute("SELECT codigo, nome, quantidade, preco_venda FROM perfumes"); perf = cursor.fetchall(); conn.close()
        tabela = ft.DataTable(columns=[ft.DataColumn(ft.Text("Código")), ft.DataColumn(ft.Text("Nome")), ft.DataColumn(ft.Text("Qtd")), ft.DataColumn(ft.Text("Valor"))], rows=[])
        for p in perf: 
            tabela.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(str(p[0]))), ft.DataCell(ft.Text(p[1])), ft.DataCell(ft.Text(str(p[2]))), ft.DataCell(ft.Text(f"R$ {p[3]:.2f}"))]))
        
        conteudo = ft.Column([ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), ft.Text("📦 Estoque Atual", size=18, weight="bold"), tabela], scroll=ft.ScrollMode.AUTO)
        navegar(conteudo, largura=420)

    def mostrar_cadastro(e=None):
        c, n, q, pc, pv = ft.TextField(label="Código"), ft.TextField(label="Nome"), ft.TextField(label="Qtd Inicial"), ft.TextField(label="Compra R$"), ft.TextField(label="Venda R$")
        def salvar(e):
            conn = conectar_banco(); cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO perfumes (codigo, nome, quantidade, preco_compra, preco_venda, data_cadastro) 
                VALUES (%s, %s, %s, %s, %s, CURRENT_DATE) 
                ON CONFLICT (codigo) DO UPDATE SET 
                quantidade = perfumes.quantidade + EXCLUDED.quantidade,
                preco_compra = EXCLUDED.preco_compra,
                preco_venda = EXCLUDED.preco_venda
            """, (c.value, n.value, int(q.value), float(pc.value), float(pv.value)))
            cursor.execute("INSERT INTO registro_entradas (codigo_perfume, quantidade_lancada) VALUES (%s, %s)", (c.value, int(q.value)))
            conn.commit(); conn.close(); mostrar_menu()
        
        conteudo = ft.Column([ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), c, n, q, pc, pv, ft.ElevatedButton("Salvar/Lançar Estoque", on_click=salvar)], scroll=ft.ScrollMode.AUTO)
        navegar(conteudo)

    def mostrar_saidas(e=None):
        conn = conectar_banco(); cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM clientes"); clientes = cursor.fetchall(); conn.close()
        cod = ft.TextField(label="Cód Perfume"); qtd = ft.TextField(label="Qtd", value="1")
        forma = ft.Dropdown(options=[ft.dropdown.Option("Pix"), ft.dropdown.Option("Dinheiro"), ft.dropdown.Option("Cartão"), ft.dropdown.Option("A prazo")], value="Pix")
        parcelas = ft.Dropdown(label="Parcelas (Se A prazo)", options=[ft.dropdown.Option(str(i)) for i in range(1, 5)], value="1")
        cliente = ft.Dropdown(options=[ft.dropdown.Option(str(c[0]), c[1]) for c in clientes])
        
        def realizar(e):
            conn = conectar_banco()
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT preco_venda, quantidade FROM perfumes WHERE codigo = %s FOR UPDATE", (cod.value,))
                resultado = cursor.fetchone()
                
                if not resultado:
                    tela_erro = ft.Column([ft.Text("❌ PRODUTO NÃO ENCONTRADO", color="red", weight="bold"), ft.ElevatedButton("Tentar Novamente", on_click=mostrar_saidas)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    container_principal.content = tela_padrao(tela_erro)
                    page.update()
                    return

                preco, estoque_atual = resultado
                qtd_venda = int(qtd.value)

                if estoque_atual < qtd_venda:
                    tela_erro = ft.Column([
                        ft.Text("❌ ESTOQUE INSUFICIENTE", size=20, weight="bold", color="red"),
                        ft.Text(f"Você tentou vender {qtd_venda}, mas só tem {estoque_atual} disponíveis."),
                        ft.ElevatedButton("Voltar", on_click=mostrar_saidas)
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    container_principal.content = tela_padrao(tela_erro)
                    page.update()
                    return

                total = preco * qtd_venda
                cursor.execute("UPDATE perfumes SET quantidade = quantidade - %s WHERE codigo = %s", (qtd_venda, cod.value))
                cursor.execute("INSERT INTO caixa (descricao, valor, forma_pagamento) VALUES (%s, %s, %s)", (f"Venda {cod.value}", total, forma.value))
                
                if forma.value == "A prazo" and cliente.value:
                    num_parc = int(parcelas.value)
                    valor_parc = total / num_parc
                    for i in range(1, num_parc + 1):
                        vencimento = datetime.now() + timedelta(days=30 * i)
                        cursor.execute("INSERT INTO parcelas (id_cliente, valor_parcela, data_vencimento, num_parcela, total_parcelas) VALUES (%s, %s, %s, %s, %s)", 
                                    (cliente.value, valor_parc, vencimento.date(), i, num_parc))
                    cursor.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + %s WHERE id = %s", (total, cliente.value))
                
                conn.commit()
                mostrar_menu()
                
            except Exception as ex:
                print(f"ERRO: {ex}")
                conn.rollback()
            finally:
                conn.close()

        conteudo = ft.Column([ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), cod, qtd, forma, parcelas, cliente, ft.ElevatedButton("Confirmar", on_click=realizar)], scroll=ft.ScrollMode.AUTO)
        navegar(conteudo)

    # --- FUNÇÕES DE LISTAS E CLIENTES ---
    def mostrar_lista_clientes(e=None):
        conn = conectar_banco(); cursor = conn.cursor()
        cursor.execute("SELECT id, nome, saldo_devedor FROM clientes"); clientes = cursor.fetchall(); conn.close()
        tabela = ft.DataTable(columns=[ft.DataColumn(ft.Text("Nome")), ft.DataColumn(ft.Text("Dívida")), ft.DataColumn(ft.Text("Pag."))], rows=[])
        for c in clientes:
            tabela.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(c[1])), ft.DataCell(ft.Text(f"R$ {c[2]:.2f}")),
                ft.DataCell(ft.IconButton(ft.Icons.MONETIZATION_ON, icon_color="green", on_click=lambda e, cid=c[0], val=float(c[2]): mostrar_tela_pagamento(cid, val)))
            ]))
        conteudo = ft.Column([ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), tabela], scroll=ft.ScrollMode.AUTO)
        navegar(conteudo)

    def mostrar_tela_pagamento(id_cliente, divida_atual):
        valor_pago = ft.TextField(label="Valor Pago R$")
        def confirmar(e):
            pago = float(valor_pago.value.replace(',', '.'))
            conn = conectar_banco(); cursor = conn.cursor()
            cursor.execute("UPDATE clientes SET saldo_devedor = saldo_devedor - %s WHERE id = %s", (pago, id_cliente))
            cursor.execute("INSERT INTO caixa (descricao, valor, forma_pagamento) VALUES (%s, %s, 'Pagto Parcial')", (f"Pagto Cliente #{id_cliente}", pago))
            conn.commit(); conn.close(); mostrar_lista_clientes()
        navegar(ft.Column([ft.Text(f"Dívida Atual: R$ {divida_atual:.2f}"), valor_pago, ft.ElevatedButton("Confirmar", on_click=confirmar), ft.TextButton("Voltar", on_click=mostrar_lista_clientes)]))

    def mostrar_caixa(e=None):
        conn = conectar_banco(); cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM caixa"); total_vendido = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM caixa WHERE forma_pagamento NOT IN ('Fiado', 'A prazo')"); saldo = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(saldo_devedor), 0) FROM clientes"); total_a_receber = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM caixa WHERE forma_pagamento = 'Pagto Parcial'"); total_pago_clientes = cursor.fetchone()[0]
        conn.close()
        conteudo = ft.Column([
            ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), 
            ft.Text("📊 Resumo Financeiro", size=20, weight="bold"), 
            ft.Text(f"🛒 Total Geral: R$ {total_vendido:.2f}"), 
            ft.Text(f"💰 Saldo Efetivo: R$ {saldo:.2f}"), 
            ft.Text(f"✅ Pago pelos Clientes: R$ {total_pago_clientes:.2f}"), 
            ft.Text(f"📋 Saldo Devedor: R$ {total_a_receber:.2f}", color="red")
        ], scroll=ft.ScrollMode.AUTO)
        navegar(conteudo)

    def mostrar_cadastro_cliente(e=None):
        n, t = ft.TextField(label="Nome"), ft.TextField(label="Telefone")
        def salvar(e):
            conn = conectar_banco(); cursor = conn.cursor()
            cursor.execute("INSERT INTO clientes (nome, telefone, saldo_devedor) VALUES (%s, %s, 0)", (n.value, t.value))
            conn.commit(); conn.close(); mostrar_menu()
        navegar(ft.Column([ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), n, t, ft.ElevatedButton("Salvar", on_click=salvar)], scroll=ft.ScrollMode.AUTO))

    # --- MENU PRINCIPAL ---
    def mostrar_menu(e=None):
        menu = ft.Column([
            ft.ElevatedButton("🌸 Cadastrar Perfume", on_click=mostrar_cadastro, width=280, height=50),
            ft.ElevatedButton("📦 Consultar Estoque", on_click=mostrar_consulta, width=280, height=50),
            ft.ElevatedButton("🛒 Registrar Venda", on_click=mostrar_saidas, width=280, height=50),
            ft.ElevatedButton("👤 Cadastrar Cliente", on_click=mostrar_cadastro_cliente, width=280, height=50),
            ft.ElevatedButton("👥 Listar Clientes", on_click=mostrar_lista_clientes, width=280, height=50),
            ft.ElevatedButton("💰 Fluxo de Caixa", on_click=mostrar_caixa, width=280, height=50),
        ], 
        spacing=15, 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER, # Centraliza os botões entre si
        alignment=ft.MainAxisAlignment.CENTER # Mantém todo o bloco de botões centralizado na tela
        )
        
        navegar(menu, com_cartao=False)

    mostrar_menu()

if __name__ == "__main__":
    ft.app(target=main, assets_dir=".")
