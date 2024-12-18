import pygame
import pickle
import socket
import sys
import time

pygame.init()


socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Creazione del socket client e connessione al server
socket_cliente.connect(('localhost', 5000))

schermo = pygame.display.set_mode((800,600))
pygame.display.set_caption("Gioco del 7 e Mezzo")

# Impostazione della finestra di gioco e dei colori
BIANCO = (255, 255, 255)
NERO = (0, 0, 0)
VERDE = (34, 139, 34)
MARRONE = (139, 69, 19)                              
ORO = (212, 175, 55)

font_principale = pygame.font.SysFont("georgia", 32)
font_piccolo = pygame.font.SysFont("georgia", 18)
font_grande = pygame.font.SysFont("georgia", 80, bold=True)
font_medio = pygame.font.SysFont("georgia", 25)
font_largo = pygame.font.SysFont("georgia", 50)
font_intermedio = pygame.font.SysFont("georgia", 37, bold=True)

# Definizione delle funzioni per disegnare il testo e caricare le immagini delle carte
def disegna_testo(testo, font, colore, superficie, x, y, ombra=False):
    if ombra:
        colore_ombra = (0, 0, 0)
        oggetto_testo = font.render(testo, True, colore_ombra)
        rettangolo_testo = oggetto_testo.get_rect(center=(x+2, y+2))
        superficie.blit(oggetto_testo, rettangolo_testo)
    oggetto_testo = font.render(testo, True, colore)
    rettangolo_testo = oggetto_testo.get_rect(center=(x, y))    
    superficie.blit(oggetto_testo, rettangolo_testo)

def carica_immagine_carta(carta):
    valore, seme = carta[:2]
    nome_file = f"carte/{valore}_di_{seme}.jpg"
    try:
        #carica l'immagine,ridimensiona alle dimensioni 80x120
        return pygame.transform.scale(pygame.image.load(nome_file).convert_alpha(), (80, 120)) 
    except FileNotFoundError:
        print(f"Immagine della carta {nome_file} non trovata.")
        return None

# Definizione della funzione per mostrare la schermata di riavvio
def mostra_schermata_riavvio(messaggio):        
    schermo.fill(VERDE)  
    disegna_testo(messaggio, font_grande, (120, 0, 0), schermo, 400, 200)  
    disegna_testo("Premi 'S' per rigiocare o 'Q' per uscire", font_medio, NERO, schermo, 400, 500)
    pygame.display.flip()

scroll_offset_x = 0  
scroll_speed = 40    
max_scroll = 0       
larghezza_carta = 100
spaziatura = 50

# Ciclo principale del gioco 
giocando = True
while giocando:
    punteggio_giocatore = 0
    carte = []
    messaggio = "Vuoi pescare una carta?"
    fine_gioco = False
    messaggio_risultato = ""
    in_esecuzione = True

    while in_esecuzione:
        schermo.fill(VERDE)                                                                                   

        rettangolo_tavolo = pygame.Rect(0, 200, 800, 200)  
        pygame.draw.rect(schermo, MARRONE, rettangolo_tavolo, border_radius=10)

        # Calcola lo spazio totale occupato dalle carte
        spazio_totale_carte = len(carte) * (larghezza_carta + spaziatura)
        max_scroll = max(0, spazio_totale_carte - 800)  # 800 è la larghezza dello schermo

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                in_esecuzione = False
                giocando = False
                socket_cliente.close()
                pygame.quit()
                sys.exit()
    
            # Controlla solo eventi KEYDOWN
            elif evento.type == pygame.KEYDOWN:  
                if evento.key == pygame.K_LEFT:  # Freccia sinistra
                    scroll_offset_x = min(scroll_offset_x + scroll_speed, 0)
                elif evento.key == pygame.K_RIGHT:  # Freccia destra
                    scroll_offset_x = max(scroll_offset_x - scroll_speed, -max_scroll)
                elif evento.key == pygame.K_s and not fine_gioco:  # Pesca una carta
                    socket_cliente.send(pickle.dumps('pescare')) 
                    dati = socket_cliente.recv(1024)
                    if pickle.loads(dati) == 'Re di Denari':
                        while True:
                            try:
                                valore = float(input("Hai pescato il Re di Denari! Scegli il valore (da 1 a 7): "))
                                if 1 <= valore <= 7:
                                    break
                                else:
                                    print("Valore non valido. Inserisci un numero tra 1 e 7.")
                            except ValueError:
                                print("Input non valido. Inserisci un numero.")
                        socket_cliente.send(str(valore).encode())
                        dati = socket_cliente.recv(1024)
                    carta, punteggio_giocatore = pickle.loads(dati)
                    carte.append(carta)
                    if punteggio_giocatore >= 7.5:
                        risultato = socket_cliente.recv(1024)
                        messaggio_risultato = pickle.loads(risultato)
                        fine_gioco = True
                elif evento.key == pygame.K_n and not fine_gioco:  # Fermati
                    socket_cliente.send(pickle.dumps('fermare'))
                    dati = socket_cliente.recv(1024)
                    punteggio_banco, risultato = pickle.loads(dati)
                    messaggio_risultato = f"Il banco ha: {punteggio_banco}. {risultato}"
                    fine_gioco = True

        x_offset = 70 
        padding = 20 

        # Disegno delle carte con lo scorrimento orizzontale
        x_offset = scroll_offset_x + spaziatura  # Inizia dallo scorrimento orizzontale
        for indice, carta in enumerate(carte):
            immagine_carta = carica_immagine_carta(carta)
            if immagine_carta:
                schermo.blit(immagine_carta, (x_offset, 220))  # Posiziona l'immagine
                nome_carta = f"{carta[0]} di {carta[1]}"
                testo = font_piccolo.render(nome_carta, True, BIANCO)
                larghezza_testo = testo.get_width()  # Calcola la larghezza del testo
                x_centro_testo = x_offset + (80 // 2) - (larghezza_testo // 2)  # Centra il testo orizzontalmente
                schermo.blit(testo, (x_centro_testo, 350))  # Posiziona il testo centrato
            x_offset += larghezza_carta + spaziatura  # Incrementa la posizione per la prossima carta

        # Disegna la barra di scorrimento orizzontale
        if spazio_totale_carte > 0:
            scrollbar_lunghezza = max(100, 800 * 800 // spazio_totale_carte) 
        else:
            scrollbar_lunghezza = 800  # La barra di scorrimento occupa tutta la larghezza quando non ci sono carte
        scrollbar_pos = -scroll_offset_x * (800 - scrollbar_lunghezza) // max_scroll if max_scroll > 0 else 0
        pygame.draw.rect(schermo, BIANCO, (scrollbar_pos, 580, scrollbar_lunghezza, 10))

        disegna_testo(f"Punteggio: {punteggio_giocatore}", font_principale, BIANCO, schermo, 680, 50)
        disegna_testo(messaggio, font_largo, BIANCO, schermo, 400, 490)
        disegna_testo("Premi 'S' per pescare, 'N' per fermarti", font_medio, BIANCO, schermo, 400, 540)

        if fine_gioco:
            disegna_testo(messaggio_risultato, font_intermedio, (120, 0, 0), schermo, 400, 140)  
            pygame.display.flip()
            time.sleep(2)
            mostra_schermata_riavvio("Vuoi rigiocare?")

            aspettando_input = True
            while aspettando_input:
                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        aspettando_input = False
                        giocando = False
                        socket_cliente.close()
                        pygame.quit()
                        sys.exit()
                    elif evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_s:
                            socket_cliente.send(pickle.dumps('riavviare'))
                            aspettando_input = False
                        elif evento.key == pygame.K_q:
                            socket_cliente.send(pickle.dumps('uscire'))
                            giocando = False
                            aspettando_input = False
            in_esecuzione = False

        pygame.display.flip()

pygame.quit()
socket_cliente.close()




