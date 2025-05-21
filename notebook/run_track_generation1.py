import sys
import os

# Stelle sicher, dass das aktuelle Verzeichnis im sys.path ist,
# damit trackgenlib gefunden wird, wenn das Skript von woanders ausgeführt wird.
# Das ist besonders nützlich, wenn trackgenlib.py im selben Verzeichnis liegt.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    import trackgenlib as tgl
except ImportError as e:
    print(f"FEHLER: Konnte trackgenlib nicht importieren: {e}")
    print("Stelle sicher, dass trackgenlib.py im selben Verzeichnis wie dieses Skript oder im Python-Pfad ist.")
    sys.exit(1)
except Exception as e:
    print(f"Ein unerwarteter Fehler ist beim Importieren von trackgenlib aufgetreten: {e}")
    sys.exit(1)

def main():
    """
    Hauptfunktion zur Generierung und Visualisierung von Tracks.
    """
    print("Starte klassisches Python Track-Generierungs-Skript...")
    print("Verwende Konfiguration aus trackgenlib:")
    if hasattr(tgl, 'config'):
        print(f"  Track-Breite: {tgl.config.get('track_width')}")
        print(f"  Beispiel Skript-Pfad: {tgl.config.get('script_path_example')}")
        print(f"  Beispiel CSV-Pfad: {tgl.config.get('csv_path_example')}")
    else:
        print("  FEHLER: tgl.config nicht gefunden. Stelle sicher, dass trackgenlib.py korrekt initialisiert wird.")
        return

    # --- Modusauswahl ---
    # Ändere diesen Wert, um verschiedene Modi zu testen:
    # 0: Zufälliger Track
    # 1: Skriptbasierter Track (aus config.yaml -> script_path_example)
    # 2: CSV-basierter Track (aus config.yaml -> csv_path_example)
    mode = 0
    
    # --- Parameter für geschlossenen Track ---
    # Ändere diesen Wert auf True, um einen geschlossenen Track zu erzeugen/laden
    create_closed_track = True 

    # Optional: Modus über Kommandozeilenargument erhalten
    # if len(sys.argv) > 1:
    #     try:
    #         mode = int(sys.argv[1])
    #         if mode not in [0, 1, 2]:
    #             raise ValueError
    #     except ValueError:
    #         print(f"Ungültiges Argument für Modus: {sys.argv[1]}. Muss 0, 1 oder 2 sein. Verwende Standardmodus 0.")
    #         mode = 0
    # else:
    #     print("Kein Modus als Kommandozeilenargument übergeben. Verwende Standardmodus 0.")
        
    print(f"\nGewählter Modus: {mode}")

    centerline = None

    # --- Track generieren/laden basierend auf dem Modus ---
    print(f"--- Starte Track-Generierung/Laden für Modus: {mode} ---")
    if mode == 0:
        print("Generiere zufälligen Track...")
        centerline = tgl.generate_random_track(closed_track=create_closed_track)
        if not centerline:
            print("Fehler bei der Generierung des zufälligen Tracks.")
    elif mode == 1:
        script_file = tgl.config.get('script_path_example')
        if not script_file:
            print("FEHLER: 'script_path_example' nicht in der Konfiguration gefunden.")
            return
        print(f"Lade skriptbasierten Track von: {script_file}...")
        if not os.path.exists(script_file):
            print(f"WARNUNG: Skriptdatei {script_file} nicht gefunden. Versuche, Beispieldateien zu erstellen...")
            tgl.ensure_example_files()
            if not os.path.exists(script_file):
                print(f"FEHLER: Skriptdatei {script_file} konnte auch nach Erstellungsversuch nicht gefunden werden.")
                return
        centerline = tgl.load_scripted_track(script_file, closed_track=create_closed_track)
        if not centerline and os.path.exists(script_file):
            print(f"Track aus {script_file} geladen, aber Ergebnis ist leer. Überprüfe Dateiformat.")
    elif mode == 2:
        csv_file = tgl.config.get('csv_path_example')
        if not csv_file:
            print("FEHLER: 'csv_path_example' nicht in der Konfiguration gefunden.")
            return
        print(f"Lade CSV-basierten Track von: {csv_file}...")
        if not os.path.exists(csv_file):
            print(f"WARNUNG: CSV-Datei {csv_file} nicht gefunden. Versuche, Beispieldateien zu erstellen...")
            tgl.ensure_example_files()
            if not os.path.exists(csv_file):
                print(f"FEHLER: CSV-Datei {csv_file} konnte auch nach Erstellungsversuch nicht gefunden werden.")
                return
        centerline = tgl.load_csv_track(csv_file, closed_track=create_closed_track)
        if not centerline and os.path.exists(csv_file):
             print(f"Track aus {csv_file} geladen, aber Ergebnis ist leer. Überprüfe Dateiformat und Inhalt.")
    else:
        print(f"Ungültiger Modus: {mode}. Bitte wähle 0, 1 oder 2.")
        return

    if not centerline:
        print("Keine Mittellinie generiert oder geladen. Breche ab.")
        return

    print(f"Anzahl der Punkte in der Mittellinie: {len(centerline)}")
    if centerline:
        print("Erste 3 Punkte der Mittellinie:", centerline[:3])
        if len(centerline) > 3:
            print("Letzte 3 Punkte der Mittellinie:", centerline[-3:])
    print("--- Ende Track-Generierung/Laden ---")

    # --- Streckenbegrenzungen berechnen und Track darstellen ---
    if len(centerline) < 2:
        print("\nMittellinie hat nicht genügend Punkte (mindestens 2 erforderlich) für die Visualisierung.")
        return

    print("\n--- Starte Track-Visualisierung ---")
    print("Berechne Streckenbegrenzungen...")
    left_border, right_border = tgl.get_track_borders(centerline)

    if not (left_border and right_border and len(left_border) == len(centerline) and len(right_border) == len(centerline)):
        print("FEHLER bei der Berechnung oder Validierung der Streckenbegrenzungen.")
        print(f"  Länge Mittellinie: {len(centerline)}")
        print(f"  Länge Linker Rand: {len(left_border) if left_border else 'N/A'}")
        print(f"  Länge Rechter Rand: {len(right_border) if right_border else 'N/A'}")
        print("  Überprüfe die Mittellinien-Daten und die Funktion 'get_track_borders'.")
        return
        
    print("Streckenbegrenzungen erfolgreich berechnet.")
    print("Stelle Track dar...")
    
    # Definiere einen Präfix für den Dateinamen (kann auch aus config gelesen werden)
    # Zum Beispiel im Unterordner 'output_images' des Notebook-Verzeichnisses
    output_directory = os.path.join(current_dir, 'output_images')
    save_prefix = os.path.join(output_directory, 'generated') 
    
    tgl.plot_track(centerline, left_border, right_border, save_path_prefix=save_prefix)
    print("--- Ende Track-Visualisierung ---")
    print("\nDas Plot-Fenster muss möglicherweise manuell geschlossen werden, um das Skript zu beenden.")

if __name__ == "__main__":
    main()