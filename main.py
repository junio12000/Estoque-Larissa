import flet as ft
import pg8000.dbapi as psycopg2

# ==========================================
# 1. FUNÇÃO DE CONEXÃO
# ==========================================
def conectar_banco():
    return psycopg2.connect(
        host="db.xrneftgkfboveqxpzmve.supabase.co",
        port="5432",
        database="postgres",
        user="postgres",
        password="27032016MateusJúnio!"
    )

# ==========================================
# 2. FUNÇÃO PARA CONSULTAR PERFUMES
# ==========================================
def consultar_perfumes():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT codigo, nome, quantidade FROM perfumes ORDER BY nome")
    dados = cursor.fetchall()
    conexao.close()
    return dados

# ==========================================
# 3. CONSTRUÇÃO DA TELA (FLET)
# ==========================================
def main(page: ft.Page):
    page.title = "Estoque Larissa 🌸"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 400
    page.window_height = 600

    # Campos de Cadastro
    txt_codigo = ft.TextField(label="🏷️ Código do Perfume")
    txt_nome = ft.TextField(label="🌸 Nome do Perfume")
    txt_quantidade = ft.TextField(label="📦 Quantidade Inicial", keyboard_type=ft.KeyboardType.NUMBER)
    lbl_mensagem = ft.Text(value="", size=16, weight=ft.FontWeight.BOLD)

    # Tabela de Consulta
    tabela_estoque = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Cód")),
            ft.DataColumn(ft.Text("Nome")),
            ft.DataColumn(ft.Text("Qtd")),
        ],
        rows=[]
    )

    # Função de Salvar
    def botao_salvar_clicado(e):
        if not txt_codigo.value or not txt_nome.value or not txt_quantidade.value:
            lbl_mensagem.value = "⚠️ Preencha tudo!"
            lbl_mensagem.color = ft.Colors.RED
        else:
            try:
                conexao = conectar_banco()
                cursor = conexao.cursor()
                cursor.execute(
                    "INSERT INTO perfumes (codigo, nome, quantidade) VALUES (%s, %s, %s)",
                    (txt_codigo.value, txt_nome.value, int(txt_quantidade.value))
                )
                conexao.commit()
                conexao.close()
                lbl_mensagem.value = f"✅ '{txt_nome.value}' salvo!"
                lbl_mensagem.color = ft.Colors.GREEN
                txt_codigo.value = txt_nome.value = txt_quantidade.value = ""
            except Exception as erro:
                lbl_mensagem.value = "❌ Erro ao salvar."
                print(erro)
        page.update()

    # Função de Carregar Tabela
    def carregar_tabela(e):
        perfumes = consultar_perfumes()
        tabela_estoque.rows.clear()
        for p in perfumes:
            tabela_estoque.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p[0])),
                    ft.DataCell(ft.Text(p[1])),
                    ft.DataCell(ft.Text(str(p[2])))
                ])
            )
        page.update()

    btn_salvar = ft.ElevatedButton("Cadastrar Perfume", on_click=botao_salvar_clicado, bgcolor=ft.Colors.PINK_400, color=ft.Colors.WHITE)

    # Layout com Abas
    page.add(
        ft.Text("Estoque Larissa 🌸", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.PINK_600),
        ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Cadastrar", content=ft.Column([
                    ft.Container(height=10),
                    txt_codigo, txt_nome, txt_quantidade, btn_salvar, lbl_mensagem
                ])),
                ft.Tab(text="Consultar", content=ft.Column([
                    ft.Container(height=10),
                    ft.ElevatedButton("Atualizar Lista", on_click=carregar_tabela),
                    tabela_estoque
                ]))
            ]
        )
    )

ft.app(target=main)
