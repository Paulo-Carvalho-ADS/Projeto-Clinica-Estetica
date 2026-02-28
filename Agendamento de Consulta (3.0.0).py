import sqlite3
import shutil
import sys
import datetime
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QTabWidget, QFormLayout, QDateEdit,
    QTimeEdit, QComboBox, QMessageBox, QHBoxLayout, QDoubleSpinBox,
    QListWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import QDate, QTime, Qt
from PyQt5.QtGui import QFont

# ---------------- Criação do diretorio de dados ---------------
pasta_documentos = os.path.join(os.path.expanduser("~"), "Documents")

# ---------------- Define o nome da pasta ----------------
pasta_programa = os.path.join(pasta_documentos, "Sistema Clinica Estetica")

# ---------------- Cria a pasta se não existir ----------------
if not os.path.exists(pasta_programa):
    os.makedirs(pasta_programa)

# ---------------- Define o caminho do arquivo de dados ----------------
ARQUIVO_DADOS = os.path.join(pasta_programa, "config.json")

# criar função de conexao segura com o banco de dados
def conectar_banco():
    caminho_documentos = os.path.expanduser("~/Documents")
    pasta_sistema = os.path.join(caminho_documentos, "Sistema Clinica Estetica")
    os.makedirs(pasta_sistema, exist_ok=True)
    caminho_banco = os.path.join(pasta_sistema, "banco_clinica.db")

    conexao = sqlite3.connect(caminho_banco)
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_cliente TEXT NOT NULL,
            servico TEXT NOT NULL,
            valor REAL NOT NULL,
            forma_pagamento TEXT NOT NULL,
            data_hora TEXT NOT NULL
        )
    """)

    conexao.commit()
    return conexao

def fazer_backup_banco():
    try:
        caminho_documentos = os.path.expanduser("~/Documents")
        pasta_sistema = os.path.join(caminho_documentos, "Sistema Clinica Estetica")
        caminho_banco = os.path.join(pasta_sistema, "banco_clinica.db")

        if not os.path.exists(caminho_banco):
            print("Arquivo de banco de dados não encontrado para backup.")
            return False

        pasta_backup = os.path.join(pasta_sistema, "Backups")
        os.makedirs(pasta_backup, exist_ok=True)

        data_atual = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
        nome_arquivo_backup = f"backup_clinica_{data_atual}.db"
        caminho_destino = os.path.join(pasta_backup, nome_arquivo_backup)

        shutil.copy2(caminho_banco, caminho_destino)
        return True
        
    except Exception as e:
        print(f"Erro ao criar backup: {e}")
        return False

# ---------------- CONFIGURAÇÃO E ESTILOS ----------------
DEFAULT_CONFIG = {
    "tema": "light",
    "cores": {
        "light": {
            "cor_fundo": "#F5F6FA", "cor_texto": "#2F3542", "cor_input": "#FFFFFF",
            "cor_borda": "#DCDDE1", "cor_primaria": "#1E90FF", "cor_primaria_hover": "#4682B4", "cor_primaria_press": "#2F3542"
        },
        "dark": {
            "cor_fundo": "#2E3440", "cor_texto": "#D8DEE9", "cor_input": "#3B4252",
            "cor_borda": "#4C566A", "cor_primaria": "#5E81AC", "cor_primaria_hover": "#81A1C1", "cor_primaria_press": "#4C566A"
        }
    }
}

def generate_qss(config, tema):
    cores = config["cores"][tema]
    return f"""
        QWidget {{ background-color: {cores['cor_fundo']}; color: {cores['cor_texto']}; font-size: 14px; font-family: "Segoe UI", sans-serif; }}
        QLineEdit, QComboBox, QDateEdit, QTimeEdit, QDoubleSpinBox {{
            background-color: {cores['cor_input']}; border: 1px solid {cores['cor_borda']}; border-radius: 5px; padding: 5px; color: {cores['cor_texto']};
        }}
        QPushButton {{
            background-color: {cores['cor_primaria']}; border: none; border-radius: 5px; padding: 8px; color: white; font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {cores['cor_primaria_hover']}; }}
        QPushButton:pressed {{ background-color: {cores['cor_primaria_press']}; }}
        QPushButton:disabled {{ background-color: {cores['cor_borda']}; color: #888; }}
        QListWidget {{
            background-color: {cores['cor_input']}; border: 1px solid {cores['cor_borda']}; border-radius: 5px; padding: 5px;
        }}
        QTabWidget::pane {{ border: 1px solid {cores['cor_borda']}; border-radius: 5px; }}
        QTabBar::tab {{ background: {cores['cor_borda']}; color: {cores['cor_texto']}; padding: 8px; border-top-left-radius: 5px; border-top-right-radius: 5px; }}
        QTabBar::tab:selected {{ background: {cores['cor_primaria']}; color: white; font-weight: bold; }}
    """

# ---------------- MODELOS DE DADOS ----------------
class Cliente:
    def __init__(self, nome, telefone):
        self.nome = nome
        self.telefone = telefone
    def __str__(self): return f"{self.nome} ({self.telefone})"
    def to_dict(self): return {"nome": self.nome, "telefone": self.telefone}
    @staticmethod
    def from_dict(data): return Cliente(data["nome"], data["telefone"])

class Servico:
    def __init__(self, nome, valor):
        self.nome = nome
        self.valor = valor
    def __str__(self): return f"{self.nome} (R$ {self.valor:.2f})"
    def to_dict(self): return {"nome": self.nome, "valor": self.valor}
    @staticmethod
    def from_dict(data): return Servico(data["nome"], data["valor"])

class Agendamento:
    def __init__(self, cliente, servico, data_hora, valor, pagamento):
        self.cliente = cliente
        self.servico = servico
        self.data_hora = data_hora
        self.valor = valor
        self.pagamento = pagamento

    def to_dict(self):
        return {
            "cliente": self.cliente.to_dict(),
            "servico": self.servico,
            "data_hora": self.data_hora.strftime("%Y-%m-%d %H:%M"),
            "valor": self.valor,
            "pagamento": self.pagamento,
        }

    @staticmethod
    def from_dict(data):
        cliente = Cliente.from_dict(data["cliente"])
        data_hora = datetime.datetime.strptime(data["data_hora"], "%Y-%m-%d %H:%M")
        return Agendamento(cliente, data["servico"], data_hora, data["valor"], data["pagamento"])

# ---------------- APLICAÇÃO PRINCIPAL ----------------
class ClinicaEsteticaApp(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("Clínica Estética - Agendamento de Consultas")
        self.resize(800, 600)
        
        # Dados e Configurações
        self.clientes = []
        self.agendamentos = []
        self.servicos = []
        self.config = DEFAULT_CONFIG.copy()
        self.current_theme = "light"
        self.indice_agendamento_em_edicao = None 

        self.load_data()
        self.carregar_do_banco()  # Carrega os dados do banco de dados
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Cabeçalho com Botão de Tema
        header_layout = QHBoxLayout()
        header_layout.addStretch(1)
        self.btn_theme = QPushButton("🌙")
        self.btn_theme.setFixedSize(40, 40)
        self.btn_theme.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.btn_theme)
        layout.addLayout(header_layout)

        # Abas
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Aba 1: Clientes e Serviços
        self.tab_clientes = QWidget()
        tabs.addTab(self.tab_clientes, "👥 Clientes e Serviços")
        self.setup_clientes_tab()

        # Aba 2: Agenda
        self.tab_agendamentos = QWidget()
        tabs.addTab(self.tab_agendamentos, "📅 Agenda")
        self.setup_agendamentos_tab()
        
        # --- CORREÇÃO AQUI ---
        # Só chamamos a atualização DEPOIS de criar ambas as abas
        self.atualizar_listas_visuais()

    def closeEvent(self, event):
        print("Iniciando backup automático...")

        sucesso_no_backup = fazer_backup_banco()

        if sucesso_no_backup:
            QMessageBox.information(self, "Encerrando Sistema", "✅ Backup criado com sucesso!")
        else:
            QMessageBox.warning(self, "Aviso de Segurança", "❌ Atenção: Houve uma falha ao realizar o backup automático!\nO programa será fechado, mas verifique o armazenamento do seu computador.")
        
        event.accept()

    # ---------------- LÓGICA DE TEMA ----------------
    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()
        self.save_data()

    def apply_theme(self):
        self.app.setStyleSheet(generate_qss(self.config, self.current_theme))
        if self.current_theme == "light":
            self.btn_theme.setText("🌙") 
        else:
            self.btn_theme.setText("☀️") 

    # ---------------- ABA: CLIENTES E SERVIÇOS ----------------
    def setup_clientes_tab(self):
        layout = QHBoxLayout(self.tab_clientes)

        # Coluna Clientes
        col_clientes = QVBoxLayout()
        col_clientes.addWidget(QLabel("<b>Cadastro de Clientes</b>"))
        
        form_cli = QFormLayout()
        self.input_nome = QLineEdit()
        self.input_telefone = QLineEdit()
        form_cli.addRow("Nome:", self.input_nome)
        form_cli.addRow("Telefone:", self.input_telefone)
        col_clientes.addLayout(form_cli)

        btn_box_cli = QHBoxLayout()
        btn_add_cli = QPushButton("Salvar Cliente")
        btn_add_cli.clicked.connect(self.cadastrar_cliente)
        self.btn_del_cli = QPushButton("Remover")
        self.btn_del_cli.clicked.connect(self.remover_cliente)
        self.btn_del_cli.setEnabled(False)
        btn_box_cli.addWidget(btn_add_cli)
        btn_box_cli.addWidget(self.btn_del_cli)
        col_clientes.addLayout(btn_box_cli)

        self.lista_clientes = QListWidget()
        self.lista_clientes.currentItemChanged.connect(lambda: self.btn_del_cli.setEnabled(True))
        col_clientes.addWidget(self.lista_clientes)
        
        # Coluna Serviços
        col_servicos = QVBoxLayout()
        col_servicos.addWidget(QLabel("<b>Cadastro de Serviços</b>"))

        form_serv = QFormLayout()
        self.input_servico_nome = QLineEdit()
        self.input_servico_valor = QDoubleSpinBox()
        self.input_servico_valor.setMaximum(10000.00)
        self.input_servico_valor.setPrefix("R$ ")
        form_serv.addRow("Serviço:", self.input_servico_nome)
        form_serv.addRow("Valor:", self.input_servico_valor)
        col_servicos.addLayout(form_serv)

        btn_box_serv = QHBoxLayout()
        btn_add_serv = QPushButton("Salvar Serviço")
        btn_add_serv.clicked.connect(self.cadastrar_servico)
        self.btn_del_serv = QPushButton("Remover")
        self.btn_del_serv.clicked.connect(self.remover_servico)
        self.btn_del_serv.setEnabled(False)
        btn_box_serv.addWidget(btn_add_serv)
        btn_box_serv.addWidget(self.btn_del_serv)
        col_servicos.addLayout(btn_box_serv)

        self.lista_servicos = QListWidget()
        self.lista_servicos.currentItemChanged.connect(lambda: self.btn_del_serv.setEnabled(True))
        col_servicos.addWidget(self.lista_servicos)

        layout.addLayout(col_clientes)
        layout.addLayout(col_servicos)
        
        # --- REMOVIDO DAQUI: self.atualizar_listas_visuais() ---

    def cadastrar_cliente(self):
        nome, fone = self.input_nome.text().strip(), self.input_telefone.text().strip()
        if not nome or not fone: return
        
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO clientes (nome, telefone) VALUES (?, ?)", (nome, fone))
        conexao.commit()
        conexao.close()
        
        self.clientes.append(Cliente(nome, fone))
        self.input_nome.clear()
        self.input_telefone.clear()
        
        self.save_and_refresh()

    def remover_cliente(self):
        row = self.lista_clientes.currentRow()
        if row == -1: return
        # Verifica se cliente tem agendamento
        cliente_alvo = self.clientes[row]
        for ag in self.agendamentos:
            # Comparação robusta: se os dados forem iguais, bloqueia
            if ag.cliente.nome == cliente_alvo.nome and ag.cliente.telefone == cliente_alvo.telefone:
                QMessageBox.warning(self, "Erro", "Cliente possui agendamentos!")
                return
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM clientes WHERE nome = ? AND telefone = ?", (cliente_alvo.nome, cliente_alvo.telefone))
        conexao.commit()
        conexao.close()

        del self.clientes[row]
        self.save_and_refresh()

    def cadastrar_servico(self):
        nome = self.input_servico_nome.text().strip()
        valor = self.input_servico_valor.value()
        if not nome or valor <= 0: return
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO servicos (nome, preco) VALUES (?, ?)", (nome, valor))
        conexao.commit()
        conexao.close()

        self.servicos.append(Servico(nome, valor))
        self.input_servico_nome.clear()
        self.input_servico_valor.setValue(0)

        self.save_and_refresh()

    def remover_servico(self):
        row = self.lista_servicos.currentRow()
        if row != -1:
            servico_alvo = self.servicos[row]

            conexao = conectar_banco()
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM servicos WHERE nome = ? AND preco = ?", (servico_alvo.nome, servico_alvo.valor))
            conexao.commit()
            conexao.close()

            del self.servicos[row]
            self.save_and_refresh()

    # ---------------- ABA: AGENDAMENTOS ----------------
    def setup_agendamentos_tab(self):
        layout = QVBoxLayout(self.tab_agendamentos)

        # Formulário
        form = QFormLayout()
        self.combo_clientes = QComboBox() # Criado aqui
        self.combo_servicos = QComboBox()
        self.combo_servicos.currentIndexChanged.connect(self.preencher_valor_servico)
        
        self.input_valor = QDoubleSpinBox()
        self.input_valor.setMaximum(10000.00)
        self.input_valor.setPrefix("R$ ")
        
        self.combo_pagamento = QComboBox()
        self.combo_pagamento.addItems(["Pix", "Dinheiro", "Cartão Crédito", "Cartão Débito"])
        
        self.input_data = QDateEdit(QDate.currentDate())
        self.input_data.setCalendarPopup(True)
        self.input_hora = QTimeEdit(QTime.currentTime())

        form.addRow("Cliente:", self.combo_clientes)
        form.addRow("Serviço:", self.combo_servicos)
        form.addRow("Valor:", self.input_valor)
        form.addRow("Pagamento:", self.combo_pagamento)
        form.addRow("Data:", self.input_data)
        form.addRow("Hora:", self.input_hora)
        layout.addLayout(form)

        # Botões
        self.btn_agendar = QPushButton("✅ Agendar Atendimento")
        self.btn_agendar.clicked.connect(self.agendar)
        layout.addWidget(self.btn_agendar)

        hbox_edit = QHBoxLayout()
        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.clicked.connect(self.iniciar_edicao)
        self.btn_editar.setEnabled(False)
        
        self.btn_remover = QPushButton("🗑️ Remover")
        self.btn_remover.clicked.connect(self.remover_agendamento)
        self.btn_remover.setEnabled(False)
        
        hbox_edit.addWidget(self.btn_editar)
        hbox_edit.addWidget(self.btn_remover)
        layout.addLayout(hbox_edit)

        # Lista formatada
        self.lista_agendamentos = QListWidget()
        self.lista_agendamentos.setSpacing(5) 
        self.lista_agendamentos.currentItemChanged.connect(self.check_selection_agenda)
        layout.addWidget(self.lista_agendamentos)

    def preencher_valor_servico(self):
        idx = self.combo_servicos.currentIndex()
        if idx >= 0 and idx < len(self.servicos):
            self.input_valor.setValue(self.servicos[idx].valor)

    def check_selection_agenda(self, current, prev):
        has_selection = current is not None
        self.btn_editar.setEnabled(has_selection)
        self.btn_remover.setEnabled(has_selection)

    def agendar(self):
        if not self.clientes or not self.servicos:
            QMessageBox.warning(self, "Erro", "Cadastre clientes e serviços primeiro!")
            return

        # Coleta de dados
        idx_cli = self.combo_clientes.currentIndex()
        idx_serv = self.combo_servicos.currentIndex()
        if idx_cli == -1 or idx_serv == -1: return

        cliente = self.clientes[idx_cli]
        servico_nome = self.servicos[idx_serv].nome
        valor = self.input_valor.value()
        pagamento = self.combo_pagamento.currentText()
        
        data = self.input_data.date().toPyDate()
        hora = self.input_hora.time().toPyTime()
        data_hora = datetime.datetime.combine(data, hora)
        data_hora_str = data_hora.strftime("%Y-%m-%d %H:%M")

        # Validação de Conflito
        for i, ag in enumerate(self.agendamentos):
            if self.indice_agendamento_em_edicao is not None and i == self.indice_agendamento_em_edicao:
                continue
            if ag.data_hora == data_hora:
                QMessageBox.warning(self, "Erro", "Horário já ocupado!")
                return

        novo_agendamento = Agendamento(cliente, servico_nome, data_hora, valor, pagamento)

        conexao = conectar_banco()
        cursor = conexao.cursor()

        if self.indice_agendamento_em_edicao is None:
            cursor.execute("INSERT INTO agendamentos (nome_cliente, servico, valor, forma_pagamento, data_hora) VALUES (?, ?, ?, ?, ?)",
                           (cliente.nome, servico_nome, valor, pagamento, data_hora_str))
            
            self.agendamentos.append(novo_agendamento)
            msg = "Agendamento criado!"
        else:
            agendamento_antigo = self.agendamentos[self.indice_agendamento_em_edicao]
            data_hora_antiga_str = agendamento_antigo.data_hora.strftime("%Y-%m-%d %H:%M")

            cursor.execute("""
                UPDATE agendamentos 
                SET nome_cliente = ?, servico = ?, valor = ?, forma_pagamento = ?, data_hora = ?
                WHERE nome_cliente = ? AND data_hora = ?
            """, (cliente.nome, servico_nome, valor, pagamento, data_hora_str, agendamento_antigo.cliente.nome, data_hora_antiga_str))
            self.agendamentos[self.indice_agendamento_em_edicao] = novo_agendamento
            self.indice_agendamento_em_edicao = None
            self.btn_agendar.setText("✅ Agendar Atendimento")
            self.btn_editar.setEnabled(True)
            msg = "Agendamento atualizado!"
        conexao.commit()
        conexao.close()

        self.agendamentos.sort(key=lambda x: x.data_hora)
        self.save_and_refresh()
        QMessageBox.information(self, "Sucesso", msg)

    def iniciar_edicao(self):
        row = self.lista_agendamentos.currentRow()
        if row == -1: return

        ag = self.agendamentos[row]
        
        # Preenche campos
        idx_cli = self.combo_clientes.findText(str(ag.cliente))
        if idx_cli != -1: self.combo_clientes.setCurrentIndex(idx_cli)
        
        idx_serv = self.combo_servicos.findText(ag.servico)
        if idx_serv != -1: self.combo_servicos.setCurrentIndex(idx_serv)
        
        self.input_valor.setValue(ag.valor)
        self.combo_pagamento.setCurrentText(ag.pagamento)
        self.input_data.setDate(ag.data_hora.date())
        self.input_hora.setTime(ag.data_hora.time())

        self.indice_agendamento_em_edicao = row
        self.btn_agendar.setText("💾 Salvar Alterações")
        self.btn_editar.setEnabled(False)
        self.tab_agendamentos.setFocus()

    def remover_agendamento(self):
        row = self.lista_agendamentos.currentRow()
        if row != -1 and QMessageBox.question(self, "Confirmação", "Remover este agendamento?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            ag = self.agendamentos[row]
            data_hora_str = ag.data_hora.strftime("%Y-%m-%d %H:%M")
            
            conexao = conectar_banco()
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM agendamentos WHERE nome_cliente = ? AND data_hora = ?", (ag.cliente.nome, data_hora_str))
            conexao.commit()
            conexao.close()
            
            del self.agendamentos[row]
            self.save_and_refresh()

    # ---------------- UTILITÁRIOS GERAIS ----------------
    def save_and_refresh(self):
        self.save_data()
        self.atualizar_listas_visuais()

    def atualizar_listas_visuais(self):
        # Agora esta função é segura porque só é chamada quando TUDO existe
        
        # Atualiza Combo Boxes
        self.combo_clientes.clear()
        self.combo_clientes.addItems([str(c) for c in self.clientes])
        
        self.combo_servicos.clear()
        self.combo_servicos.addItems([s.nome for s in self.servicos])

        # Atualiza Listas Visuais (ListWidgets)
        self.lista_clientes.clear()
        for c in self.clientes: self.lista_clientes.addItem(str(c))
        
        self.lista_servicos.clear()
        for s in self.servicos: self.lista_servicos.addItem(str(s))

        # Atualiza Lista de Agendamentos
        self.lista_agendamentos.clear()
        for ag in self.agendamentos:
            texto = f"📅 {ag.data_hora.strftime('%d/%m/%Y')}   ⏰ {ag.data_hora.strftime('%H:%M')}\n"
            texto += f"👤 {ag.cliente.nome}   ✨ {ag.servico}\n"
            texto += f"💰 R$ {ag.valor:.2f}   💳 {ag.pagamento}"
            
            item = QListWidgetItem(texto)
            item.setFont(QFont("Segoe UI", 11))
            self.lista_agendamentos.addItem(item)

    def save_data(self):
        # Agora o JSON salva APENAS configurações visuais.
        # Os dados do banco (clientes, etc) não entram mais aqui.
        data = {
            "tema": self.current_theme,
            "cores": self.config["cores"]
        }
        with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_data(self):
        # Tenta carregar as configurações de tema salvas
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Carrega o tema salvo (se não tiver, usa 'light')
                self.current_theme = data.get("tema", "light")
                if "cores" in data:
                    self.config["cores"] = data["cores"]
                    
        except (FileNotFoundError, json.JSONDecodeError):
            # Se o arquivo não existir ou estiver corrompido,ele usará o DEFAULT_CONFIG e criará o arquivo no primeiro save.
            pass

    def carregar_do_banco(self):
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute("SELECT nome, telefone FROM clientes")
        self.clientes = [Cliente(linha[0], linha[1]) for linha in cursor.fetchall()]

        cursor.execute("SELECT nome, preco FROM servicos")
        self.servicos = [Servico(linha[0], linha[1]) for linha in cursor.fetchall()]

        cursor.execute("SELECT nome_cliente, servico, valor, forma_pagamento, data_hora FROM agendamentos")
        agendamentos_db = cursor.fetchall()
        self.agendamentos = []
        for linha in agendamentos_db:
            nome_cli = linha[0]
            nome_serv = linha[1]
            valor_ag = linha[2]
            pagamento_ag = linha[3]
            data_hora_str = linha[4]
            
            data_hora_obj = datetime.datetime.strptime(data_hora_str, "%Y-%m-%d %H:%M")
            cliente_obj = next((c for c in self.clientes if c.nome == nome_cli), Cliente(nome_cli, ""))
            self.agendamentos.append(Agendamento(cliente_obj, nome_serv, data_hora_obj, valor_ag, pagamento_ag))

        conexao.close()



conexao_teste = conectar_banco()  # Testa a conexão com o banco de dados
conexao_teste.close()  # Fecha a conexão de teste

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClinicaEsteticaApp(app)
    window.show()
    sys.exit(app.exec_())