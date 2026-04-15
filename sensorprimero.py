from machine import Pin, time_pulse_us
import time

# LEDs
led_verde = Pin(13, Pin.OUT)
led_amarillo = Pin(12, Pin.OUT)
led_rojo = Pin(14, Pin.OUT)

# buzzer
buzzer = Pin(27, Pin.OUT)

# sensor
trig = Pin(5, Pin.OUT)
echo = Pin(18, Pin.IN)


def medir_distancia():

    trig.off()
    time.sleep_us(2)

    trig.on()
    time.sleep_us(10)
    trig.off()

    duracion = time_pulse_us(echo, 1)
    distancia = (duracion * 0.0343) / 2

    return distancia


while True:

    distancia = medir_distancia()
    print("Distancia:", distancia, "cm")

    # LEJOS (verde)
    if distancia > 30:

        led_verde.on()
        led_amarillo.off()
        led_rojo.off()

        buzzer.on()
        time.sleep(0.2)
        buzzer.off()
        time.sleep(1)   # sonido lento


    # DISTANCIA MEDIA (amarillo)
    elif distancia > 15:

        led_verde.off()
        led_amarillo.on()
        led_rojo.off()

        buzzer.on()
        time.sleep(0.15)
        buzzer.off()
        time.sleep(0.15)  # sonido más rápido


    # MUY CERCA (rojo)
    else:

        led_verde.off()
        led_amarillo.off()
        led_rojo.on()

        buzzer.on()  # sonido constante     