import network
import socket
from machine import Pin, time_pulse_us
import time
import _thread

# --- HARDWARE ---
led_verde = Pin(13, Pin.OUT)
led_amarillo = Pin(12, Pin.OUT)
led_rojo = Pin(14, Pin.OUT)
buzzer = Pin(27, Pin.OUT)
trig = Pin(5, Pin.OUT)
echo = Pin(18, Pin.IN)

# --- VARIABLES ---
distancia_actual = 0.0
distancia_minima = 999.0
historial = [0] * 10 

# --- WIFI AP ---
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid="Radar_ESP32", password="")

# --- HTML (Con Círculos de Colores Dinámicos) ---
def obtener_html():
    return """<!DOCTYPE html><html><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; text-align: center; background: #121212; color: white; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 15px; display: inline-block; margin-top: 20px; width: 90%; }
        .dato { font-size: 3em; color: #00e676; font-weight: bold; }
        
        /* Estilo de los círculos indicadores */
        .indicadores { margin: 20px 0; }
        .circulo { width: 40px; height: 40px; border-radius: 50%; display: inline-block; margin: 0 10px; background: #333; transition: 0.2s; border: 2px solid #555; }
        
        svg { background: #000; border-radius: 10px; width: 100%; height: 150px; margin-bottom: 15px; }
        polyline { fill: none; stroke: #00e676; stroke-width: 3; }
        .bar-container { background: #333; height: 20px; border-radius: 10px; margin: 20px 0; overflow: hidden; }
        #bar { background: #00e676; height: 100%; width: 0%; transition: width 0.2s; }
        button { background: #d32f2f; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; font-size: 16px; }
    </style></head><body>
    <div class="card">
        <h1>RADAR ESP32</h1>
        
        <div class="indicadores">
            <div id="cV" class="circulo"></div>
            <div id="cA" class="circulo"></div>
            <div id="cR" class="circulo"></div>
        </div>

        <div id="dist" class="dato">0.0 cm</div>
        
        <svg viewBox="0 0 100 100" preserveAspectRatio="none">
            <polyline id="linea" points="0,100 100,100"/>
        </svg>

        <div class="bar-container"><div id="bar"></div></div>
        <p>Mínima: <span id="min">999</span> cm</p>
        <button onclick="fetch('/reset')">CALIBRAR / RESET</button>
    </div>
    <script>
        setInterval(() => {
            fetch('/update').then(r => r.json()).then(data => {
                let d = data.d;
                document.getElementById('dist').innerText = d.toFixed(1) + " cm";
                document.getElementById('min').innerText = data.m.toFixed(1);
                
                // Actualizar barra
                document.getElementById('bar').style.width = Math.min(d, 100) + "%";
                
                // Lógica de los Círculos en el Celular
                document.getElementById('cV').style.background = (d > 30) ? "#00ff00" : "#333";
                document.getElementById('cA').style.background = (d <= 30 && d > 15) ? "#ffff00" : "#333";
                document.getElementById('cR').style.background = (d <= 15) ? "#ff0000" : "#333";
                
                // Sombras de luz (glow)
                document.getElementById('cV').style.boxShadow = (d > 30) ? "0 0 15px #00ff00" : "none";
                document.getElementById('cA').style.boxShadow = (d <= 30 && d > 15) ? "0 0 15px #ffff00" : "none";
                document.getElementById('cR').style.boxShadow = (d <= 15) ? "0 0 15px #ff0000" : "none";

                // Gráfica
                let pts = "";
                for(let i=0; i<data.h.length; i++){
                    pts += (i * 11.1) + "," + (100 - Math.min(data.h[i], 100)) + " ";
                }
                document.getElementById('linea').setAttribute("points", pts);
            }).catch(e => {});
        }, 500);
    </script></body></html>"""

# --- SERVIDOR WEB ---
def servidor_web():
    global distancia_minima
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 80))
    s.listen(1)
    while True:
        try:
            conn, addr = s.accept()
            request = conn.recv(1024).decode()
            if '/update' in request:
                res = '{"d":' + str(distancia_actual) + ',"m":' + str(distancia_minima) + ',"h":' + str(historial) + '}'
                conn.send('HTTP/1.1 200 OK\nContent-Type: application/json\n\n' + res)
            elif '/reset' in request:
                distancia_minima = 999.0
                conn.send('HTTP/1.1 200 OK\n\nOK')
            else:
                conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\n\n' + obtener_html())
            conn.close()
        except: pass

_thread.start_new_thread(servidor_web, ())

# --- BUCLE PRINCIPAL (Tu lógica original intacta) ---
while True:
    trig.off()
    time.sleep_us(2)
    trig.on()
    time.sleep_us(10)
    trig.off()
    dur = time_pulse_us(echo, 1, 30000)
    dist = (dur * 0.0343) / 2 if dur > 0 else 400.0
    distancia_actual = dist
    
    historial.pop(0)
    historial.append(dist)
    
    if dist < distancia_minima:
        distancia_minima = dist

    # Alertas (Hardware)
    if dist > 30:
        led_verde.on(); led_amarillo.off(); led_rojo.off()
        buzzer.on(); time.sleep(0.1); buzzer.off(); time.sleep(0.5)
    elif dist > 15:
        led_verde.off(); led_amarillo.on(); led_rojo.off()
        buzzer.on(); time.sleep(0.1); buzzer.off(); time.sleep(0.1)
    else:
        led_verde.off(); led_amarillo.off(); led_rojo.on()
        buzzer.on(); time.sleep(0.05); buzzer.off(); time.sleep(0.05)