
import sys
import io
from pathlib import Path

import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QTextEdit, QMessageBox
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class inventario(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("inventario de sucursales")
        self.resize(1100, 730)

        # archivo csv
        archivo = Path(__file__).parent / "Datos Utilizados.csv"
        self.datos = pd.read_csv(
            archivo, sep=None, engine="python", encoding="utf-8-sig"
        )

        self.datos["Cantidad"] = pd.to_numeric(self.datos["Cantidad"])
        self.datos["Stock_Minimo"] = pd.to_numeric(self.datos["Stock_Minimo"])
        self.datos["Precio_Unitario_USD"] = pd.to_numeric(
            self.datos["Precio_Unitario_USD"]
        )
        self.datos["Valor_Total"] = (
            self.datos["Cantidad"] * self.datos["Precio_Unitario_USD"]
        )

        # ventanas
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f9;
                font-family: Segoe UI;
                font-size: 12px;
            }
            QLabel#titulo {
                font-size: 23px;
                font-weight: bold;
                color: #17365d;
            }
            QLabel#resumen {
                background: white;
                padding: 14px;
                border: 1px solid #dce3eb;
            }
            QComboBox {
                background: white;
                padding: 7px;
                border: 1px solid #cfd8e3;
            }
            QTabWidget::pane {
                background: white;
                border: 1px solid #dce3eb;
            }
            QTabBar::tab {
                padding: 9px 15px;
                background: #e4eaf2;
            }
            QTabBar::tab:selected {
                background: #17365d;
                color: white;
            }
            QTableWidget, QTextEdit {
                background: white;
            }
        """)

        principal = QVBoxLayout(self)

        titulo = QLabel("control de inventario")
        titulo.setObjectName("titulo")
        principal.addWidget(titulo)

        principal.addWidget(
            QLabel("consulta de productos de las cinco sucursales")
        )

        # seleccion de sucursal
        fila = QHBoxLayout()
        fila.addWidget(QLabel("seleccionar sucursal:"))

        self.combo = QComboBox()
        self.combo.addItem("todas")
        self.combo.addItems(
            sorted(self.datos["Sucursal"].dropna().unique())
        )

        fila.addWidget(self.combo)
        fila.addStretch()
        principal.addLayout(fila)

        # resumen del inventario
        self.resumen = QLabel()
        self.resumen.setObjectName("resumen")
        principal.addWidget(self.resumen)

        # pestanas
        pestanas = QTabWidget()
        principal.addWidget(pestanas)

        # primera pestana: graficos
        pagina_graficos = QWidget()
        diseno_graficos = QVBoxLayout(pagina_graficos)

        self.figura = Figure(figsize=(9, 4))
        self.lienzo = FigureCanvas(self.figura)

        diseno_graficos.addWidget(self.lienzo)
        pestanas.addTab(pagina_graficos, "graficos")

        # segunda pestana: inventario
        self.tabla = QTableWidget()
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        pestanas.addTab(self.tabla, "inventario")

        # tercera pestana: analisis con pandas
        self.analisis = QTextEdit()
        self.analisis.setReadOnly(True)
        self.analisis.setStyleSheet(
            "font-family: Consolas; font-size: 12px;"
        )
        pestanas.addTab(self.analisis, "analisis de datos")

        self.combo.currentTextChanged.connect(self.actualizar)
        self.actualizar()

    def actualizar(self):
        # filtrar por sucursal
        sucursal = self.combo.currentText()

        if sucursal == "todas":
            df = self.datos.copy()
        else:
            df = self.datos[
                self.datos["Sucursal"] == sucursal
            ]

        # calcular informacion general
        cantidad = df["Cantidad"].sum()
        valor = df["Valor_Total"].sum()
        bajos = (
            df["Cantidad"] < df["Stock_Minimo"]
        ).sum()

        self.resumen.setText(
            f"registros: {len(df)}     |     "
            f"unidades: {cantidad:,}     |     "
            f"valor del inventario: ${valor:,.2f}     |     "
            f"productos con stock bajo: {bajos}"
        )

        # mostrar los datos en la tabla
        columnas = list(df.columns)

        self.tabla.setRowCount(len(df))
        self.tabla.setColumnCount(len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)

        for fila, (_, producto) in enumerate(df.iterrows()):
            for columna, nombre in enumerate(columnas):
                self.tabla.setItem(
                    fila,
                    columna,
                    QTableWidgetItem(str(producto[nombre]))
                )

        self.tabla.resizeColumnsToContents()

        # graficos de matplotlib
        self.figura.clear()

        grafico1 = self.figura.add_subplot(121)
        grafico2 = self.figura.add_subplot(122)

        # grafico de cantidades por sucursal
        unidades = df.groupby("Sucursal")["Cantidad"].sum()

        grafico1.bar(
            unidades.index,
            unidades.values,
            color="#4472c4"
        )
        grafico1.set_title("unidades por sucursal")
        grafico1.set_ylabel("cantidad")
        grafico1.tick_params(
            axis="x", labelrotation=35, labelsize=8
        )

        # grafico del valor de las categorias
        categorias = (
            df.groupby("Categoria")["Valor_Total"]
            .sum()
            .sort_values()
        )

        grafico2.barh(
            categorias.index,
            categorias.values,
            color="#36a89b"
        )
        grafico2.set_title("valor por categoria (usd)")
        grafico2.set_xlabel("dolares")
        grafico2.tick_params(axis="y", labelsize=8)

        self.figura.tight_layout()
        self.lienzo.draw()

        # analisis estadistico utilizando pandas
        informacion = io.StringIO()
        df.info(buf=informacion)

        texto = (
            "1. primeros registros (head)\n"
            + df.head().to_string(index=False)
            + "\n\n2. estructura de los datos (info)\n"
            + informacion.getvalue()
            + "\n3. tipos de datos (dtypes)\n"
            + df.dtypes.to_string()
            + "\n\n4. estadisticas basicas (describe)\n"
            + df.describe().round(2).to_string()
            + "\n\n5. datos vacios (isnull)\n"
            + df.isnull().sum().to_string()
        )

        self.analisis.setPlainText(texto)


# iniciar programa
app = QApplication(sys.argv)

try:
    ventana = inventario()
    ventana.show()
    sys.exit(app.exec_())
except Exception as error:
    QMessageBox.critical(None, "error", str(error))
