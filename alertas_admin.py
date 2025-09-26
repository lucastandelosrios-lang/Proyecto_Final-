import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
import os
import tempfile
from datetime import datetime

# -------------------
# Cargar credenciales
# -------------------
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

# -------------------
# Configuración
# -------------------
DATA_FILE = "datos_trabajo_FGN.csv"
DIAS_ALERTA = 180

# Correos de administradores
ADMIN_CORREOS = [
    "lucastandelosrios@gmail.com",
    "admin2@fiscalia.gov"
]

# -------------------
# Cargar datos
# -------------------
df = pd.read_csv(DATA_FILE)
df["FECHA ENTRADA"] = pd.to_datetime(df["FECHA ENTRADA"], errors="coerce")
df["TIEMPO_CUSTODIA(DIAS)"] = pd.to_numeric(df["TIEMPO_CUSTODIA(DIAS)"], errors="coerce")

df_alerta = df[df["TIEMPO_CUSTODIA(DIAS)"] > DIAS_ALERTA].copy()
df_alerta = df_alerta[[
    "SECCIONAL", "DEPENDENCIA PADRE", "NOMBRE RESPESPONSABLE",
    "NRO PROCESO", "PLACA SIAF", "FECHA ENTRADA", "TIEMPO_CUSTODIA(DIAS)"
]]

# -------------------
# Generar Excel con pestañas
# -------------------
def generar_excel(df_alerta):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        with pd.ExcelWriter(tmp.name, engine="openpyxl") as writer:
            for responsable, df_responsable in df_alerta.groupby("NOMBRE RESPESPONSABLE"):
                hoja = responsable[:30] if pd.notna(responsable) else "Sin_Responsable"
                df_responsable.to_excel(writer, sheet_name=hoja, index=False)
        return tmp.name

# -------------------
# Enviar correo a admins
# -------------------
def enviar_reporte(destinatarios, df_alerta):
    remitente = EMAIL_USER
    password = EMAIL_PASS

    asunto = f"[Reporte Consolidado] Vehículos > {DIAS_ALERTA} días - {datetime.today().date()}"
    cuerpo = (
        f"Se generó el reporte consolidado de vehículos con más de {DIAS_ALERTA} días en custodia.\n\n"
        "Cada pestaña en el Excel corresponde a un responsable.\n\n"
        "Atentamente,\nSistema de Alertas Automáticas"
    )

    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = ", ".join(destinatarios)
    msg["Subject"] = asunto
    msg.attach(MIMEText(cuerpo, "plain"))

    excel_path = generar_excel(df_alerta)
    with open(excel_path, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="xlsx")
        attach.add_header("Content-Disposition", "attachment", filename="reporte_consolidado.xlsx")
        msg.attach(attach)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(remitente, password)
        server.send_message(msg)

# -------------------
# Ejecutar
# -------------------
if len(df_alerta) > 0:
    enviar_reporte(ADMIN_CORREOS, df_alerta)
    print(f"✅ Reporte consolidado enviado a administradores: {', '.join(ADMIN_CORREOS)}")
else:
    print("ℹ️ No hay vehículos en alerta para consolidar.")



