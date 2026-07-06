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

def consultar_perfumes():
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, nome, quantidade, preco_venda FROM perfumes ORDER BY nome")
        dados = cursor.fetchall()
        cursor.close(); conn.close()
        return dados
    except Exception as e:
        print(f"Erro no banco: {e}")
        return []

def main(page: ft.Page):
    page.title = "Controle de Estoque, Vendas e Perfumaria"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    page.bgcolor = ft.Colors.WHITE

    def tela_padrao(conteudo_interno, com_cartao=True, largura=360):
        if com_cartao:
            meio = ft.Container(
                content=conteudo_interno,
                bgcolor=ft.Colors.WHITE70,
                padding=20,
                border_radius=15,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
                width=largura
            )
        else:
            meio = ft.Container(content=conteudo_interno, width=280)

        return ft.Stack(controls=[
            ft.Image(src="fundo.jpg", fit="cover", opacity=0.85, expand=True),
            ft.Container(content=meio, alignment=ft.Alignment(-0.85, 0), padding=20)
        ], expand=True)

    # --- MENU PRINCIPAL ---
    def mostrar_menu(e=None):
        page.controls.clear()
        menu = ft.Column([
            ft.ElevatedButton("🌸 Cadastrar Perfume", on_click=mostrar_cadastro, width=250),
            ft.ElevatedButton("📦 Consultar Estoque", on_click=mostrar_consulta, width=250),
            ft.ElevatedButton("🛒 Registrar Venda/Saída", on_click=mostrar_saidas, width=250),
            ft.ElevatedButton("👤 Cadastrar Cliente", on_click=mostrar_cadastro_cliente, width=250),
            ft.ElevatedButton("👥 Listar Clientes", on_click=mostrar_lista_clientes, width=250),
            ft.ElevatedButton("💰 Fluxo de Caixa", on_click=mostrar_caixa, width=250),
        ], horizontal_alignment="start", tight=True, spacing=12)
        
        page.add(tela_padrao(menu, com_cartao=False))
        page.update()

    # --- FLUXO DE CAIXA ---
    def mostrar_caixa(e=None):
        page.controls.clear()
        conn = conectar_banco()
        cursor = conn.cursor()
        # Ignora tanto 'A prazo' quanto registros antigos de 'Fiado'
        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM caixa WHERE forma_pagamento NOT IN ('Fiado', 'A prazo')")
        saldo_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT descricao, valor, forma_pagamento FROM caixa ORDER BY id DESC LIMIT 5")
        ultimas = cursor.fetchall()
        conn.close()

        tabela = ft.DataTable(columns=[ft.DataColumn(ft.Text("Descrição")), ft.DataColumn(ft.Text("Valor")), ft.DataColumn(ft.Text("Pagamento"))], rows=[], column_spacing=12)
        for u in ultimas:
            tabela.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(u[0][:15])), ft.DataCell(ft.Text(f"R$ {u[1]:.2f}")), ft.DataCell(ft.Text(u[2]))]))

        conteudo = ft.Column([
            ft.TextButton("⬅️ Voltar ao Menu", on_click=mostrar_menu),
            ft.Container(
                content=ft.Column([
                    ft.Text("Saldo Total em Caixa:", size=14, color=ft.Colors.BLACK54),
                    ft.Text(f"R$ {saldo_total:,.2f}".replace('.', '_').replace(',', '.').replace('_', ','), size=24, weight="bold", color=ft.Colors.GREEN_700)
                ]),
                bgcolor=ft.Colors.GREEN_50, padding=15, border_radius=10, width=320
            ),
            ft.Text("Últimas Movimentações:", size=16, weight="bold"),
            tabela
        ], horizontal_alignment="start", tight=True)

        page.add(tela_padrao(conteudo, com_cartao=True, largura=380))
        page.update()

    # --- ESTOQUE ---
    def mostrar_consulta(e=None):
        page.controls.clear()
        tabela = ft.DataTable(
            columns=[ft.DataColumn(ft.Text("Cód")), ft.DataColumn(ft.Text("Nome")), ft.DataColumn(ft.Text("Qtd")), ft.DataColumn(ft.Text("R$ Venda"))], 
            rows=[], column_spacing=12
        )
        for p in consultar_perfumes():
            tabela.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(p[0]))), ft.DataCell(ft.Text(p[1])), 
                ft.DataCell(ft.Text(str(p[2]))), ft.DataCell(ft.Text(f"R$ {p[3]:.2f}" if p[3] else "R$ 0,00"))
            ]))
        
        conteudo = ft.Column([
            ft.TextButton("⬅️ Voltar ao Menu", on_click=mostrar_menu), 
            ft.Text("📦 Estoque Atual", size=18, weight="bold"),
            tabela
        ], horizontal_alignment="start", tight=True)
        
        page.add(tela_padrao(conteudo, com_cartao=True, largura=360))
        page.update()

    def mostrar_cadastro(e=None):
        page.controls.clear()
        txt_c = ft.TextField(label="🏷️ Código", width=300)
        txt_n = ft.TextField(label="🌸 Nome", width=300)
        txt_q = ft.TextField(label="🔢 Quantidade", width=300)
        txt_compra = ft.TextField(label="💵 Preço de Compra (Ex: 85.50)", width=300)
        txt_venda = ft.TextField(label="💰 Preço de Venda (Ex: 150.00)", width=300)
        
        def salvar(e):
            if txt_c.value and txt_n.value and txt_q.value:
                try:
                    pc = float(txt_compra.value.replace(',', '.')) if txt_compra.value else 0.0
                    pv = float(txt_venda.value.replace(',', '.')) if txt_venda.value else 0.0
                    
                    conn = conectar_banco()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO perfumes (codigo, nome, quantidade, preco_compra, preco_venda) VALUES (%s, %s, %s, %s, %s)", 
                        (txt_c.value, txt_n.value, int(txt_q.value), pc, pv)
                    )
                    conn.commit(); conn.close()
                    mostrar_menu()
                except Exception as err:
                    print(f"Erro ao salvar: {err}")
                
        conteudo = ft.Column([
            ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), 
            ft.Text("Cadastrar Perfume", size=18, weight="bold"),
            txt_c, txt_n, txt_q, txt_compra, txt_venda,
            ft.ElevatedButton("Salvar", on_click=salvar, bgcolor=ft.Colors.BLUE_600, color="white")
        ], horizontal_alignment="start", tight=True)
        
        page.add(tela_padrao(conteudo, com_cartao=True, largura=360))
        page.update()

    # --- REGISTRAR VENDA ---
    def mostrar_saidas(e=None):
        page.controls.clear()
        
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM clientes ORDER BY nome")
        clientes_db = cursor.fetchall()
        conn.close()

        opcoes_clientes = [ft.dropdown.Option(str(c[0]), f"#{c[0]} - {c[1]}") for c in clientes_db]

        txt_cod = ft.TextField(label="🏷️ Código do Perfume", width=300)
        txt_qtd = ft.TextField(label="➖ Quantidade", width=300, value="1")
        
        forma_pagto = ft.Dropdown(
            label="💳 Forma de Pagamento", width=300,
            options=[
                ft.dropdown.Option("Pix"), ft.dropdown.Option("Dinheiro"), 
                ft.dropdown.Option("Cartão"), ft.dropdown.Option("A prazo")
            ], value="Pix"
        )
        
        dd_cliente = ft.Dropdown(
            label="👤 Selecione o Cliente (Se for A prazo)", 
            width=300,
            options=opcoes_clientes
        )
        
        def realizar(e):
            if txt_cod.value and txt_qtd.value:
                try:
                    qtd = int(txt_qtd.value)
                    conn = conectar_banco()
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT nome, preco_venda FROM perfumes WHERE codigo = %s", (txt_cod.value,))
                    perfume = cursor.fetchone()
                    
                    if perfume:
                        nome_perfume, preco_unit = perfume[0], perfume[1]
                        valor_total = float(preco_unit or 0) * qtd
                        
                        # 1. Abate do estoque
                        cursor.execute("UPDATE perfumes SET quantidade = quantidade - %s WHERE codigo = %s", (qtd, txt_cod.value))
                        
                        # 2. Lança no Caixa
                        cursor.execute(
                            "INSERT INTO caixa (descricao, valor, forma_pagamento) VALUES (%s, %s, %s)",
                            (f"Venda: {qtd}x {nome_perfume}", valor_total, forma_pagto.value)
                        )
                        
                        # 3. Se for A PRAZO e selecionou o cliente no dropdown
                        if forma_pagto.value == "A prazo" and dd_cliente.value:
                            id_cliente = int(dd_cliente.value)
                            cursor.execute("UPDATE clientes SET saldo_devedor = COALESCE(saldo_devedor, 0) + %s WHERE id = %s", (valor_total, id_cliente))
                        
                        conn.commit()
                    conn.close()
                    mostrar_menu()
                except Exception as err:
                    print(f"Erro na venda: {err}")
                
        conteudo = ft.Column([
            ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), 
            ft.Text("Registrar Venda", size=18, weight="bold"),
            txt_cod, txt_qtd, forma_pagto, dd_cliente,
            ft.ElevatedButton("Confirmar Venda", on_click=realizar, bgcolor=ft.Colors.ORANGE_600, color="white")
        ], horizontal_alignment="start", tight=True)
        
        page.add(tela_padrao(conteudo, com_cartao=True, largura=360))
        page.update()

    # --- CLIENTES ---
    def mostrar_cadastro_cliente(e=None):
        page.controls.clear()
        n = ft.TextField(label="👤 Nome do Cliente", width=300)
        t = ft.TextField(label="📞 Telefone", width=300)
        
        def salvar(e):
            if n.value:
                conn = conectar_banco()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO clientes (nome, telefone, saldo_devedor) VALUES (%s, %s, 0)", (n.value, t.value))
                conn.commit(); conn.close()
                mostrar_menu()
                
        conteudo = ft.Column([
            ft.TextButton("⬅️ Voltar", on_click=mostrar_menu), 
            ft.Text("Cadastrar Cliente", size=18, weight="bold"),
            n, t, 
            ft.ElevatedButton("Salvar", on_click=salvar, bgcolor=ft.Colors.GREEN_600, color="white")
        ], horizontal_alignment="start", tight=True)
        
        page.add(tela_padrao(conteudo, com_cartao=True, largura=360))
        page.update()

    def mostrar_lista_clientes(e=None):
        page.controls.clear()
        
        def quitar_divida(id_cliente, valor_divida):
            if valor_divida > 0:
                conn = conectar_banco()
                cursor = conn.cursor()
                cursor.execute("UPDATE clientes SET saldo_devedor = 0 WHERE id = %s", (id_cliente,))
                cursor.execute("INSERT INTO caixa (descricao, valor, forma_pagamento) VALUES (%s, %s, 'Pagto A prazo')", (f"Pagamento dívida Cliente #{id_cliente}", valor_divida))
                conn.commit(); conn.close()
                mostrar_lista_clientes()

        tabela = ft.DataTable(
            columns=[ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Nome")), ft.DataColumn(ft.Text("Dívida (R$)")), ft.DataColumn(ft.Text("Quitar"))], 
            rows=[], column_spacing=18
        )
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, COALESCE(saldo_devedor, 0) FROM clientes ORDER BY saldo_devedor DESC")
        for c in cursor.fetchall():
            divida = float(c[2])
            cor_divida = ft.Colors.RED_600 if divida > 0 else ft.Colors.BLACK87
            tabela.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(c[0]))), ft.DataCell(ft.Text(c[1])), 
                ft.DataCell(ft.Text(f"R$ {divida:.2f}", color=cor_divida, weight="bold" if divida > 0 else "normal")),
                ft.DataCell(ft.IconButton(ft.Icons.MONETIZATION_ON, icon_color="green" if divida > 0 else "grey", tooltip="Quitar Dívida", on_click=lambda e, cid=c[0], val=divida: quitar_divida(cid, val)))
            ]))
        conn.close()
        
        conteudo = ft.Column([
            ft.TextButton("⬅️ Voltar ao Menu", on_click=mostrar_menu), 
            ft.Text("👥 Lista de Clientes", size=18, weight="bold"),
            tabela
        ], horizontal_alignment="start", tight=True)
        
        page.add(tela_padrao(conteudo, com_cartao=True, largura=360))
        page.update()

    def mostrar_edicao_cliente(id_cliente):
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, telefone FROM clientes WHERE id = %s", (id_cliente,))
        dados = cursor.fetchone()
        conn.close()
        
        nome_input = ft.TextField(label="Nome", value=dados[0], width=300)
        tel_input = ft.TextField(label="Telefone", value=dados[1], width=300)
        
        def salvar_edicao(e):
            conn = conectar_banco()
            cursor = conn.cursor()
            cursor.execute("UPDATE clientes SET nome=%s, telefone=%s WHERE id=%s", (nome_input.value, tel_input.value, id_cliente))
            conn.commit(); conn.close()
            mostrar_lista_clientes()

        conteudo = ft.Column([
            ft.Text("✏️ Editar Cliente", size=18, weight="bold"),
            nome_input, tel_input, 
            ft.Row([
                ft.TextButton("Cancelar", on_click=mostrar_lista_clientes),
                ft.ElevatedButton("Salvar Alterações", on_click=salvar_edicao, bgcolor=ft.Colors.BLUE_600, color="white")
            ], alignment="spaceBetween", width=300)
        ], horizontal_alignment="start", tight=True)

        page.controls.clear()
        page.add(tela_padrao(conteudo, com_cartao=True, largura=360))
        page.update()

    mostrar_menu()

if __name__ == "__main__":
    ft.app(target=main, assets_dir=".")
