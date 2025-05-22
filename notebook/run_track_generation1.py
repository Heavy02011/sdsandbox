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
    print("Verwende Konfiguration aus trackgenlib (via config.yaml):")
    if hasattr(tgl, 'config') and tgl.config:
        print(f"  Track-Breite: {tgl.config.get('track_width')}")
        print(f"  Beispiel Skript-Pfad (Mode 1): {tgl.config.get('script_path_example')}")
        print(f"  Beispiel CSV-Pfad (Mode 2): {tgl.config.get('csv_path_example')}")
        print(f"  Glättungsfenster: {tgl.config.get('smoothing_window')}")
    else:
        print("  FEHLER: tgl.config nicht gefunden oder leer. Stelle sicher, dass trackgenlib.py korrekt initialisiert wird und config.yaml geladen werden kann.")
        return

    # --- Modus und Schließ-Parameter aus config.yaml laden --- 
    mode = tgl.config.get('default_run_mode', 0) # Standardwert 0, falls nicht in config
    create_closed_track = tgl.config.get('create_closed_track_default', True) # Standardwert True

    # --- Überschreiben durch Kommandozeilenargumente --- 
    if len(sys.argv) > 1:
        try:
            mode_arg = int(sys.argv[1])
            if mode_arg not in [0, 1, 2, 3, 4]:
                raise ValueError(f"Modus muss zwischen 0 und 4 liegen, war aber {mode_arg}")
            mode = mode_arg # Überschreibe mit Kommandozeilen-Wert
        except ValueError as e:
            print(f"Ungültiges Argument für Modus: '{sys.argv[1]}'. {e}. Verwende Wert aus config oder Standard: {mode}.")
    
    if len(sys.argv) > 2:
        try:
            val_arg = sys.argv[2].lower()
            if val_arg in ['true', '1', 'yes']:
                create_closed_track = True # Überschreibe mit Kommandozeilen-Wert
            elif val_arg in ['false', '0', 'no']:
                create_closed_track = False # Überschreibe mit Kommandozeilen-Wert
            else:
                raise ValueError(f"Argument für geschlossenen Track muss True/False sein, war aber {val_arg}")
        except ValueError as e:
            print(f"Ungültiges Argument für geschlossenen Track: '{sys.argv[2]}'. {e}. Verwende Wert aus config oder Standard: {create_closed_track}.")
    
    print(f"\nGewählter Modus (ggf. via CLI überschrieben): {mode}")
    print(f"Track soll geschlossen werden (ggf. via CLI überschrieben): {create_closed_track}")

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
    elif mode == 3:
        print("Generiere festen Polar-Track aus config (polar_angles_fixed, polar_distances_fixed)...")
        # Die Funktion generate_polar_track greift direkt auf die config zu, wenn angles/distances None sind.
        centerline = tgl.generate_polar_track(closed_track=create_closed_track)
    elif mode == 4:
        print("Generiere zufälligen Polar-Track mit konfigurierten Bereichen...")
        # Parameter direkt aus der config holen
        angle_min, angle_max = tgl.config.get('polar_angle_range_random', [0, 359]) # Standard falls nicht in config
        dist_min, dist_max = tgl.config.get('polar_distance_range_random', [5.0, 20.0])
        num_points = tgl.config.get('num_points_polar_random', 15)
        
        import random
        import numpy as np
        import math
        
        # Verbesserte Ankerpunkterzeugung für interessantere Strecken
        # Wir verwenden eine Kombination aus regelmäßiger Anordnung und zufälligen Distanzen
        
        # 1. Erzeuge Winkel mit kontrollierter Verteilung
        angle_step = 360.0 / num_points
        angles_random = []
        for i in range(num_points):
            base_angle = i * angle_step
            # Variable Jitter-Größe für mehr Abwechslung
            # Jitter ist größer bei späteren Punkten, um mehr Variation zu erzielen
            jitter_percent = 0.1 + (i / num_points * 0.2)  # 10-30% Jitter
            jitter = random.uniform(-jitter_percent * angle_step, jitter_percent * angle_step)
            angles_random.append((base_angle + jitter) % 360)
        
        # Sortieren für konsistente Reihenfolge
        angles_random.sort()
        
        # 2. Erzeuge interessantere Distanzmuster mit verbesserten Geometrien
        # Wähle ein zufälliges Muster: Ellipse, Stern, Welle oder Dreiecksform
        # 'complex' kombiniert mehrere Muster für anspruchsvollere Strecken
        pattern_type = random.choice(['ellipse', 'star', 'wave', 'triangle', 'complex'])
        print(f"Erzeuge Track mit Muster-Typ: {pattern_type}")
        
        base_distance = (dist_min + dist_max) / 2.0
        amplitude = (dist_max - dist_min) / 2.0 * 0.8  # 80% des halben Bereichs für kontrollierte Variation
        
        distances_random = []
        
        # Parameter für komplexere Muster
        eccentricity = random.uniform(0.35, 0.65)  # Parameter für Ellipsen
        rotation = random.uniform(0, 2 * math.pi)  # Zufällige Drehung für alle Muster
        n_star_points = random.randint(3, 6)  # Anzahl der Spitzen für den Stern
        phases = [random.uniform(0, 2*math.pi) for _ in range(3)]  # Phasenverschiebungen für Wellen
        
        for i, angle in enumerate(angles_random):
            angle_rad = math.radians(angle)
            rotated_angle = angle_rad + rotation  # Angewendete Rotation für alle Muster
            dist = base_distance  # Standarddistanz
            
            if pattern_type == 'ellipse':
                # Verbesserte Ellipse mit kontrollierten Parametern
                # Ellipsengleichung: r = a(1-e²)/(1-e*cos(θ)) wobei e = Exzentrizität
                dist = base_distance * (1 - eccentricity**2) / (1 - eccentricity * math.cos(rotated_angle))
                # Begrenzen, um sicherzustellen, dass wir im gewünschten Bereich bleiben
                dist = min(dist, dist_min + amplitude * 1.8)  # Vermeide zu große Ausschläge
                
            elif pattern_type == 'star':
                # Verbessertes Sternmuster mit variabler Spitzenzahl
                # Für n Spitzen verwenden wir eine Sinusfunktion mit n/2 Perioden
                # Die Multiplikation mit n_star_points erzeugt die Anzahl von "Zacken"
                star_factor = abs(math.cos(n_star_points * rotated_angle / 2))
                # Verwende Potenz für schärfere Spitzen
                star_factor = star_factor ** 0.5  # Quadratwurzel für weniger extreme Spitzen
                dist = base_distance - amplitude * (1 - star_factor)
                
            elif pattern_type == 'wave':
                # Multi-Frequenz-Welle mit Phasenverschiebungen für organischere Formen
                freq1 = random.uniform(2, 4)  # Niedrigere Frequenz
                freq2 = random.uniform(4, 7)  # Mittlere Frequenz
                freq3 = random.uniform(8, 12) # Höhere Frequenz
                
                # Komponenten mit unterschiedlichen Gewichtungen und Phasen
                wave1 = math.sin(rotated_angle * freq1 + phases[0]) * 0.6
                wave2 = math.sin(rotated_angle * freq2 + phases[1]) * 0.3
                wave3 = math.sin(rotated_angle * freq3 + phases[2]) * 0.1
                
                combined_wave = wave1 + wave2 + wave3
                dist = base_distance + amplitude * combined_wave
                
            elif pattern_type == 'triangle':
                # Dreieckige oder polygonale Form
                # Wir verwenden eine Funktion, die bei bestimmten Winkeln Maxima hat
                n_sides = random.randint(3, 6)  # Anzahl der Seiten des Polygons
                polygon_factor = abs(math.cos(n_sides * rotated_angle / 2))
                # Potenz für schärfere Ecken
                polygon_factor = polygon_factor ** 2  # Quadrat für schärfere Ecken
                dist = base_distance - amplitude * 0.7 * (1 - polygon_factor)
                
            elif pattern_type == 'complex':
                # Kombination verschiedener Muster für komplexere Strecken
                # Zufällige Gewichtung der verschiedenen Komponenten
                ellipse_weight = random.uniform(0.3, 0.7)
                wave_weight = 1 - ellipse_weight
                
                # Elliptische Komponente
                ellipse_component = base_distance * (1 - eccentricity * math.cos(rotated_angle))
                
                # Wellenkomponente mit mehreren Frequenzen
                freq = random.uniform(2, 5)
                wave_component = math.sin(rotated_angle * freq + phases[0]) * amplitude
                
                # Kombination
                dist = ellipse_weight * ellipse_component + wave_weight * (base_distance + wave_component)
            
            # Füge etwas Zufälligkeit hinzu - reduziert für konsistentere Ergebnisse
            random_factor = random.uniform(-0.05, 0.05) * amplitude
            dist += random_factor
            
            # Begrenzen auf erlaubten Bereich
            dist = max(min(dist, dist_max), dist_min)
            distances_random.append(dist)
        
        # Das smoothing_window wird von generate_polar_track intern aus der Config gelesen
        # centerline = tgl.generate_polar_track(angles=angles_random, distances=distances_random,
        #                                       closed_track=create_closed_track)

        # NEU: Verwende generate_random_polar_arc_track für Mode 4
        print("Verwende generate_random_polar_arc_track für Mode 4...")
        centerline = tgl.generate_random_polar_arc_track(angles_deg=angles_random, 
                                                         distances=distances_random,
                                                         closed_track=create_closed_track)
    else:
        print(f"Ungültiger Modus: {mode}. Bitte wähle 0, 1, 2, 3 oder 4.")
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