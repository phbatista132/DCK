from src.utils import SistemaAdm,Produto, SistemaPrincipal
from src.utils import fernet, descriptografar

def main():
    adm = SistemaAdm(fernet, descriptografar)
    produto = Produto()
    sis_principal = SistemaPrincipal()
    while True:
        try:
            opc = int(input("Selecione uma Opção: "))

            if opc == 1:
                print(sis_principal.cadastrar_produto())
            elif opc == 2:
                produto.listar_produtos()
            elif opc == 3:
                print(sis_principal.deletar_produto())
            elif opc == 4:
                print(sis_principal.filtrar_produto())
            elif opc == 5:
                adm.cadastrar_cliente()
            elif opc == 6:
                cpf = str(input("CPF: ")).replace('.', '').replace('-', '')
                adm.excluir_cliente(cpf)
            elif opc == 7:
                id = int(input("ID: "))
                qtd = int(input("Quantidade: "))
                sis_principal.reposicao(id, qtd)
            elif opc == 0:
                print("Saindo do programa!")
                break
            else:
                print("❌ Opção inválida.")
        except Exception as e:
            print(f"⚠️ Erro: {e}")


if __name__ == "__main__":
    main()