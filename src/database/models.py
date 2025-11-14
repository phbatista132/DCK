from sqlalchemy import (Column, Integer, String, Numeric, DateTime, Boolean, CheckConstraint, Index, Text, Date,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship, validates
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
import os

Base = declarative_base()

tipo_usuario_enum = ENUM(
    'admin', 'gerente', 'vendedor', 'cliente',
    name='tipo_usuario_enum',
    create_type=True
)

forma_pagamento_enum = ENUM(
    'Dinheiro', 'Debito', 'Credito', 'PIX',
    name='forma_pagamento_enum',
    create_type=True,
)

tipo_movimentacao_enum = ENUM(
    'ENTRADA', 'SAIDA', 'AJUSTE', 'RESERVA', 'LIBERACAO',
    name='tipo_movimentacao_enum',
    create_type=True
)
acao_enum = ENUM(
    'LOGIN', 'LOGOUT', 'CRIAR', 'ATUALIZAR', 'DELETAR',
    'DESATIVAR', 'ATIVAR', 'AJUSTE_ESTOQUE',
    name='acao_enum',
    create_type=True
)


class Usuarios(Base):
    """
       Tabela de usuários do sistema (vendedores, gerentes, admins)

       Relacionamentos:
       - vendas: Vendas realizadas por este usuário (se for vendedor)
       """
    __tablename__ = 'usuarios'

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    nome_completo = Column(String(200))
    tipo_usuario = Column(tipo_usuario_enum, nullable=False, index=True)
    ativo = Column(Boolean, default=True, index=True)
    data_cadastro = Column(DateTime, default=datetime.now, nullable=False)
    ultimo_acesso = Column(DateTime)

    vendas = relationship('Vendas', back_populates='vendedor', lazy='selectin')

    __table_args__ = (
        Index('idx_usuario_ativo_tipo', 'ativo', 'tipo_usuario'),
    )

    def __repr__(self):
        return f"<Usuario(id{self.id_usuario}, username='{self.username}', tipo='{self.tipo_usuario}')>"

    def __str__(self):
        return f"{self.nome_completo} ({self.username})"

    @validates('email')
    def validate_email(self, key, email):
        """validação baisca de email"""
        if '@' not in email or '.' not in email:
            raise ValueError("Email invalido")
        return email.lower()

    @validates('username')
    def validate_username(self, key, username):
        """Validação de username"""
        if len(username) < 3:
            raise ValueError("Username deve ter no mínimo 3 caracteres")
        return username.lower()


class Clientes(Base):
    """
    Tabela de clientes da loja

     Relacionamentos:
    - vendas: Compras realizadas por este cliente
    """
    __tablename__ = 'clientes'

    id_cliente = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False, index=True)
    dt_nascimento = Column(Date, nullable=False)
    telefone = Column(String(15))
    endereco = Column(Text, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    data_cadastro = Column(DateTime, default=datetime.now, nullable=False)

    vendas = relationship('Vendas', back_populates='cliente', lazy='selectin')

    __table_args__ = (
        CheckConstraint("LENGTH(cpf) = 11", name='check_cpf_length'),
        Index('idx_cliente_ativo', 'ativo')
    )

    def __repr__(self):
        return f"<Cliente(id{self.id_cliente}, nome='{self.nome}')>"

    def __str__(self):
        return f"{self.nome})"

    @validates('cpf')
    def validate_cpf(self, key, cpf):
        """Remove formatação do CPF"""
        cpf = ''.join(filter(str.isdigit, cpf))
        if len(cpf) != 11:
            raise ValueError("CPF deve conter 11 dígitos")
        return cpf

    @property
    def idade(self):
        """calcula idade do cliente"""
        hoje = datetime.now().date()

        return hoje.year - self.dt_nascimento.year - (
                (hoje.month, hoje.day) < (self.dt_nascimento.month, self.dt_nascimento.day)
        )


class Produtos(Base):
    """
    Tabela de produtos da loja

    Relacionamentos:
    - itens_venda: Itens de venda que incluem este produto
    - movimentacoes_estoque: Histórico de movimentações
    """
    __tablename__ = 'produtos'

    # Colunas
    codigo = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(200), nullable=False, index=True)
    modelo = Column(String(100))
    categoria = Column(String(100), nullable=False, index=True)
    valor = Column(Numeric(10, 2), nullable=False)
    vlr_compra = Column(Numeric(10, 2), nullable=False)
    quantidade_estoque = Column(Integer, nullable=False, default=0)
    quantidade_reservada = Column(Integer, nullable=False, default=0)
    margem_lucro = Column(Numeric(5, 2))  # Percentual
    ativo = Column(Boolean, default=True, nullable=False, index=True)
    dt_cadastro = Column(DateTime, default=datetime.now, nullable=False)

    # Relacionamentos
    itens_venda = relationship('ItemVenda', back_populates='produto', lazy='selectin')
    movimentacoes = relationship('MovimentacaoEstoque', back_populates='produto', lazy='selectin')

    # Constraints
    __table_args__ = (
        CheckConstraint('valor > 0', name='check_valor_positivo'),
        CheckConstraint('vlr_compra > 0', name='check_vlr_compra_positivo'),
        CheckConstraint('quantidade_estoque >= 0', name='check_estoque_nao_negativo'),
        CheckConstraint('quantidade_reservada >= 0', name='check_reservada_nao_negativo'),
        CheckConstraint('quantidade_reservada <= quantidade_estoque', name='check_reserva_menor_estoque'),
        CheckConstraint('valor >= vlr_compra', name='check_valor_maior_custo'),
        UniqueConstraint('nome', 'modelo', 'categoria', name='uq_produto'),
        Index('idx_produto_ativo_categoria', 'ativo', 'categoria'),
        Index('idx_produto_estoque_baixo', 'quantidade_estoque', 'ativo'),
    )

    def __repr__(self):
        return f"<Produto(codigo={self.codigo}, nome='{self.nome}', estoque={self.quantidade_estoque})>"

    @validates('valor', 'vlr_compra')
    def validate_valores(self, key, value):
        d = Decimal(str(value))
        if d <= 0:
            raise ValueError(f"{key} deve ser maior que zero")
        return d.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    @property
    def margem_lucro_calculada(self):
        """Calcula margem de lucro automaticamente"""
        if self.vlr_compra > 0:
            return round(((self.valor - self.vlr_compra) / self.vlr_compra) * 100, 2)
        return 0

    @property
    def estoque_baixo(self):
        """Verifica se estoque está baixo"""
        return self.quantidade_estoque < 10


class Vendas(Base):
    """
    Tabela de vendas realizadas

    Relacionamentos:
    - cliente: Cliente que realizou a compra (opcional)
    - vendedor: Usuário vendedor que finalizou a venda
    - itens: Lista de itens da venda
    """
    __tablename__ = 'vendas'

    # Colunas
    id_venda = Column(Integer, primary_key=True, autoincrement=True)
    data_hora = Column(DateTime, default=datetime.now, nullable=False, index=True)
    subtotal = Column(Numeric(10, 2), nullable=False)
    desconto = Column(Numeric(10, 2), default=0, nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    forma_pagamento = Column(forma_pagamento_enum, nullable=False)

    # Foreign Keys
    cliente_id = Column(Integer, ForeignKey('clientes.id_cliente', ondelete='SET NULL'))
    vendedor_id = Column(Integer, ForeignKey('usuarios.id_usuario', ondelete='SET NULL'),
                         nullable=False, index=True)

    # Denormalização para performance (snapshot do nome do vendedor)
    vendedor_nome = Column(String(50))

    # Relacionamentos
    cliente = relationship('Clientes', back_populates='vendas')
    vendedor = relationship('Usuarios', back_populates='vendas')
    itens = relationship('ItemVenda', back_populates='venda', cascade='all, delete-orphan', lazy='selectin')

    # Constraints
    __table_args__ = (
        CheckConstraint('subtotal >= 0', name='check_subtotal_positivo'),
        CheckConstraint('desconto >= 0', name='check_desconto_positivo'),
        CheckConstraint('total >= 0', name='check_total_positivo'),
        CheckConstraint('desconto <= subtotal', name='check_desconto_menor_subtotal'),
        Index('idx_venda_data', 'data_hora'),
        Index('idx_venda_vendedor', 'vendedor_id', 'data_hora'),
        Index('idx_venda_cliente', 'cliente_id', 'data_hora'),
    )

    def __repr__(self):
        return f"<Venda(id={self.id_venda}, total={self.total}, vendedor='{self.vendedor_nome}')>"

    @validates('desconto')
    def validate_desconto(self, key, desconto):
        """Validação de desconto"""
        if desconto < 0:
            raise ValueError("Desconto não pode ser negativo")
        if self.subtotal and desconto > self.subtotal:
            raise ValueError("Desconto não pode ser maior que subtotal")
        return desconto

    def aplicar_desconto(self, percentual: float):
        if not 0 <= percentual <= 100:
            raise ValueError("Percentual deve estar entre 0 e 100")

        desconto_decimal = (Decimal(str(self.subtotal)) * Decimal(str(percentual)) / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_DOWN)
        self.desconto = desconto_decimal
        self.total = Decimal(str(self.subtotal)) - desconto_decimal

    @property
    def quantidade_itens(self):
        """Retorna quantidade total de itens"""
        return sum(item.quantidade for item in self.itens)


status_carrinho_enum = ENUM(
    'ATIVO', 'FINALIZADO', 'CANCELADO', 'EXPIRADO',
    name='status_carrinho_enum',
    create_type=True
)


class Carrinho(Base):
    """
    Carrinho de compras persistido no banco

    Status:
    - ATIVO: Carrinho em uso (pode adicionar/remover itens)
    - FINALIZADO: Compra foi finalizada (convertido em Venda)
    - CANCELADO: Usuário cancelou
    - EXPIRADO: Passou do tempo limite (30 minutos de inatividade)

    Relacionamentos:
    - usuario: Dono do carrinho
    - itens: Lista de produtos no carrinho
    """
    __tablename__ = 'carrinhos'

    id_carrinho = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id_usuario', ondelete='CASCADE'),
                        nullable=False, index=True)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    expira_em = Column(DateTime, nullable=False, index=True)
    subtotal = Column(Numeric(10, 2), default=0, nullable=False)
    status = Column(status_carrinho_enum, default='ATIVO', nullable=False, index=True)

    # Relacionamentos
    usuario = relationship("Usuarios")
    itens = relationship("ItemCarrinho", back_populates="carrinho",
                         cascade="all, delete-orphan", lazy='joined')

    __table_args__ = (
        CheckConstraint('subtotal >= 0', name='check_carrinho_subtotal_positivo'),
        Index('idx_carrinho_usuario_status', 'usuario_id', 'status'),
        Index('idx_carrinho_ativo_expirado', 'status', 'expira_em'),
    )

    def __repr__(self):
        return (f"<Carrinho(id={self.id_carrinho}, usuario_id={self.usuario_id}, "
                f"itens={len(self.itens)}, subtotal={self.subtotal}, status='{self.status}')>")

    @property
    def total_itens(self):
        """Retorna quantidade total de itens no carrinho"""
        return sum(item.quantidade for item in self.itens)

    @property
    def expirou(self):
        """Verifica se o carrinho expirou"""
        return datetime.now() > self.expira_em

    def calcular_subtotal(self):
        """Recalcula subtotal baseado nos itens"""
        self.subtotal = sum(
            item.preco_unitario * item.quantidade
            for item in self.itens
        )
        return self.subtotal

    def renovar_expiracao(self, minutos: int = 30):
        """Renova o tempo de expiração (quando usuário interage)"""
        from datetime import timedelta
        self.expira_em = datetime.now() + timedelta(minutes=minutos)
        self.atualizado_em = datetime.now()


class ItemCarrinho(Base):
    """
    Item individual dentro de um carrinho

    Snapshot do preço no momento que foi adicionado ao carrinho
    (caso o preço do produto mude depois)

    Relacionamentos:
    - carrinho: Carrinho ao qual pertence
    - produto: Produto referenciado
    """
    __tablename__ = 'itens_carrinho'

    id_item = Column(Integer, primary_key=True, autoincrement=True)
    carrinho_id = Column(Integer, ForeignKey('carrinhos.id_carrinho', ondelete='CASCADE'),nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey('produtos.codigo', ondelete='CASCADE'),nullable=False, index=True)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)  # Snapshot do preço
    subtotal = Column(Numeric(10, 2), nullable=False)
    adicionado_em = Column(DateTime, default=datetime.now, nullable=False)
    carrinho = relationship("Carrinho", back_populates="itens")
    produto = relationship("Produtos")

    __table_args__ = (
        CheckConstraint('quantidade > 0', name='check_item_quantidade_positiva'),
        CheckConstraint('preco_unitario > 0', name='check_item_preco_positivo'),
        CheckConstraint('subtotal >= 0', name='check_item_subtotal_positivo'),
        UniqueConstraint('carrinho_id', 'produto_id', name='uq_carrinho_produto'),
        Index('idx_item_carrinho', 'carrinho_id'),
    )

    def __repr__(self):
        return (f"<ItemCarrinho(id={self.id_item}, produto_id={self.produto_id}, "
                f"qtd={self.quantidade}, subtotal={self.subtotal})>")

    def calcular_subtotal(self):
        """Calcula subtotal do item"""
        self.subtotal = float(
            Decimal(str(self.preco_unitario * self.quantidade)).quantize(
                Decimal('0.01'), rounding=ROUND_DOWN
            )
        )
        return self.subtotal


class ItemVenda(Base):
    """
    Tabela de itens individuais de cada venda

    Relacionamentos:
    - venda: Venda a qual este item pertence
    - produto: Produto vendido (opcional - pode ser deletado depois)
    """
    __tablename__ = 'itens_venda'

    id_item = Column(Integer, primary_key=True, autoincrement=True)
    id_venda = Column(Integer, ForeignKey('vendas.id_venda', ondelete='CASCADE'),nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey('produtos.codigo', ondelete='SET NULL'))
    nome_produto = Column(String(200), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    venda = relationship('Vendas', back_populates='itens')
    produto = relationship('Produtos', back_populates='itens_venda', lazy='selectin')

    __table_args__ = (
        CheckConstraint('quantidade > 0', name='check_quantidade_positiva'),
        CheckConstraint('preco_unitario > 0', name='check_preco_positivo'),
        CheckConstraint('subtotal >= 0', name='check_subtotal_item_positivo'),
        Index('idx_item_venda', 'id_venda'),
        Index('idx_item_produto', 'produto_id'),
    )

    def __repr__(self):
        return f"<ItemVenda(id={self.id_item}, produto='{self.nome_produto}', qtd={self.quantidade})>"

    def __str__(self):
        return f"{self.quantidade}x {self.nome_produto} @ {self.preco_unitario}"

    @validates('quantidade')
    def validate_quantidade(self, key, quantidade):
        """Validação de quantidade"""
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return quantidade

    def calcular_subtotal(self):
        preco = Decimal(str(self.preco_unitario))
        qtd = Decimal(str(self.quantidade))
        self.subtotal = (preco * qtd).quantize(Decimal("0.01"), rounding=ROUND_DOWN)


class Reserva(Base):
    """
    Tabela para rastrear reservas individuais (carrinhos)

    Cada item no carrinho cria uma reserva que expira em 30 minutos
    """
    __tablename__ = 'reservas'

    id_reserva = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey('produtos.codigo', ondelete='CASCADE'),
                        nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id_usuario', ondelete='CASCADE'),
                        nullable=False, index=True)
    quantidade = Column(Integer, nullable=False)
    data_criacao = Column(DateTime, default=datetime.now, nullable=False)
    expira_em = Column(DateTime, nullable=False, index=True)  # 30min após criação
    ativa = Column(Boolean, default=True, nullable=False, index=True)

    # Relacionamentos
    produto = relationship('Produtos')
    usuario = relationship('Usuarios')

    __table_args__ = (
        CheckConstraint('quantidade > 0', name='check_reserva_quantidade_positiva'),
        Index('idx_reserva_ativa_expira', 'ativa', 'expira_em'),
        Index('idx_reserva_usuario_ativa', 'usuario_id', 'ativa'),
    )

    def __repr__(self):
        return f"<Reserva(id={self.id_reserva}, produto_id={self.produto_id}, qtd={self.quantidade})>"

    @property
    def expirou(self):
        """Verifica se a reserva expirou"""
        return datetime.now() > self.expira_em

    @property
    def tempo_restante_segundos(self):
        """Retorna tempo restante em segundos"""
        if self.expirou:
            return 0
        return int((self.expira_em - datetime.now()).total_seconds())


class MovimentacaoEstoque(Base):
    """
    Tabela para rastrear todas as movimentações de estoque

    Tipos:
    - ENTRADA: Reposição de estoque
    - SAIDA: Venda
    - AJUSTE: Correção manual
    - RESERVA: Produto adicionado ao carrinho
    - LIBERACAO: Produto removido do carrinho

    Relacionamentos:
    - produto: Produto movimentado
    - usuario: Usuário responsável pela movimentação
    - venda: Venda relacionada (se tipo = SAIDA)
    """
    __tablename__ = 'movimentacoes_estoque'

    # Colunas
    id_movimentacao = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey('produtos.codigo', ondelete='CASCADE'),
                        nullable=False, index=True)
    tipo = Column(tipo_movimentacao_enum, nullable=False, index=True)
    quantidade = Column(Integer, nullable=False)
    estoque_anterior = Column(Integer, nullable=False)
    estoque_posterior = Column(Integer, nullable=False)
    data_hora = Column(DateTime, default=datetime.now, nullable=False, index=True)
    observacao = Column(Text)

    # Foreign Keys
    usuario_id = Column(Integer, ForeignKey('usuarios.id_usuario', ondelete='SET NULL'))
    venda_id = Column(Integer, ForeignKey('vendas.id_venda', ondelete='SET NULL'))

    # Relacionamentos
    produto = relationship('Produtos', back_populates='movimentacoes')
    usuario = relationship('Usuarios')
    venda = relationship('Vendas')

    # Constraints
    __table_args__ = (
        CheckConstraint('quantidade != 0', name='check_quantidade_nao_zero'),
        CheckConstraint('estoque_anterior >= 0', name='check_estoque_anterior_valido'),
        CheckConstraint('estoque_posterior >= 0', name='check_estoque_posterior_valido'),
        Index('idx_movimentacao_produto_data', 'produto_id', 'data_hora'),
        Index('idx_movimentacao_tipo', 'tipo', 'data_hora'),
    )

    def __repr__(self):
        return f"<MovimentacaoEstoque(id={self.id_movimentacao}, tipo='{self.tipo}', qtd={self.quantidade})>"

    def __str__(self):
        return f"{self.tipo} de {self.quantidade} un. em {self.data_hora.strftime('%d/%m/%Y %H:%M')}"


# ==================== TABELA: AUDITORIA/LOG (NOVO) ====================

class LogAuditoria(Base):
    """
    Tabela de auditoria para rastrear ações importantes

    Registra:
    - Logins/logouts
    - Alterações de dados críticos
    - Desativações
    - Ajustes de estoque
    """
    __tablename__ = 'log_auditoria'

    # Colunas
    id_log = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id_usuario', ondelete='SET NULL'))
    acao = Column(acao_enum, nullable=False, index=True)
    tabela = Column(String(50))
    registro_id = Column(Integer)
    dados_anteriores = Column(Text)
    dados_novos = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    data_hora = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # Relacionamentos
    usuario = relationship('Usuarios')

    # Constraints
    __table_args__ = (
        Index('idx_log_usuario', 'usuario_id', 'data_hora'),
        Index('idx_log_acao', 'acao', 'data_hora'),
        Index('idx_log_tabela', 'tabela', 'registro_id'),
    )

    def __repr__(self):
        return f"<LogAuditoria(id={self.id_log}, acao='{self.acao}', usuario_id={self.usuario_id})>"


# ==================== FUNÇÕES AUXILIARES ====================

def criar_todas_tabelas(engine):
    Base.metadata.create_all(engine)
    tabelas = Base.metadata.tables.keys()
    print(f"Tabelas criadas: {', '.join(tabelas)}")


def dropar_todas_tabelas(engine):
    if engine.dialect.name == "sqlite" or os.getenv("ENVIRONMENT") == "development":
        Base.metadata.drop_all(engine)
        print("Todas as tabelas removidas!")
    else:
        raise RuntimeError("Dropar tabelas só é permitido em ambiente de desenvolvimento ou SQLite.")


def resetar_banco(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Banco resetado com sucesso.")
