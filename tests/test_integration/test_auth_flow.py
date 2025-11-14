
class TestAuthFlow:
    """Testes de fluxo de autenticação"""

    def test_registro_e_login_completo(self, db_session, auth_controller):
        """Testa registro de usuário e login"""
        # 1. Registrar usuário
        sucesso, msg, dados = auth_controller.registrar_usuario(
            db=db_session,
            username="joao",
            email="joao@test.com",
            senha="Senha123!@#",
            nome_completo="João Silva",
            tipo_usuario="cliente"
        )

        assert sucesso, f"Registro falhou: {msg}"
        assert dados is not None
        assert dados['username'] == "joao"
        assert dados['tipo_usuario'] == "cliente"

        # 2. Fazer login
        sucesso, msg, dados_login = auth_controller.login(
            db=db_session,
            username="joao",
            senha="Senha123!@#"
        )

        assert sucesso, f"Login falhou: {msg}"
        assert 'access_token' in dados_login
        assert 'refresh_token' in dados_login
        assert dados_login['token_type'] == "bearer"

    def test_login_senha_incorreta(self, db_session, auth_controller, usuario_vendedor):
        """Testa login com senha incorreta"""
        sucesso, msg, dados = auth_controller.login(
            db=db_session,
            username="vendedor_test",
            senha="SenhaErrada123!"
        )

        assert not sucesso
        assert "inválidas" in msg.lower() or "incorreta" in msg.lower()

    def test_alterar_senha(self, db_session, auth_controller, usuario_vendedor):
        """Testa alteração de senha"""
        sucesso, msg = auth_controller.alterar_senha(
            db=db_session,
            user_id=usuario_vendedor['id_usuario'],
            senha_atual="Vendedor123!@#",
            nova_senha="NovaSenha456!@#"
        )

        assert sucesso, f"Alteração de senha falhou: {msg}"

        # Verificar se nova senha funciona
        sucesso_login, _, _ = auth_controller.login(
            db=db_session,
            username="vendedor_test",
            senha="NovaSenha456!@#"
        )

        assert sucesso_login, "Login com nova senha falhou"
