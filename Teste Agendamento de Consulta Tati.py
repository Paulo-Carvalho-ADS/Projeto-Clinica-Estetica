import sys
import datetime
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QTabWidget, QFormLayout, QDateEdit,
    QTimeEdit, QComboBox, QMessageBox, QHBoxLayout, QSpinBox, QDoubleSpinBox,
    QListWidgetItem
)
from PyQt5.QtCore import QDate, QTime, Qt
from PyQt5.QtGui import QPixmap, QFont

# ---------------- CONFIGURAÇÃO PADRÃO ----------------
DEFAULT_CONFIG = {
    "tema": "light",
    "cores": {
        "light": {
            "cor_fundo": "#F5F6FA",
            "cor_texto": "#2F3542",
            "cor_input": "#FFFFFF",
            "cor_borda": "#DCDDE1",
            "cor_primaria": "#1E90FF",
            "cor_primaria_hover": "#4682B4",
            "cor_primaria_press": "#2F3542"
        },
        "dark": {
            "cor_fundo": "#2E3440",
            "cor_texto": "#D8DEE9",
            "cor_input": "#3B4252",
            "cor_borda": "#4C566A",
            "cor_primaria": "#5E81AC",
            "cor_primaria_hover": "#81A1C1",
            "cor_primaria_press": "#4C566A"
        }
    }
}

# ---------------- FUNÇÃO DE TEMA DINÂMICO ----------------
def generate_qss(config, tema):
    cores = config["cores"][tema]
    return f"""
        QWidget {{
            background-color: {cores['cor_fundo']};
            color: {cores['cor_texto']};
            font-size: 14px;
            font-family: "Segoe UI", "Ubuntu", sans-serif;
        }}
        QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox {{
            background-color: {cores['cor_input']};
            border: 1px solid {cores['cor_borda']};
            border-radius: 5px;
            padding: 5px;
            color: {cores['cor_texto']};
        }}
        QPushButton {{
            background-color: {cores['cor_primaria']};
            border: none;
            border-radius: 5px;
            padding: 8px;
            color: white;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {cores['cor_primaria_hover']}; }}
        QPushButton:pressed {{ background-color: {cores['cor_primaria_press']}; }}
        QListWidget {{
            background-color: {cores['cor_input']};
            border: 1px solid {cores['cor_borda']};
            border-radius: 5px;
            padding: 5px;
        }}
        QTabWidget::pane {{
            border: 1px solid {cores['cor_borda']};
            border-radius: 5px;
        }}
        QTabBar::tab {{
            background: {cores['cor_borda']};
            color: {cores['cor_texto']};
            padding: 8px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }}
        QTabBar::tab:selected {{
            background: {cores['cor_primaria']};
            color: white;
            font-weight: bold;
        }}
    """

# ---------------- MODELOS ----------------
class Cliente:
    def __init__(self, nome, telefone):
        self.nome = nome
        self.telefone = telefone

    def __str__(self):
        return f"{self.nome} ({self.telefone})"

    def to_dict(self):
        return {"nome": self.nome, "telefone": self.telefone}

    @staticmethod
    def from_dict(data):
        return Cliente(data["nome"], data["telefone"])


class Agendamento:
    def __init__(self, cliente, servico, data_hora, valor, pagamento):
        self.cliente = cliente
        self.servico = servico
        self.data_hora = data_hora
        self.valor = valor
        self.pagamento = pagamento

    def __str__(self):
        return (f"{self.data_hora.strftime('%d/%m/%Y %H:%M')} - {self.cliente} - "
                f"{self.servico} | R$ {self.valor:.2f} | {self.pagamento}")

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


class Servico:
    def __init__(self, nome,valor):
        self.nome = nome
        self.valor = valor
        
    def __str__(self):
        return f"{self.nome}  (R$ {self.valor:.2f})"
    
    def to_dict(self):
        return {"nome": self.nome, "valor": self.valor}
    
    @staticmethod
    def from_dict(data):
        return Servico(data["nome"], data["valor"])

# ---------------- APLICAÇÃO ----------------
class ClinicaEsteticaApp(QWidget):
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle("Clínica Estética - Sistema de Agendamento")
        self.resize(700, 500)

        self.app = app
        self.clientes = []
        self.agendamentos = []
        self.servicos = []
        self.config = DEFAULT_CONFIG.copy()
        self.current_theme = "light"

        self.indice_agendamento_em_edicao = None  # Índice do agendamento sendo editado

        self.load_data()

        layout = QVBoxLayout(self)

        # Usaremos o logo_layout APENAS para o botão de tema
        logo_layout = QHBoxLayout()
        
        # O espaço à esquerda empurra o botão de tema para a direita
        logo_layout.addStretch(1)

        # Botão de alternância de tema
        self.btn_theme = QPushButton()
        self.btn_theme.clicked.connect(self.toggle_theme)

        logo_layout.addWidget(self.btn_theme)

        logo_layout.setContentsMargins(0, 10, 10, 0) # Ajuste as margens conforme desejar

        layout.addLayout(logo_layout)

        layout.setSpacing(5)


        self.btn_theme = QPushButton()
        self.btn_theme.clicked.connect(self.toggle_theme)


        self.apply_theme()

        # Tabs principais
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Aba Clientes
        self.tab_clientes = QWidget()
        tabs.addTab(self.tab_clientes, "Clientes e Serviços")
        self.setup_clientes_tab()

        # Aba Agendamentos
        self.tab_agendamentos = QWidget()
        tabs.addTab(self.tab_agendamentos, "Agendamentos")
        self.setup_agendamentos_tab()

        self.apply_theme()


    def atualizar_lista_agendamentos(self):
        self.lista_agendamentos.clear()
        for ag in self.agendamentos:
            texto = f"📅 {ag.data_hora.strftime('%d/%m/%Y')}    ⏰ {ag.data_hora.strftime('%H:%M')}\n"
            # Linha 2: Cliente e Serviço
            texto += f"👤 {ag.cliente.nome}    ✨ {ag.servico}\n"
            # Linha 3: Valor e Pagamento
            texto += f"💰 R$ {ag.valor:.2f}    💳 {ag.pagamento}"

            # 3. Cria o item da lista
            item = QListWidgetItem(texto)
            
            # 4. Configura uma fonte maior e mais legível
            font = QFont()
            font.setPointSize(11) # Tamanho da letra
            # font.setBold(True) # Se quiser tudo em negrito, descomente esta linha
            item.setFont(font)
            
            # 5. Adiciona o item à lista visual
            self.lista_agendamentos.addItem(item)


    # ----------------Limpeza de campos----------------

    def limpar_campos_agendamento(self):
        """
        Reseta todos os campos de entrada do formulário de agendamento
        para um estado neutro/padrão.
        """
        # Limpa o campo de texto do serviço (REMOVIDO APÓS A INTEGRAÇÃO DO COMBOBOX)
        # Linha removida: self.input_servico.clear()
        
        # Reseta o valor para zero
        self.input_valor.setValue(0.00) 
        
        # Reseta a data e hora para os valores atuais do sistema (útil para novo agendamento)
        self.input_data.setDate(QDate.currentDate())
        self.input_hora.setTime(QTime.currentTime())
        
        # Reseta a ComboBox de Cliente para o primeiro item (se houver clientes)
        if self.combo_clientes.count() > 0:
            self.combo_clientes.setCurrentIndex(0)
        
        # Reseta a ComboBox de Serviço
        if self.combo_servicos.count() > 0:
            self.combo_servicos.setCurrentIndex(0)
            
        # Reseta a ComboBox de Pagamento para o primeiro item
        if self.combo_pagamento.count() > 0:
            self.combo_pagamento.setCurrentIndex(0)
    
    # ---------------- TEMA ----------------
    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()
        self.save_data()

    def apply_theme(self):
        # 1. Aplica o estilo QSS globalmente
        qss = generate_qss(self.config, self.current_theme)
        self.app.setStyleSheet(qss)
        
        # ------------------ Switch de Tema com Emoji ------------------
        if self.current_theme == "light":
            # Modo Claro: Mostra o ícone de Lua (para ir para o Escuro)
            self.btn_theme.setText("Claro")
            self.btn_theme.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent; 
                    border: none;
                    font-size: 24px; /* <--- GARANTE O TAMANHO DO EMOJI */
                    color: {self.config['cores']['light']['cor_texto']}; /* <--- Cor do texto/emoji no modo claro (PRETO) */
                    padding: 5px;
                }}
                QPushButton:hover {{
                    background-color: {self.config['cores']['light']['cor_borda']};
                    border-radius: 5px;
                }}
            """)
        else:
            # Modo Escuro: Mostra o ícone de Sol (para ir para o Claro)
            self.btn_theme.setText("Escuro")
            self.btn_theme.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent; 
                    border: none;
                    font-size: 24px; /* <--- GARANTE O TAMANHO DO EMOJI */
                    /* A cor do emoji (cor_texto do tema escuro = claro) para ser visível no fundo escuro */
                    color: {self.config['cores']['dark']['cor_texto']}; 
                    padding: 5px;
                }}
                QPushButton:hover {{
                    background-color: {self.config['cores']['dark']['cor_borda']};
                    border-radius: 5px;
                }}
            """)
            
    # ---------------- LÓGICA DE SERVIÇOS ----------------
    def atualizar_botoes_servico(self, current, previous):
        """Habilita/desabilita o botão 'Remover Serviço'."""
        item_selecionado = current is not None
        self.btn_remover_servico.setEnabled(item_selecionado)

    def cadastrar_servico(self):
        """Cadastra um novo serviço fixo na lista."""
        nome = self.input_servico_nome.text().strip()
        valor = self.input_servico_valor.value()
        
        if not nome or valor <= 0:
            QMessageBox.warning(self, "Erro", "Preencha o nome e o valor do serviço corretamente!")
            return

        servico = Servico(nome, valor)
        self.servicos.append(servico)
        self.lista_servicos.addItem(str(servico))

        self.input_servico_nome.clear()
        self.input_servico_valor.setValue(0.00)

        self.atualizar_servicos_combo() 
        self.save_data()
        QMessageBox.information(self, "Sucesso", "Serviço cadastrado com sucesso!")

    def atualizar_servicos_combo(self):

        if hasattr(self, 'combo_servicos'):
            self.combo_servicos.clear()
            for servico in self.servicos:
                self.combo_servicos.addItem(servico.nome)

        pass

    def remover_servico(self):
        """Remove o serviço selecionado da lista."""
        row = self.lista_servicos.currentRow()

        if row == -1:
            QMessageBox.warning(self, "Atenção", "Selecione um serviço para remover!")
            return 
        
        # NÃO PRECISAMOS DE VERIFICAÇÃO DE AGENDAMENTO AQUI
        # (Se um serviço for removido, agendamentos antigos ainda terão o nome e valor salvos)

        confirm = QMessageBox.question(self, "Confirmação", "Tem certeza que deseja remover este serviço fixo?",
                                       QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.No:
            return
        
        del self.servicos[row]
        self.lista_servicos.takeItem(row)

        self.atualizar_servicos_combo() 
        self.save_data()
        QMessageBox.information(self, "Sucesso", "Serviço removido com sucesso!")

    def preencher_valor_servico(self):
        """Preenche automaticamente o campo de valor ao selecionar um serviço fixo."""
        idx = self.combo_servicos.currentIndex()
        if idx == -1:
            self.input_valor.setValue(0.00)
            return
        
        if idx < len(self.servicos):
            servico_selecionado = self.servicos[idx]
            self.input_valor.setValue(servico_selecionado.valor)

    # ---------------- CLIENTES ----------------
    def setup_clientes_tab(self):
        # Layout principal que divide a aba em duas colunas (Clientes e Serviços)
        main_h_layout = QHBoxLayout(self.tab_clientes)

        # ------------------ PAINEL DE CLIENTES ------------------
        cliente_v_layout = QVBoxLayout()
        
        titulo_cliente = QLabel("📋 Clientes")
        titulo_cliente.setAlignment(Qt.AlignCenter)
        titulo_cliente.setStyleSheet("font-weight: bold; font-size: 16px;")
        cliente_v_layout.addWidget(titulo_cliente)

        form_cliente = QFormLayout()
        self.input_nome = QLineEdit()
        self.input_telefone = QLineEdit()
        form_cliente.addRow("Nome:", self.input_nome)
        form_cliente.addRow("Telefone:", self.input_telefone)
        cliente_v_layout.addLayout(form_cliente)

        # Botões de Cliente (Cadastro/Remoção)
        botoes_cliente_layout = QHBoxLayout()

        btn_add = QPushButton("Cadastrar Cliente")
        btn_add.clicked.connect(self.cadastrar_cliente)
        botoes_cliente_layout.addWidget(btn_add)

        self.btn_remover_cliente = QPushButton("🗑️ Remover Cliente")
        self.btn_remover_cliente.clicked.connect(self.remover_cliente)
        self.btn_remover_cliente.setEnabled(False)

        botoes_cliente_layout.addWidget(self.btn_remover_cliente)
        cliente_v_layout.addLayout(botoes_cliente_layout)

        self.lista_clientes = QListWidget()
        self.lista_clientes.currentItemChanged.connect(self.atualizar_botoes_remover_cliente)
        cliente_v_layout.addWidget(self.lista_clientes)

        for cliente in self.clientes:
            self.lista_clientes.addItem(str(cliente))
        
        main_h_layout.addLayout(cliente_v_layout) # Adiciona a coluna de clientes

        # ------------------ PAINEL DE SERVIÇOS (NOVO) ------------------
        servico_v_layout = QVBoxLayout()
        
        titulo_servico = QLabel("✨ Serviços Fixos")
        titulo_servico.setAlignment(Qt.AlignCenter)
        titulo_servico.setStyleSheet("font-weight: bold; font-size: 16px;")
        servico_v_layout.addWidget(titulo_servico)

        form_servico = QFormLayout()
        self.input_servico_nome = QLineEdit() # Novo campo para o nome do serviço
        self.input_servico_valor = QDoubleSpinBox() # Novo campo para o valor
        
        # Configuração do campo de valor do serviço (igual ao da agenda)
        self.input_servico_valor.setMaximum(10000.00)
        self.input_servico_valor.setPrefix("R$ ")
        self.input_servico_valor.setSingleStep(10.00)
        self.input_servico_valor.setDecimals(2)
        
        form_servico.addRow("Nome:", self.input_servico_nome)
        form_servico.addRow("Valor:", self.input_servico_valor)
        servico_v_layout.addLayout(form_servico)

        # Botões de Serviço (Cadastro/Remoção)
        botoes_servico_layout = QHBoxLayout()

        btn_add_servico = QPushButton("Cadastrar Serviço")
        btn_add_servico.clicked.connect(self.cadastrar_servico) # Conecta ao novo método
        botoes_servico_layout.addWidget(btn_add_servico)

        self.btn_remover_servico = QPushButton("🗑️ Remover Serviço")
        self.btn_remover_servico.clicked.connect(self.remover_servico) # Conecta ao novo método
        self.btn_remover_servico.setEnabled(False)

        botoes_servico_layout.addWidget(self.btn_remover_servico)
        servico_v_layout.addLayout(botoes_servico_layout)

        self.lista_servicos = QListWidget()
        # Conexão para habilitar o botão de remoção
        self.lista_servicos.currentItemChanged.connect(self.atualizar_botoes_servico) 
        servico_v_layout.addWidget(self.lista_servicos)

        # Popula a lista de serviços ao carregar
        for servico in self.servicos:
            self.lista_servicos.addItem(str(servico))
            
        main_h_layout.addLayout(servico_v_layout) # Adiciona a coluna de serviços

    def cadastrar_cliente(self):
        nome = self.input_nome.text().strip()
        telefone = self.input_telefone.text().strip()
        if not nome or not telefone:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos!")
            return

        cliente = Cliente(nome, telefone)
        self.clientes.append(cliente)
        self.lista_clientes.addItem(str(cliente))

        self.input_nome.clear()
        self.input_telefone.clear()

        self.atualizar_clientes_combo()
        self.save_data()

    #------------------logica de edição/remoção de clientes-----------------------------
    def atualizar_botoes_remover_cliente(self, current, previous):

        # verifica se há um item selecionado
        item_selecionado = current is not None
        self.btn_remover_cliente.setEnabled(item_selecionado)

    def remover_cliente(self):

        row = self.lista_clientes.currentRow()

        if row == -1:
            QMessageBox.warning(self, "Atenção", "Selecione um cliente para remover!")
            return  # Nenhum item selecionado
        
        cliente_a_remover = self.clientes[row]

        #verifica se o cliente possui agendamentos
        agendamentos_ativos = [ag for ag in self.agendamentos if ag.cliente == cliente_a_remover]

        if agendamentos_ativos:
            QMessageBox.warning(self, "Atenção", "Este cliente possui agendamentos ativos e não pode ser removido!")
            return
        
        confirm = QMessageBox.question(self, "Confirmação", "Tem certeza que deseja remover este cliente?",
                                        QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.No:
            return
        
        del self.clientes[row]

        self.lista_clientes.takeItem(row)

        self.atualizar_clientes_combo()

        self.save_data()
        QMessageBox.information(self, "Sucesso", "Cliente removido com sucesso!")

    #------------------logica de edição/remoção agendamentos-----------------------------
    def atualizar_botoes_agendamento(self, current, previous):
        # verifica se há um item selecionado
        item_selecionado = current is not None
        self.btn_editar.setEnabled(item_selecionado)
        self.btn_remover.setEnabled(item_selecionado)

    def remover_agendamento(self):
        # remove o agendamento selecionado da lista e salva os dados
        # 1. pegar o indice do item selecionado
        row = self.lista_agendamentos.currentRow()

        if row == -1:
            QMessageBox.warning(self, "Atenção", "Selecione um agendamento para remover!")
            return  # Nenhum item selecionado
        
        # 2. comfirmação do usuario antes de remover
        confirm = QMessageBox.question(self, "Confirmação", "Tem certeza que deseja remover este agendamento?",
                                        QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.No:
            return
        
        # 3. remover da lista (onde os dados estão armazenados)
        # o indice da lista de agendamentos é o mesmo do QListWidget
        del self.agendamentos[row]

        # 4. remover da interface (QListWidget)
        self.lista_agendamentos.takeItem(row)

        # 5. salvar os dados atualizados no json
        self.save_data()
        QMessageBox.information(self, "Sucesso", "Agendamento removido com sucesso!")

    def iniciar_edicao_agendamento(self):
        """
        Carrega os dados do agendamento selecionado no formulário e
        coloca a interface em modo de edição.
        """
        row = self.lista_agendamentos.currentRow()

        if row == -1:
            QMessageBox.warning(self, "Atenção", "Selecione um agendamento para editar!")
            return # Nenhum item selecionado
          
        agendamento_selecionado = self.agendamentos[row]
          
        # --- Carregamento de Dados (Seu código anterior, mas no novo método) ---
        nome_cliente = str(agendamento_selecionado.cliente)
        index_cliente = self.combo_clientes.findText(nome_cliente)
        if index_cliente != -1:
            self.combo_clientes.setCurrentIndex(index_cliente)

        self.input_servico.setText(agendamento_selecionado.servico)
        self.input_valor.setValue(agendamento_selecionado.valor)

        pagamento = agendamento_selecionado.pagamento
        index_pagamento = self.combo_pagamento.findText(pagamento)
        if index_pagamento != -1:
            self.combo_pagamento.setCurrentIndex(index_pagamento)

        data_py = agendamento_selecionado.data_hora.date()
        hora_py = agendamento_selecionado.data_hora.time()
        qdate = QDate(data_py.year, data_py.month, data_py.day)
        qtime = QTime(hora_py.hour, hora_py.minute)

        self.input_data.setDate(qdate)
        self.input_hora.setTime(qtime)
        
        # --- Ações de Modo Edição ---
        # 1. Armazena o índice (CRUCIAL)
        self.indice_agendamento_em_edicao = row
        
        # 2. MUDANÇA: Altera o texto do BOTÃO PRINCIPAL (self.btn_agendar)
        self.btn_agendar.setText("✅ Salvar Edição") 

        # 3. Desabilita o botão auxiliar de edição
        self.btn_editar.setEnabled(False) 
        
        QMessageBox.information(self, "Modo Edição Ativado", "Dados carregados! Altere os campos e clique em 'Salvar Edição'.")

    # ---------------- AGENDAMENTOS ----------------
    def setup_agendamentos_tab(self):
        layout = QVBoxLayout(self.tab_agendamentos)

        titulo = QLabel("📅 Agendamentos")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(titulo)

        form = QFormLayout()
        self.combo_clientes = QComboBox()
        self.combo_servicos = QComboBox()
        self.combo_servicos.currentIndexChanged.connect(self.preencher_valor_servico)
        self.input_valor = QDoubleSpinBox()
        self.input_valor.setMaximum(100000.00)
        self.input_valor.setPrefix("R$ ")
        self.input_valor.setSingleStep(5.00)
        self.input_valor.setDecimals(2)

        self.combo_pagamento = QComboBox()
        self.combo_pagamento.addItems(["Cartão de Crédito", "Cartão de Débito", "Pix", "Cheque", "Dinheiro"])

        self.input_data = QDateEdit()
        self.input_data.setDate(QDate.currentDate())
        self.input_data.setCalendarPopup(True)

        self.input_hora = QTimeEdit()
        self.input_hora.setTime(QTime.currentTime())

        form.addRow("Cliente:", self.combo_clientes)
        form.addRow("Serviço:", self.combo_servicos)
        form.addRow("Valor:", self.input_valor)
        form.addRow("Pagamento:", self.combo_pagamento)
        form.addRow("Data:", self.input_data)
        form.addRow("Hora:", self.input_hora)
        form.addRow("Hora:", self.input_hora)
        layout.addLayout(form)

        # 1. BOTÃO PRINCIPAL (SERÁ NOVO CADASTRO OU SALVAR EDIÇÃO)
        self.btn_agendar = QPushButton("Agendar Atendimento")
        self.btn_agendar.clicked.connect(self.agendar) # Conexão principal e única
        layout.addWidget(self.btn_agendar)

        # 2. BOTÕES DE AÇÃO AUXILIARES
        botoes_acao_layout = QHBoxLayout()

        self.btn_editar = QPushButton("✏️ Iniciar Edição") # Mude o texto para 'Iniciar Edição'
        self.btn_editar.clicked.connect(self.iniciar_edicao_agendamento) # NOVO MÉTODO
        self.btn_editar.setEnabled(False) 

        self.btn_remover = QPushButton("🗑️ Remover Agendamento") 
        self.btn_remover.clicked.connect(self.remover_agendamento) 
        self.btn_remover.setEnabled(False) 

        botoes_acao_layout.addWidget(self.btn_editar)
        botoes_acao_layout.addWidget(self.btn_remover)
        layout.addLayout(botoes_acao_layout)

        #-------------------------------------------------

        self.lista_agendamentos = QListWidget()
        layout.addWidget(self.lista_agendamentos)

        self.lista_agendamentos.currentItemChanged.connect(self.atualizar_botoes_agendamento)
        layout.addWidget(self.lista_agendamentos)

        for ag in self.agendamentos:
            self.lista_agendamentos.addItem(str(ag))

        self.atualizar_clientes_combo()
        self.atualizar_servicos_combo()

    def atualizar_clientes_combo(self):
        self.combo_clientes.clear()
        for cliente in self.clientes:
            self.combo_clientes.addItem(str(cliente))

    def agendar(self):
        # 1. Validações Iniciais
        if not self.clientes:
            QMessageBox.warning(self, "Erro", "Cadastre um cliente primeiro!")
            return
        
        # O ComboBox de serviços pode estar visível mesmo se a lista interna estiver vazia
        if not self.servicos:
            QMessageBox.warning(self, "Erro", "Cadastre um serviço primeiro na aba Clientes!")
            return

        # 2. Coleta de Dados
        idx_cliente = self.combo_clientes.currentIndex()
        idx_servico = self.combo_servicos.currentIndex()
        
        if idx_cliente == -1 or idx_servico == -1:
            QMessageBox.warning(self, "Erro", "Selecione um cliente e um serviço para agendar!")
            return
            
        cliente = self.clientes[idx_cliente]
        
        # Agora pegamos o nome do serviço a partir do objeto na lista self.servicos
        # O índice do ComboBox é o mesmo da lista self.servicos
        servico_obj = self.servicos[idx_servico]
        servico = servico_obj.nome # Pegamos o nome do serviço para o Agendamento
        
        valor = float(self.input_valor.value()) # Valor pode ter sido alterado manualmente
        pagamento = self.combo_pagamento.currentText()
        
        # A validação de serviço (if not servico:) não é mais necessária aqui
        
        data = self.input_data.date().toPyDate()
        hora = self.input_hora.time().toPyTime()
        data_hora = datetime.datetime.combine(data, hora)

        # 2. Verificação de Conflito de Horário
        for i, ag in enumerate(self.agendamentos):
            # Se a data_hora for a mesma E não for o agendamento que está sendo editado (se houver)
            if ag.data_hora == data_hora and (self.indice_agendamento_em_edicao is None or i != self.indice_agendamento_em_edicao):
                QMessageBox.warning(self, "Erro", "Este horário já está ocupado!")
                return
            
        # 3. Criação do Objeto Agendamento
        agendamento = Agendamento(cliente, servico, data_hora, valor, pagamento)
        
        # 4. Lógica de Cadastro OU Edição (FLUXO EXCLUSIVO)
        if self.indice_agendamento_em_edicao is None:
            # MODO CADASTRO: Adiciona um novo
            self.agendamentos.append(agendamento)
            self.lista_agendamentos.addItem(str(agendamento))
            msg = "Agendamento realizado com sucesso!"
        else:
            # MODO EDIÇÃO: Substitui o antigo pelo novo
            idx_edicao = self.indice_agendamento_em_edicao
            self.agendamentos[idx_edicao] = agendamento
            
            # Atualiza o texto na lista gráfica
            item_lista = self.lista_agendamentos.item(idx_edicao)
            item_lista.setText(str(agendamento))

            # Reseta o modo de edição (CRUCIAL)
            self.indice_agendamento_em_edicao = None
            
            # ATENÇÃO: Resetar o botão principal e o botão editar auxiliar
            self.btn_agendar.setText("Agendar Atendimento") # Volta o texto do botão principal
            self.btn_editar.setEnabled(True) # Habilita de volta o botão de edição auxiliar
            
            msg = "Agendamento editado com sucesso!"
            
        # 5. Ações Finais (executadas em ambos os casos)
        # Limpa os campos após agendar ou editar
        self.limpar_campos_agendamento()

        self.save_data()
        QMessageBox.information(self, "Sucesso", msg)

        

        for ag in self.agendamentos:
            if ag.data_hora == data_hora:
                QMessageBox.warning(self, "Erro", "Este horário já está ocupado!")
                return

        agendamento = Agendamento(cliente, servico, data_hora, valor, pagamento)
        self.agendamentos.append(agendamento)
        self.lista_agendamentos.addItem(str(agendamento))

        self.input_servico.clear()
        self.save_data()

    # ---------------- PERSISTÊNCIA ----------------
    def save_data(self):
        data = {
            "clientes": [c.to_dict() for c in self.clientes],
            "agendamentos": [a.to_dict() for a in self.agendamentos],
            "servicos": [s.to_dict() for s in self.servicos],
            "tema": self.current_theme,
            "cores": self.config["cores"],
        }
        with open("clinica.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_data(self):
        try:
            with open("clinica.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.clientes = [Cliente.from_dict(c) for c in data.get("clientes", [])]
                self.agendamentos = [Agendamento.from_dict(a) for a in data.get("agendamentos", [])]
                self.servicos = [Servico.from_dict(s) for s in data.get("servicos", [])]
                self.current_theme = data.get("tema", "light")
                self.config["cores"] = data.get("cores", DEFAULT_CONFIG["cores"])
        except FileNotFoundError:
            self.clientes = []
            self.agendamentos = []
            self.servicos = []
            self.current_theme = "light"
            self.config = DEFAULT_CONFIG.copy()

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClinicaEsteticaApp(app)
    window.show()
    sys.exit(app.exec_())
