import flet as ft
import pg8000.dbapi as psycopg2

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
    page.spacing = 0
    page.bgcolor = ft.Colors.WHITE

    # container_principal evita a tela branca ao trocar de função
    container_principal = ft.Container(expand=True)
    page.add(container_principal)

    def tela_padrao(conteudo_interno, com_cartao=True, largura=360):
        meio = ft.Container(
            content=conteudo_interno,
            bgcolor=ft.Colors.WHITE70,
            padding=20,
            border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
            width=largura if com_cartao else 280
        )
        return ft.Stack(controls=[
            ft.Image(src="fundo.jpg", fit="cover", opacity=0.85, expand=True),
            ft.Container(content=meio, alignment=ft.Alignment(-0.85, 0), padding=20)
        ], expand=True)

    def navegar_para(conteudo):
        container_principal.content = conteudo
        page.update()

    # --- MENU PRINCIPAL ---
    def mostrar_menu(e=None):
        menu = ft.Column([
            ft.ElevatedButton("🌸 Cadastrar Perfume", on_click=lambda _: mostrar_cadastro(), width=250),
            ft.ElevatedButton("📦 Consultar Estoque", on_click=lambda _: mostrar_consulta(), width=250),
            ft.ElevatedButton("🛒 Registrar Venda", on_click=lambda _: mostrar_saidas(), width=250),
            ft.ElevatedButton("👤 Cadastrar Cliente", on_click=lambda _: mostrar_cadastro_cliente(), width=250),
            ft.ElevatedButton("👥 Listar Clientes", on_click=lambda _: mostrar_lista_clientes(), width=250),
            ft.ElevatedButton("💰 Fluxo de Caixa", on_click=lambda _: mostrar_caixa(), width=250),
        ], horizontal_alignment="start", tight=True, spacing=15)
        navegar_para(tela_padrao(menu, com_cartao=False))

    # --- FLUXO DE CAIXA ---
    def mostrar_caixa():
        conn = conectar_banco(); cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM caixa WHERE forma_pagamento NOT IN ('Fiado', 'A prazo')")
        saldo = cursor.fetchone()[0]; conn.close()
        conteudo = ft.Column([ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), ft.Text(f"Saldo em Caixa: R$ {saldo:.2f}", size=18, weight="bold")], tight=True)
        navegar_para(tela_padrao(conteudo))

    # --- VENDAS ---
    def mostrar_saidas():
        conn = conectar_banco(); cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM clientes"); clientes = cursor.fetchall(); conn.close()
        cod = ft.TextField(label="Cód Perfume")
        qtd = ft.TextField(label="Qtd", value="1")
        forma = ft.Dropdown(options=[ft.dropdown.Option("Pix"), ft.dropdown.Option("Dinheiro"), ft.dropdown.Option("A prazo")], value="Pix")
        cliente = ft.Dropdown(options=[ft.dropdown.Option(str(c[0]), c[1]) for c in clientes])
        
        def realizar(e):
            conn = conectar_banco(); cursor = conn.cursor()
            cursor.execute("SELECT preco_venda FROM perfumes WHERE codigo = %s", (cod.value,))
            preco = cursor.fetchone()[0]
            total = preco * int(qtd.value)
            cursor.execute("INSERT INTO caixa (descricao, valor, forma_pagamento) VALUES (%s, %s, %s)", (f"Venda {cod.value}", total, forma.value))
            if forma.value == "A prazo": cursor.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + %s WHERE id = %s", (total, cliente.value))
            conn.commit(); conn.close(); mostrar_menu()
        
        navegar_para(tela_padrao(ft.Column([ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), cod, qtd, forma, cliente, ft.ElevatedButton("Confirmar", on_click=realizar)])))

    # --- CADASTROS E LISTAS ---
    def mostrar_cadastro():
        c, n, q, pc, pv = ft.TextField(label="Código"), ft.TextField(label="Nome"), ft.TextField(label="Qtd"), ft.TextField(label="Compra R$"), ft.TextField(label="Venda R$")
        def salvar(e):
            conn = conectar_banco(); cursor = conn.cursor()
            cursor.execute("INSERT INTO perfumes (codigo, nome, quantidade, preco_compra, preco_venda) VALUES (%s, %s, %s, %s, %s)", (c.value, n.value, int(q.value), float(pc.value), float(pv.value)))
            conn.commit(); conn.close(); mostrar_menu()
        navegar_para(tela_padrao(ft.Column([ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), c, n, q, pc, pv, ft.ElevatedButton("Salvar", on_click=salvar)])))

    def mostrar_consulta():
        conn = conectar_banco(); cursor = conn.cursor()
        cursor.execute("SELECT codigo, nome, preco_venda FROM perfumes"); perf = cursor.fetchall(); conn.close()
        tabela = ft.DataTable(columns=[ft.DataColumn(ft.Text("Cód")), ft.DataColumn(ft.Text("Nome")), ft.DataColumn(ft.Text("R$ Venda"))], rows=[])
        for p in perf: tabela.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(p[0])), ft.DataCell(ft.Text(p[1])), ft.DataCell(ft.Text(f"R$ {p[2]:.2f}"))]))
        navegar_para(tela_padrao(ft.Column([ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), tabela])))

    def mostrar_cadastro_cliente():
        n, t = ft.TextField(label="Nome"), ft.TextField(label="Telefone")
        def salvar(e):
            conn = conectar_banco(); cursor = conn.cursor()
            cursor.execute("INSERT INTO clientes (nome, telefone, saldo_devedor) VALUES (%s, %s, 0)", (n.value, t.value))
            conn.commit(); conn.close(); mostrar_menu()
        navegar_para(tela_padrao(ft.Column([ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), n, t, ft.ElevatedButton("Salvar", on_click=salvar)])))

    def mostrar_lista_clientes():
        conn = conectar_banco(); cursor = conn.cursor()
        cursor.execute("SELECT nome, saldo_devedor FROM clientes"); clientes = cursor.fetchall(); conn.close()
        tabela = ft.DataTable(columns=[ft.DataColumn(ft.Text("Nome")), ft.DataColumn(ft.Text("Dívida R$"))], rows=[])
        for c in clientes: tabela.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(c[0])), ft.DataCell(ft.Text(f"R$ {c[1]:.2f}"))]))
        navegar_para(tela_padrao(ft.Column([ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), tabela])))

    mostrar_menu()

if __name__ == "__main__":
    ft.app(target=main, assets_dir=".")
