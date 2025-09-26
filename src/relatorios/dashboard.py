import pandas as pd
import plotly.express as px
from datetime import date
from abc import ABC, abstractmethod



class RelatoriosBase(ABC):
    @abstractmethod
    def gerar(self) -> pd.DataFrame:
        pass

    @property
    @abstractmethod
    def coluna_y(self) -> str:
        """Define dinamicamente a coluna Y do gráfico"""
        pass

    @property
    def titulo(self) -> str:
        return f"📊 {self.__class__.__name__}"

    def gerar_grafico(self, df: pd.DataFrame):
        if df.empty or self.coluna_y not in df.columns:
            raise ValueError(f"Coluna Y '{self.coluna_y}' não encontrada no DataFrame.")

        return px.bar(df, x=df.columns[0], y=self.coluna_y, title=self.titulo)

    def exportar_dashboard(self, arquivo=None):
        df = self.gerar()
        fig = self.gerar_grafico(df)
        fig.write_image("grafico.png")

        if arquivo is None:
            arquivo = f"{self.__class__.__name__}_{date.today()}.xlsx"

        with pd.ExcelWriter(arquivo, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Dados", index=False)
            worksheet = writer.sheets["Dados"]
            worksheet.insert_image("F2", "grafico.png", {"x_scale": 0.8, "y_scale": 0.8})

        print(f"✅ Relatório exportado como {arquivo}")


class RelatorioEstoque(RelatoriosBase):
    def __init__(self, arquivo='C:/Users/phbat/OneDrive/Desktop/DCK/src/utils/estoque.csv'):
        self.estoque = arquivo

    def gerar(self) -> pd.DataFrame:
        df = pd.read_csv(self.estoque, encoding='utf-8', sep=',')
        filtro = df[['modelo','quantidade']]
        return filtro

    @property
    def coluna_y(self) -> str:
        return "quantidade"










