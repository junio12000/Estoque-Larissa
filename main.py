import flet as ft
import psycopg2

# ==========================================
# 1. FUNÇÃO DE CONEXÃO COM A NUVEM
# ==========================================
def conectar_banco():
    return psycopg2.connect(
        host="db.xrneftgkfboveqxpzmve.supabase.co",
        port="5432",
        database="postgres",
        user="postgres",
        password="27032016MateusJúnio!"  # <-- Coloque sua senha real aqui!
    )

# ==========================================
# 2. CONSTRUÇÃO DA TELA DO APP (FLET)
# ==========================================
def main(page: ft.Page):
    # Configurações da tela do aplicativo
    page.title = "Estoque Larissa 🌸"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 400   # Formato exato de tela de celular
    page.window_height = 600

    # Caixas de texto
    txt_codigo = ft.TextField(label="🏷️ Código do Perfume")
    txt_nome = ft.TextField(label="🌸 Nome do Perfume")
    txt_quantidade = ft.TextField(label="📦 Quantidade Inicial", keyboard_type=ft.KeyboardType.NUMBER)
    
    lbl_mensagem = ft.Text(value="", size=16, weight=ft.FontWeight.BOLD)

    # Função que roda ao clicar em Salvar
    def botao_salvar_clicado(e):
        if not txt_codigo.value or not txt_nome.value or not txt_quantidade.value:
            lbl_mensagem.value = "⚠️ Preencha todos os campos!"
            lbl_mensagem.color = ft.Colors.RED
            page.update()
            return
        
        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()
            
            cursor.execute(
                "INSERT INTO perfumes (codigo, nome, quantidade) VALUES (%s, %s, %s)",
                (txt_codigo.value, txt_nome.value, int(txt_quantidade.value))
            )
            conexao.commit()
            conexao.close()

            lbl_mensagem.value = f"✅ Perfume '{txt_nome.value}' salvo na nuvem!"
            lbl_mensagem.color = ft.Colors.GREEN
            txt_codigo.value = ""
            txt_nome.value = ""
            txt_quantidade.value = ""
            
        except Exception as erro:
            lbl_mensagem.value = "❌ Erro ao salvar (Esse código já existe?)"
            lbl_mensagem.color = ft.Colors.RED
            print(f"Erro detalhado: {erro}")
            
        page.update()

    # Botão principal blindado com content=ft.Text()
    btn_salvar = ft.ElevatedButton(
        content=ft.Text("Cadastrar Perfume", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        on_click=botao_salvar_clicado,
        bgcolor=ft.Colors.PINK_400,
        width=360,
        height=50
    )

    # Adicionando tudo na tela em ordem vertical
    page.add(
        ft.Text("🌸 Cadastro de Estoque", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.PINK_600),
        ft.Divider(),
        txt_codigo,
        txt_nome,
        txt_quantidade,
        ft.Container(height=10),
        btn_salvar,
        lbl_mensagem
    )

ft.app(target=main)