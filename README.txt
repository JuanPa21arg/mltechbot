MLTechBot - Sistema completo de WhatsApp con IA, pagos y panel

1. INSTALACIÓN DE DEPENDENCIAS
--------------------------------
Instalá Flask y extensiones:

pip install flask flask_sqlalchemy flask_login python-dotenv openai

2. CONFIGURAR VARIABLES
-------------------------
Copiá `.env.example` como `.env` y completá:

- OPENAI_API_KEY → tu clave de https://platform.openai.com/
- MERCADOPAGO_ACCESS_TOKEN → tu token de https://www.mercadopago.com.ar/developers/panel

3. INICIAR EL SISTEMA
-------------------------
Desde terminal:

python app.py

Luego andá a:

http://localhost:5000

4. FLUJO DE USO
-------------------------
- Registrate como cliente
- Configurá tu perfil del negocio
- Cargá tus respuestas personalizadas
- El bot usará reglas + IA para responder
- Admin puede activar o suspender cuentas
- Si está inactivo, el bot se bloquea

5. PRÓXIMO PASO
-------------------------
Ejecutar también el bot de WhatsApp con IA (te lo entregamos por separado)

---

Cualquier duda, escribí a soporte@mltechhub.com
¡Gracias por usar MLTechBot!
