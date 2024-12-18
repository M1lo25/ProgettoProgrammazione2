import socket
import random
import pickle

# Definizione dei semi e dei valori delle carte
semi = ['Bastoni', 'Denari', 'Spadi', 'Coppe']
valori = {                                                     
    'Re': 0.5, 'Cavallo': 0.5, 'Fante': 0.5,
    'Asso': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7
}

# Definizione delle funzioni per creare il mazzo, pescare una carta, calcolare il punteggio e la probabilità di sballare

def crea_mazzo():
    mazzo = [(valore, seme, punti) for valore, punti in valori.items() for seme in semi]
    random.shuffle(mazzo)
    return mazzo

def pesca_carta(mazzo):
    return mazzo.pop()

def calcola_punteggio(carte):
    return sum(carta[2] for carta in carte)

def calcola_probabilita_sballare(punteggio_attuale, mazzo):
    carte_sballo = sum(1 for carta in mazzo if punteggio_attuale + carta[2] > 7.5)
    return carte_sballo / len(mazzo)

# Creazione del socket server e inizio dell'ascolto sulla porta 5000
socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_server.bind(('localhost', 5000))
socket_server.listen(1)
print("Server in ascolto sulla porta 5000...")

# Accettazione delle connessioni e gestione del gioco+
while True:                                                                    
    socket_cliente, indirizzo = socket_server.accept()
    print(f"Connessione stabilita con {indirizzo}")

    giocando = True
    while giocando:
        mazzo = crea_mazzo()
        carte_giocatore = []
        carte_banco = []

        while True:
            dati = socket_cliente.recv(1024) # Ricezione della richiesta del giocatore
            if not dati:
                giocando = False
                break

            richiesta = pickle.loads(dati)
            if richiesta == 'pescare':
                carta = pesca_carta(mazzo) # Pesca una carta dal mazzo
                if carta[0] == 'Re' and carta[1] == 'Denari':
                    socket_cliente.send(pickle.dumps('Re di Denari'))
                    valore = float(socket_cliente.recv(1024).decode())
                    carta = (carta[0], carta[1], valore)
                carte_giocatore.append(carta)
                punteggio = calcola_punteggio(carte_giocatore)
                risposta = (carta, punteggio)
                socket_cliente.send(pickle.dumps(risposta)) # invia i dettagli della carta pescata al giocatore

                if punteggio > 7.5:
                    socket_cliente.send(pickle.dumps("Hai sballato! Hai perso."))
                    break
                elif punteggio == 7.5:
                    socket_cliente.send(pickle.dumps("Hai fatto 7 e mezzo! Hai vinto!"))
                    break

            elif richiesta == 'fermare':
                punteggio_giocatore = calcola_punteggio(carte_giocatore)
                while True:
                    punteggio_banco = calcola_punteggio(carte_banco)
                    if punteggio_banco >= 5.5 and punteggio_banco >= punteggio_giocatore:
                        break
                    if calcola_probabilita_sballare(punteggio_banco, mazzo) > 0.5:
                        break
                    carta = pesca_carta(mazzo)
                    if carta[0] == 'Re' and carta[1] == 'Denari':
                        possibili_valori = [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7]
                        miglior_valore = min(possibili_valori, key=lambda x: abs(7.5 - (punteggio_banco + x)))
                        carta = (carta[0], carta[1], miglior_valore)
                    carte_banco.append(carta)

                punteggio_banco = calcola_punteggio(carte_banco)
                if punteggio_banco > 7.5 or punteggio_giocatore > punteggio_banco:
                    risultato = "Hai vinto!"
                elif punteggio_giocatore < punteggio_banco:
                    risultato = "Hai perso!"
                else:
                    risultato = "Pareggio!"
                socket_cliente.send(pickle.dumps((punteggio_banco, risultato)))
                break

        richiesta_rigiocare = socket_cliente.recv(1024)
        if pickle.loads(richiesta_rigiocare) != 'riavviare':
            giocando = False

    socket_cliente.close()
