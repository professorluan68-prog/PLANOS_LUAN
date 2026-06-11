import subprocess
import sys
import shutil

def verificar_instalacao(comando):
    """Verifica se uma ferramenta está instalada."""
    return shutil.which(comando) is not None

def executar_comando(comando):
    """Executa um comando no terminal e exibe a saída."""
    try:
        print(f"\n🔹 Executando: {' '.join(comando)}")
        resultado = subprocess.run(comando, check=False, text=True)
        if resultado.returncode == 0:
            print("✅ Concluído com sucesso!")
        else:
            print(f"⚠️ Comando retornou código {resultado.returncode}")
    except Exception as e:
        print(f"❌ Erro ao executar {comando[0]}: {e}")

def main():
    ferramentas = ["black", "isort", "flake8"]

    # Verifica se todas as ferramentas estão instaladas
    for ferramenta in ferramentas:
        if not verificar_instalacao(ferramenta):
            print(f"❌ A ferramenta '{ferramenta}' não está instalada.")
            print(f"   Instale com: pip install {ferramenta}")
            sys.exit(1)

    # Executa as ferramentas na ordem correta
    executar_comando(["black", "."])
    executar_comando(["isort", "."])
    executar_comando(["flake8"])

if __name__ == "__main__":
    main()
