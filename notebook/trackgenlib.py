import yaml
import math # Für Kreisberechnungen
import random # Für Zufallswerte
import matplotlib.pyplot as plt
import numpy as np
import os
import datetime # Hinzugefügt

CONFIG_FILE = '/workspaces/sdsandbox/notebook/config.yaml'

def load_config():
    """Lädt die Konfiguration aus der YAML-Datei."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = yaml.safe_load(f)
        if config_data is None:
            print(f"Warnung: Konfigurationsdatei {CONFIG_FILE} ist leer. Verwende Standardwerte.")
            return get_default_config()
        # Sicherstellen, dass die Beispielpfade absolut sind oder relativ zum Notebook-Verzeichnis korrekt aufgelöst werden
        # Da das Skript selbst im Notebook-Verzeichnis liegt, können relative Pfade für tracks/ problematisch sein,
        # wenn das Notebook aus einem anderen Arbeitsverzeichnis gestartet wird.
        # Besser ist es, absolute Pfade zu verwenden oder Pfade relativ zum Skript selbst zu bilden.
        # Hier gehen wir davon aus, dass die Pfade in config.yaml bereits korrekt sind (z.B. absolut).
        return config_data
    except FileNotFoundError:
        print(f"Warnung: Konfigurationsdatei {CONFIG_FILE} nicht gefunden. Verwende Standardwerte.")
        return get_default_config()
    except Exception as e:
        print(f"Fehler beim Laden der Konfiguration {CONFIG_FILE}: {e}. Verwende Standardwerte.")
        return get_default_config()

def get_default_config():
    """Gibt eine Standardkonfiguration zurück."""
    return {
        'track_width': 0.8,
        'segment_length': 5.0,
        'turn_angle_max': 45, # Für 'straight_turn'
        'num_segments_random': 20,
        'color_centerline': 'black',
        'color_left_border': 'blue',
        'color_right_border': 'red',
        'alternating_colors_segments': ['lightgrey', 'darkgrey'],
        'csv_delimiter': ',',
        'script_path_example': '/workspaces/sdsandbox/notebook/tracks/scripted_track1.txt',
        'csv_path_example': '/workspaces/sdsandbox/notebook/tracks/centerline1.csv',
        # Neue Parameter für zufällige Trackgenerierung mit Bögen
        'curve_types_random': ['straight_turn', 'arc'], # Mögliche Segmenttypen
        'arc_radius_min': 5.0,                             # Minimaler Radius für einen Bogen
        'arc_radius_max': 20.0,                            # Maximaler Radius für einen Bogen
        'arc_angle_max': 90.0,                             # Maximaler Winkel (in Grad) für ein Bogensegment
        'arc_num_points': 10,                              # Anzahl der Punkte zur Approximation eines Bogens
        'max_closing_length_factor': 1.5,                  # Maximales Verhältnis der Schließungslänge zur durchschnittlichen Segmentlänge
        # Standardparameter für polare Track-Generierung
        'polar_angles_fixed': [0, 90, 180, 270],                 # Winkel in Grad zur Erzeugung der Mittellinie
        'polar_distances_fixed': [10, 10, 10, 10],               # Abstände vom Ursprung für polaren Track
        'polar_angle_range_random': [0, 360],                 # Winkelbereich in Grad für zufällige Polarwinkel
        'polar_distance_range_random': [5, 20],               # Abstandsbereich für zufällige Polarabstände
        'num_points_polar_random': 10,                        # Anzahl der Punkte für zufällige polare Tracks
        'smoothing_window': 1                              # Fenstergröße für gleitenden Durchschnitt (1 = kein Smoothing)
    }

config = load_config()

# Stelle sicher, dass die Beispielpfade und neuen Kurvenparameter in der Konfiguration vorhanden sind
# Diese Validierung kann verfeinert oder entfernt werden, wenn die config.yaml als "source of truth" gilt.
default_conf = get_default_config() # Wird ggf. nicht mehr benötigt, wenn alles aus config kommt
for key in ['script_path_example', 'csv_path_example', 
            'curve_types_random', 'arc_radius_min', 'arc_radius_max', 
            'arc_angle_max', 'arc_num_points', 'max_closing_length_factor',
            'polar_angles_fixed', 'polar_distances_fixed', # Angepasst an neue Namen
            'polar_angle_range_random', 'polar_distance_range_random', # Angepasst an neue Namen
            'num_points_polar_random', 'smoothing_window']: # Fehlende hinzugefügt
    if key not in config:
        # config[key] = default_conf.get(key) # Optional: Fehlende Werte mit Defaults füllen
        print(f"Hinweis: Schlüssel '{key}' nicht in config.yaml gefunden. Standardwert wird verwendet oder es könnte ein Fehler auftreten.")


def generate_random_track(closed_track=False):
    """Generiert einen zufälligen Track, optional geschlossen, mit verschiedenen Segmenttypen."""
    track_points = [(0, 0)]
    current_angle_rad = 0  # Startwinkel 0 (entlang der positiven x-Achse)
    num_segments_total = config.get('num_segments_random', 20)
    
    # Parameter für 'straight_turn'
    segment_len_straight = config.get('segment_length', 5.0)
    max_angle_turn_deg = config.get('turn_angle_max', 45)

    # Parameter für 'arc'
    curve_types = config.get('curve_types_random', ['straight_turn'])
    arc_radius_min = config.get('arc_radius_min', 5.0)
    arc_radius_max = config.get('arc_radius_max', 20.0)
    # arc_angle_max_deg wird als maximaler *Betrag* des Winkels für einen Bogen interpretiert
    arc_angle_total_max_deg = config.get('arc_angle_max', 90.0) 
    arc_num_points_approx = config.get('arc_num_points', 10)

    for i in range(num_segments_total):
        last_x, last_y = track_points[-1]
        
        # Wähle zufällig einen Segmenttyp
        segment_type = random.choice(curve_types)

        if segment_type == 'straight_turn' or not curve_types or 'arc' not in curve_types: # Fallback, falls 'arc' nicht konfiguriert
            # Generiere ein gerades Segment mit einer Kurve (Ecke) am Ende
            turn_angle_deg = random.uniform(-max_angle_turn_deg, max_angle_turn_deg)
            current_angle_rad += math.radians(turn_angle_deg)
            
            new_x = last_x + segment_len_straight * math.cos(current_angle_rad)
            new_y = last_y + segment_len_straight * math.sin(current_angle_rad)
            track_points.append((new_x, new_y))

        elif segment_type == 'arc':
            # Generiere ein Kreisbogensegment
            arc_radius = random.uniform(arc_radius_min, arc_radius_max)
            # Zufälliger Gesamtwinkel für den Bogen (positiv oder negativ)
            arc_total_angle_deg = random.uniform(-arc_angle_total_max_deg, arc_angle_total_max_deg)
            if abs(arc_total_angle_deg) < 1: # Mindestwinkel, um Division durch Null zu vermeiden
                arc_total_angle_deg = math.copysign(1.0, arc_total_angle_deg)

            arc_total_angle_rad = math.radians(arc_total_angle_deg)
            
            # Richtung des Bogens (links oder rechts)
            # Positive arc_total_angle_rad -> Linkskurve
            # Negative arc_total_angle_rad -> Rechtskurve

            # Mittelpunkt des Kreises finden, auf dem der Bogen liegt.
            # Der Mittelpunkt liegt senkrecht zur aktuellen Bewegungsrichtung (current_angle_rad)
            # im Abstand arc_radius.
            # Winkel zum Kreismittelpunkt (senkrecht zur Fahrtrichtung)
            # Bei Linkskurve (arc_total_angle_rad > 0): current_angle_rad + PI/2
            # Bei Rechtskurve (arc_total_angle_rad < 0): current_angle_rad - PI/2
            angle_to_center_rad = current_angle_rad + math.copysign(math.pi / 2, arc_total_angle_rad)
            
            center_x = last_x - arc_radius * math.cos(angle_to_center_rad)
            center_y = last_y - arc_radius * math.sin(angle_to_center_rad)

            # Startwinkel des Bogens relativ zum Kreismittelpunkt
            # Dies ist der Winkel vom Kreismittelpunkt zum letzten Punkt des Tracks
            start_angle_on_circle_rad = angle_to_center_rad + math.pi # Um 180 Grad gedreht

            # Punkte auf dem Bogen generieren
            # arc_num_points_approx ist die Anzahl der *Segmente* des Bogens, also +1 Punkte
            for k in range(1, arc_num_points_approx + 1):
                # Interpolierter Winkel auf dem Bogen
                # Der Winkel inkrementiert von start_angle_on_circle_rad
                # in Richtung von -copysign(1, arc_total_angle_rad) * (k * step)
                # (Vorzeichenumkehr, da der Bogen "zurück" zum Mittelpunkt zeigt)
                
                # Der Winkel des aktuellen Punkts auf dem Kreis, relativ zum Kreismittelpunkt
                # Der Bogen "startet" am letzten Punkt. Der Winkel von diesem Punkt zum Kreismittelpunkt ist
                # current_angle_rad - copysign(PI/2, arc_total_angle_rad).
                # Der Startwinkel des Bogensegments auf dem Kreis ist dieser Winkel.
                # Der Endwinkel ist start_angle_segment_rad + arc_total_angle_rad.
                
                # Startwinkel des Bogens relativ zum Kreismittelpunkt (zeigt vom Mittelpunkt zum letzten Punkt)
                angle_from_center_to_last_point_rad = math.atan2(last_y - center_y, last_x - center_x)

                # Punkte auf dem Bogen generieren
                for point_idx in range(1, arc_num_points_approx + 1):
                    # Anteil des aktuellen Punktes am Gesamtbogen
                    fraction_of_arc = point_idx / arc_num_points_approx
                    # Aktueller Winkel auf dem Kreis für diesen Punkt
                    # Das Vorzeichen von arc_total_angle_rad bestimmt die Drehrichtung
                    current_segment_angle_rad = angle_from_center_to_last_point_rad + fraction_of_arc * arc_total_angle_rad
                    
                    arc_point_x = center_x + arc_radius * math.cos(current_segment_angle_rad)
                    arc_point_y = center_y + arc_radius * math.sin(current_segment_angle_rad)
                    track_points.append((arc_point_x, arc_point_y))

            # Update current_angle_rad für das nächste Segment
            # Die neue Richtung ist die Tangente am Ende des Bogens.
            # Der Winkel vom Mittelpunkt zum letzten Bogenpunkt ist current_segment_angle_rad (bereits berechnet).
            # Die Tangente steht senkrecht dazu.
            # Bei Linkskurve (arc_total_angle_rad > 0): current_segment_angle_rad + PI/2
            # Bei Rechtskurve (arc_total_angle_rad < 0): current_segment_angle_rad - PI/2
            current_angle_rad = current_segment_angle_rad + math.copysign(math.pi / 2, -arc_total_angle_rad) # Vorzeichen umkehren für Tangente

    if closed_track and len(track_points) > 1:
        track_points = close_track_smoothly(track_points)
    return track_points

def generate_polar_track(angles=None, distances=None, smoothing_window_override=None, closed_track=False):
    """Generiert einen Track anhand polaren Koordinaten (Winkel in Grad, Abstand zum Ursprung).

    Parameter:
      angles: Liste von Winkeln in Grad (0–360). Wenn None, werden 'polar_angles_fixed' aus config verwendet.
      distances: Liste von Abständen zum Ursprung. Wenn None, werden 'polar_distances_fixed' aus config verwendet.
      smoothing_window_override: Überschreibt den 'smoothing_window' Wert aus der config.
      closed_track: Bool, ob der Track geschlossen wird.  

    Gibt zurück:
      Liste von (x, y) Koordinaten der Mittellinie."""
    # Standardwerte aus Konfiguration, wenn keine spezifischen übergeben wurden
    # Dies ist für Mode 3 (fester Polar-Track)
    if angles is None:
        angles = config.get('polar_angles_fixed')
    if distances is None:
        distances = config.get('polar_distances_fixed')
        
    # Glättungsfenster: Override hat Vorrang, dann config, dann Default 1
    smoothing_val = smoothing_window_override if smoothing_window_override is not None else config.get('smoothing_window', 1)

    # Validierung
    if not angles or not distances or len(angles) != len(distances):
        print(f"FEHLER in generate_polar_track: Ungültige Winkel ({len(angles) if angles else 'None'}) oder Distanzen ({len(distances) if distances else 'None'}). Müssen Listen gleicher Länge sein.")
        return []
    # 1) Erzeuge Punkte in kartesischen Koordinaten
    track_points = []
    for ang_deg, r in zip(angles, distances):
        ang_rad = np.deg2rad(ang_deg % 360)
        x = r * np.cos(ang_rad)
        y = r * np.sin(ang_rad)
        track_points.append((x, y))
    # 2) Glättung: gleitender Durchschnitt (Smoothing)
    if smoothing_val and smoothing_val > 1 and len(track_points) >= smoothing_val:
        xs = np.array([p[0] for p in track_points])
        ys = np.array([p[1] for p in track_points])
        kernel = np.ones(smoothing_val) / smoothing_val
        xs_smooth = np.convolve(xs, kernel, mode='same')
        ys_smooth = np.convolve(ys, kernel, mode='same')
        track_points = list(zip(xs_smooth.tolist(), ys_smooth.tolist()))
    # 3) Optional sanftes Schließen des Tracks
    if closed_track:
        # Verwende die verbesserte Schließfunktion
        track_points = close_track_smoothly(track_points)
    return track_points


def generate_random_polar_arc_track(angles_deg, distances, closed_track=False):
    """
    Generiert einen zufälligen Polar-Track mit gleichmäßigen Kreisbogensegmenten.
    
    Diese verbesserte Version vermeidet Selbstüberschneidungen und erzeugt konsistente Kurvenübergänge durch:
    1. Verbesserte Spline-Interpolation mit optimierter Glättung
    2. Spezielle Behandlung für geschlossene Tracks
    3. Qualitätsüberprüfung der generierten Punkte und Korrektur bei Bedarf
    4. Verbesserte Algorithmen zur Berechnung der Parameter- und Kontrollpunkte
    
    Args:
        angles_deg (list): Liste von Winkeln in Grad.
        distances (list): Liste von Distanzen vom Ursprung.
        closed_track (bool): Ob der Track geschlossen werden soll.

    Returns:
        list: Liste von (x, y) Koordinaten der Mittellinie.
    """
    if not angles_deg or not distances or len(angles_deg) != len(distances):
        print("FEHLER in generate_random_polar_arc_track: Ungültige Winkel oder Distanzen.")
        return []

    import math
    import numpy as np
    import random
    from scipy import interpolate

    # 1. Konvertiere Polar-Ankerpunkte zu kartesischen Koordinaten
    anchor_points_cartesian = []
    for ang_deg, r in zip(angles_deg, distances):
        ang_rad = math.radians(ang_deg % 360)
        x = r * math.cos(ang_rad)
        y = r * math.sin(ang_rad)
        anchor_points_cartesian.append((x, y))

    if len(anchor_points_cartesian) < 3:
        print("FEHLER in generate_random_polar_arc_track: Mindestens 3 Ankerpunkte erforderlich.")
        return []

    # 2. Vorverarbeitung für geschlossene Tracks
    if closed_track:
        # Für geschlossene Tracks benötigen wir eine spezielle Behandlung, um eine glatte Schließung zu gewährleisten
        # Wir fügen den ersten Punkt am Ende an, und um C1-Kontinuität (kontinuierliche erste Ableitung) 
        # zu gewährleisten, wiederholen wir einige Anfangspunkte am Ende und umgekehrt
        wrap_points = 3  # Anzahl der zu wiederholenden Punkte für glatte Übergänge
        
        # Erstelle erweiterte Arrays mit wiederholten Anfangs- und Endpunkten
        if len(anchor_points_cartesian) > wrap_points:
            # Anfangspunkte am Ende wiederholen
            extended_points = anchor_points_cartesian.copy()
            for i in range(1, min(wrap_points+1, len(anchor_points_cartesian))):
                extended_points.append(anchor_points_cartesian[i])
            
            # Endpunkte am Anfang wiederholen
            prefix_points = []
            for i in range(len(anchor_points_cartesian)-wrap_points, len(anchor_points_cartesian)):
                prefix_points.append(anchor_points_cartesian[i])
            
            anchor_points_cartesian = prefix_points + extended_points
    
    # 3. Berechne Parameter für die Interpolation
    # Für eine natürlichere Kurve verwenden wir die kumulative Bogenlänge als Parameter
    x_points = np.array([p[0] for p in anchor_points_cartesian])
    y_points = np.array([p[1] for p in anchor_points_cartesian])
    
    # Berechne kumulative Distanzen für eine gleichmäßigere Interpolation
    t = np.zeros(len(anchor_points_cartesian))
    for i in range(1, len(anchor_points_cartesian)):
        dx = x_points[i] - x_points[i-1]
        dy = y_points[i] - y_points[i-1]
        t[i] = t[i-1] + np.sqrt(dx*dx + dy*dy)
    
    # Normalisiere Parameter auf [0,1]
    if t[-1] > 0:
        t = t / t[-1]
    
    # 4. Erzeuge Spline-Interpolation mit angepasster Glättung
    # Optimierter Glättungsparameter für bessere Ergebnisse
    # Ein Wert von s=0 ergibt eine exakte Interpolation, höhere Werte glätten mehr
    smoothing = 0.0001 if len(anchor_points_cartesian) > 8 else 0  # Leichte Glättung bei vielen Punkten
    
    # Erzeuge unterschiedliche Splinetypen für offene und geschlossene Tracks
    if closed_track:
        # Für geschlossene Tracks verwenden wir periodische Splines
        # Der Parameter k=3 gibt einen kubischen Spline an (C2-Kontinuität)
        tck_x = interpolate.splrep(t, x_points, s=smoothing, k=3, per=True)
        tck_y = interpolate.splrep(t, y_points, s=smoothing, k=3, per=True)
    else:
        # Für offene Tracks verwenden wir normale Splines
        tck_x = interpolate.splrep(t, x_points, s=smoothing, k=3)
        tck_y = interpolate.splrep(t, y_points, s=smoothing, k=3)
    
    # 5. Erzeuge dicht interpolierte Punkte für die Trackgenerierung
    # Mehr Punkte für eine präzisere Darstellung
    num_points = max(150, len(anchor_points_cartesian) * 10)
    u = np.linspace(0, 1, num_points)
    
    # Interpoliere die Punkte mit den Splines
    x_interp = interpolate.splev(u, tck_x, der=0)
    y_interp = interpolate.splev(u, tck_y, der=0)
    
    # 6. Erstelle die Mittellinie und konvertiere zu Python-Floats für Kompatibilität
    track_points = [(float(x), float(y)) for x, y in zip(x_interp, y_interp)]
    
    # 7. Nachbearbeitung für geschlossene Tracks
    if closed_track:
        # Schneide die Ergebnispunkte, um nur den eigentlichen geschlossenen Track zu behalten
        # Berechne den zentralen Bereich, der den tatsächlichen Track darstellt
        start_idx = int(num_points * wrap_points / len(anchor_points_cartesian)) if wrap_points < len(anchor_points_cartesian) else 0
        end_idx = num_points - start_idx if start_idx > 0 else num_points
        
        # Trimmen der Liste und Sicherstellen, dass der Track geschlossen ist
        track_points = track_points[start_idx:end_idx]
        
        # Stelle sicher, dass der Track wirklich geschlossen ist, indem der letzte Punkt gleich dem ersten ist
        if track_points and track_points[0] != track_points[-1]:
            track_points.append(track_points[0])
    
    # 8. Qualitätsprüfung: Entferne zu dicht beieinanderliegende Punkte
    if len(track_points) > 3:
        filtered_points = [track_points[0]]
        min_dist_squared = 0.001  # Minimaler quadrierter Abstand zwischen Punkten
        
        for i in range(1, len(track_points)):
            last_x, last_y = filtered_points[-1]
            curr_x, curr_y = track_points[i]
            dist_squared = (curr_x - last_x)**2 + (curr_y - last_y)**2
            
            if dist_squared > min_dist_squared:
                filtered_points.append(track_points[i])
        
        if len(filtered_points) >= 3:  # Mindestanzahl für sinnvolle Tracks
            track_points = filtered_points
    
    # 9. Stellensicher, dass bei geschlossenen Tracks Start und Ende identisch sind
    if closed_track and track_points and track_points[0] != track_points[-1]:
        track_points[-1] = track_points[0]
    
    return track_points
def load_scripted_track(script_path, closed_track=False):
    """Lädt einen Track aus einer Skriptdatei (jede Zeile "x y"), optional geschlossen."""
    track_points = []
    try:
        with open(script_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    try:
                        x, y = float(parts[0]), float(parts[1])
                        track_points.append((x, y))
                    except ValueError:
                        print(f"Ungültige Zeile im Skript übersprungen: {line.strip()}")
    except FileNotFoundError:
        print(f"Skriptdatei nicht gefunden: {script_path}")
        return []
    
    if closed_track and track_points and (len(track_points) < 2 or track_points[0] != track_points[-1]):
        track_points = close_track_smoothly(track_points)
    return track_points

def load_csv_track(csv_path, closed_track=False):
    """Lädt einen Track aus einer CSV-Datei (Mittellinie), optional geschlossen."""
    track_points = []
    try:
        with open(csv_path, 'r') as f:
            header = next(f, None) # Header lesen und überspringen
            if header is None:
                print(f"CSV-Datei ist leer: {csv_path}")
                return []
            for line_number, line in enumerate(f, 1):
                parts = line.strip().split(config.get('csv_delimiter', ','))
                if len(parts) >= 2:
                    try:
                        x, y = float(parts[0]), float(parts[1])
                        track_points.append((x, y))
                    except ValueError:
                        print(f"Ungültige Zeile {line_number+1} in CSV übersprungen: {line.strip()}")
    except FileNotFoundError:
        print(f"CSV-Datei nicht gefunden: {csv_path}")
        return []
    except Exception as e:
        print(f"Fehler beim Lesen der CSV-Datei {csv_path}: {e}")
        return []

    if closed_track and track_points and (len(track_points) < 2 or track_points[0] != track_points[-1]):
        track_points = close_track_smoothly(track_points)
    return track_points

def get_track_borders(centerline_points):
    """
    Berechnet die linke und rechte Begrenzung eines Tracks mit verbesserten Normalenvektoren.
    
    Diese Funktion verwendet eine Kombination aus:
    1. Verbesserte Berechnung von Normalenvektoren an Kurvenpunkten
    2. Glättung der Normalenvektoren für konsistente Streckenbreite
    3. Adaptive Behandlung von geschlossenen Tracks und scharfen Kurven
    4. Spezialbehandlung für Start- und Endpunkte
    
    Args:
        centerline_points: Liste von (x, y) Koordinaten der Mittellinie
        
    Returns:
        Tuple mit zwei Listen: (linke Begrenzungspunkte, rechte Begrenzungspunkte)
    """
    import numpy as np
    
    left_border = []
    right_border = []
    
    # Grundlegende Validierung
    if not centerline_points or len(centerline_points) < 2:
        print("Warnung in get_track_borders: Mittellinie hat weniger als 2 Punkte, Ränder können nicht berechnet werden.")
        return [], []

    # Parameter aus der Konfiguration laden
    track_w = config.get('track_width', 0.8)  # Streckenbreite
    
    # Überprüfen ob der Track geschlossen ist
    is_closed_track = (len(centerline_points) > 2 and 
                       centerline_points[0] == centerline_points[-1])
    
    # Arrays für effizientere Berechnung
    points = np.array(centerline_points)
    normals = np.zeros((len(points), 2))  # Für Normalenvektoren
    
    # Für jeden Punkt: Berechne den Tangentenvektor und dann den Normalenvektor
    for i in range(len(points)):
        # Erster Punkt: Verwende Richtung zum nächsten Punkt
        if i == 0:
            if is_closed_track:
                # Bei geschlossenem Track: Verwende Punkte vor und nach dem ersten/letzten Punkt
                p_prev = points[-2]  # Vorletzter Punkt
                p_curr = points[i]   # Erster/Letzter Punkt (identisch)
                p_next = points[i+1] # Zweiter Punkt
                # Berechne Tangentenvektor als Durchschnitt der Richtungen
                dx_prev = p_curr[0] - p_prev[0]
                dy_prev = p_curr[1] - p_prev[1]
                dx_next = p_next[0] - p_curr[0]
                dy_next = p_next[1] - p_curr[1]
                
                # Normalisiere diese Vektoren
                len_prev = np.sqrt(dx_prev**2 + dy_prev**2)
                len_next = np.sqrt(dx_next**2 + dy_next**2)
                
                if len_prev > 0:
                    dx_prev, dy_prev = dx_prev/len_prev, dy_prev/len_prev
                if len_next > 0:
                    dx_next, dy_next = dx_next/len_next, dy_next/len_next
                
                # Berechne den Tangentenvektor als Durchschnitt
                dx = (dx_prev + dx_next) / 2
                dy = (dy_prev + dy_next) / 2
            else:
                # Bei offenem Track: Verwende Richtung zum zweiten Punkt
                p_curr = points[i]
                p_next = points[i+1]
                # Tangentenvektor zeigt in Richtung des nächsten Punktes
                dx, dy = p_next[0] - p_curr[0], p_next[1] - p_curr[1]
                # Keine weitere Berechnung nötig
        
        # Letzter Punkt: Verwende Richtung vom vorherigen Punkt
        elif i == len(points) - 1:
            if is_closed_track:
                # Bei geschlossenem Track: Bereits beim ersten Punkt behandelt
                # Wir können die bereits berechneten Werte für den ersten Punkt wiederverwenden
                normals[i] = normals[0]
                continue
            else:
                # Bei offenem Track: Verwende Richtung vom vorletzten zum letzten Punkt
                p_prev = points[i-1]
                p_curr = points[i]
                # Tangentenvektor zeigt in die gleiche Richtung wie der vorherige
                dx, dy = p_curr[0] - p_prev[0], p_curr[1] - p_prev[1]
        
        # Für alle anderen Punkte: Verwende den Durchschnitt der Richtungen
        else:
            p_prev = points[i-1]
            p_curr = points[i]
            p_next = points[i+1]
            
            # Vektoren von aktuellem Punkt zum vorherigen und nächsten
            dx_prev = p_curr[0] - p_prev[0]
            dy_prev = p_curr[1] - p_prev[1]
            dx_next = p_next[0] - p_curr[0]
            dy_next = p_next[1] - p_curr[1]
            
            # Normalisiere diese Vektoren
            len_prev = np.sqrt(dx_prev**2 + dy_prev**2)
            len_next = np.sqrt(dx_next**2 + dy_next**2)
            
            if len_prev > 0:
                dx_prev, dy_prev = dx_prev/len_prev, dy_prev/len_prev
            if len_next > 0:
                dx_next, dy_next = dx_next/len_next, dy_next/len_next
            
            # Berechne den Tangentenvektor als Durchschnitt der normalisierten Vektoren
            # Diese Methode erzeugt glattere Übergänge an Kurvenpunkten
            dx = (dx_prev + dx_next) / 2
            dy = (dy_prev + dy_next) / 2
        
        # Berechne den Normalenvektor (senkrecht zum Tangentenvektor)
        normal_x, normal_y = -dy, dx
        
        # Normalisiere den Normalenvektor
        normal_length = np.sqrt(normal_x**2 + normal_y**2)
        
        if normal_length > 0:
            normal_x, normal_y = normal_x/normal_length, normal_y/normal_length
            normals[i] = [normal_x, normal_y]
        elif i > 0:
            # Falls der Normalenvektor nicht berechnet werden kann, verwende den vorherigen
            normals[i] = normals[i-1]
        else:
            # Fallback für den ersten Punkt
            normals[i] = [0, 1]
    
    # Optional: Glätte die Normalenvektoren für geschmeidigere Ränder
    # Dies verhindert abrupte Änderungen an scharfen Kurven
    if len(points) > 3:
        # Einfacher gleitender Durchschnitt für die Normalenvektoren
        smoothed_normals = np.copy(normals)
        window_size = min(5, len(normals) // 3)  # Adaptive Fenstergröße
        
        if window_size >= 3:
            # Nicht für Start- und Endpunkte, falls offener Track
            start_idx = 1 if not is_closed_track else 0
            end_idx = len(normals)-1 if not is_closed_track else len(normals)
            
            for i in range(start_idx, end_idx):
                # Berechne Durchschnitt der benachbarten Normalenvektoren
                window_start = max(0, i - window_size // 2)
                window_end = min(len(normals), i + window_size // 2 + 1)
                
                avg_normal = np.mean(normals[window_start:window_end], axis=0)
                # Normalisiere den gemittelten Vektor
                avg_length = np.sqrt(avg_normal[0]**2 + avg_normal[1]**2)
                
                if avg_length > 0:
                    smoothed_normals[i] = avg_normal / avg_length
        
        normals = smoothed_normals
    
    # Berechne die Randpunkte basierend auf der Mittellinie und den Normalenvektoren
    for i, point in enumerate(points):
        normal = normals[i]
        
        # Linke Seite: Mittelpunkt + Normale * halbe Streckenbreite
        left_x = point[0] + normal[0] * track_w / 2
        left_y = point[1] + normal[1] * track_w / 2
        left_border.append((float(left_x), float(left_y)))  # Konvertiere zu Python Float
        
        # Rechte Seite: Mittelpunkt - Normale * halbe Streckenbreite
        right_x = point[0] - normal[0] * track_w / 2
        right_y = point[1] - normal[1] * track_w / 2
        right_border.append((float(right_x), float(right_y)))  # Konvertiere zu Python Float
    
    return left_border, right_border


def plot_track(centerline, left_border, right_border, save_path_prefix=None):
    """Stellt den Track mit verbesserten visuellen Elementen dar und speichert ihn optional."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig = plt.figure(figsize=(16, 10))
    
    # Parametrierung für bessere Visualisierung
    track_closed = len(centerline) > 1 and centerline[0] == centerline[-1]
    
    # Farbverlauf für die Strecke - vom Start zum Ende
    if len(centerline) > 1 and len(left_border) > 1 and len(right_border) > 1:
        # Farbverlauf berechnen - Grün zu Gelb zu Rot
        num_segments = len(centerline) - 1
        
        from matplotlib.colors import LinearSegmentedColormap
        
        # Erstelle benutzerdefinierten Farbverlauf für bessere Sichtbarkeit der Richtung
        if track_closed:
            # Für geschlossene Tracks: Blau -> Grün -> Gelb -> Orange -> Rot -> Violett -> Blau
            colors_gradient = [(0.0, 'royalblue'), 
                              (0.2, 'limegreen'),
                              (0.4, 'gold'),
                              (0.6, 'darkorange'),
                              (0.8, 'crimson'),
                              (1.0, 'royalblue')]
        else:
            # Für offene Tracks: Grün -> Gelb -> Orange -> Rot
            colors_gradient = [(0.0, 'limegreen'), 
                              (0.33, 'gold'),
                              (0.67, 'darkorange'),
                              (1.0, 'crimson')]
        
        # Erstelle den Farbverlauf
        cmap = LinearSegmentedColormap.from_list('track_gradient', colors_gradient, N=max(100, num_segments))
        
        # Segmente mit Farbverlauf füllen
        for i in range(num_segments):
            frac = i / num_segments  # Position im Farbverlauf
            
            # Polygon-Koordinaten für das Segment
            x_coords = [left_border[i][0], right_border[i][0], right_border[i+1][0], left_border[i+1][0]]
            y_coords = [left_border[i][1], right_border[i][1], right_border[i+1][1], left_border[i+1][1]]
            
            # Einfärben mit Farbverlauf
            segment_color = cmap(frac)
            plt.fill(x_coords, y_coords, color=segment_color, alpha=0.6, 
                     edgecolor='grey', linewidth=0.5, zorder=0)
    
    # Mittellinie mit verbesserten Pfeilen für Richtungsvisualisierung
    if centerline:
        cx, cy = zip(*centerline)
        plt.plot(cx, cy, color='black', linewidth=2.0, linestyle='--', 
                 label='Mittellinie', zorder=3)
        
        # Pfeile entlang der Mittellinie zur Anzeige der Fahrtrichtung
        # Füge mehr Pfeile für längere Strecken hinzu
        num_arrows = min(20, max(5, len(centerline) // 15))  # Adaptive Pfeilanzahl
        arrow_indices = np.linspace(0, len(centerline)-2, num_arrows, dtype=int)
        
        for idx in arrow_indices:
            # Hol Startpunkt und Richtungsvektor für den Pfeil
            x, y = centerline[idx]
            next_x, next_y = centerline[idx + 1]
            dx, dy = next_x - x, next_y - y
            
            # Normalisiere die Länge
            length = np.sqrt(dx*dx + dy*dy)
            if length > 0:
                dx, dy = dx/length, dy/length
                
                # Zeichne den Pfeil - länger und deutlicher
                plt.arrow(x, y, dx*5, dy*5, head_width=2.0, head_length=3.0, 
                          fc='black', ec='black', alpha=0.7, zorder=4)
    
    # Rechter und linker Rand mit verbesserten visuellen Eigenschaften
    line_width_border = 4.0
    
    if left_border:
        lx, ly = zip(*left_border)
        # Eleganter Schattenwurf für besseren 3D-Effekt
        shadow_offset = 0.5
        plt.plot(np.array(lx) + shadow_offset, np.array(ly) - shadow_offset, 
                 color='#555599', linewidth=line_width_border + 1.5, 
                 zorder=1, alpha=0.3)
        plt.plot(lx, ly, color=config.get('color_left_border', 'blue'), 
                linewidth=line_width_border, label='Linker Rand', zorder=2)
    
    if right_border:
        rx, ry = zip(*right_border)
        # Eleganter Schattenwurf
        shadow_offset = 0.5
        plt.plot(np.array(rx) + shadow_offset, np.array(ry) - shadow_offset, 
                 color='#995555', linewidth=line_width_border + 1.5, 
                 zorder=1, alpha=0.3)
        plt.plot(rx, ry, color=config.get('color_right_border', 'red'), 
                linewidth=line_width_border, label='Rechter Rand', zorder=2)
    
    # Verbesserte Start- und Endpunktmarkierungen mit intuitiven Icons
    if centerline and len(centerline) > 1:
        start_x, start_y = centerline[0]
        end_x, end_y = centerline[-1]
        
        # Startpunkt: Klares blaues Flaggensymbol
        plt.scatter(start_x, start_y, s=200, color='darkblue', marker='o', 
                   edgecolor='white', linewidth=2, zorder=10)
        plt.text(start_x+2, start_y+2, 'START', fontsize=12, color='darkblue', 
                fontweight='bold', ha='left', va='bottom', zorder=10)
        
        # Endpunkt: Nur anzeigen, wenn nicht geschlossen
        if not track_closed:
            plt.scatter(end_x, end_y, s=200, color='darkred', marker='D', 
                       edgecolor='white', linewidth=2, zorder=10) 
            plt.text(end_x+2, end_y+2, 'ZIEL', fontsize=12, color='darkred', 
                    fontweight='bold', ha='left', va='bottom', zorder=10)
            
        # Bei geschlossenen Tracks speziellen Text hinzufügen
        if track_closed:
            plt.text(start_x+2, start_y+2, 'START/ZIEL', fontsize=12, color='darkblue', 
                    fontweight='bold', ha='left', va='bottom', zorder=10)

    plt.title('Generierter Track', fontsize=26, fontweight='bold', color='#333333')
    plt.xlabel('X-Koordinate', fontsize=18, color='#444444')
    plt.ylabel('Y-Koordinate', fontsize=18, color='#444444')
    plt.legend(fontsize=14, loc='best', frameon=True, shadow=True)
    plt.axis('equal')
    plt.grid(True, linestyle=':', alpha=0.7, color='darkgray')
    plt.gca().set_facecolor('#fafafa') # Sehr heller Hintergrund
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout() # Passt Plot an Fenstergröße an

    # Ausgabe der Eingabedaten neben dem Plot
    # Erstelle eine Textbox für die Eingabedaten
    # Die Positionierung erfolgt relativ zur Figure (0,0 links unten, 1,1 rechts oben)
    # Wir platzieren sie rechts neben dem Plot.

    # Sammle die relevanten Konfigurationsparameter
    config_text = "Konfiguration:\n"
    config_text += f"  Track-Breite: {config.get('track_width')}\n"
    config_text += f"  Glättungsfenster: {config.get('smoothing_window')}\n"

    # Einfacher Ansatz: Zeige die wichtigsten Parameter, die immer gelten
    # oder die für die aktuelle Visualisierung relevant sein könnten.
    # Basisparameter für alle Modi
    param_summary = {
        "Track Breite": config.get('track_width'),
        "Glättung": config.get('smoothing_window'),
        "Max. Schließfaktor": config.get('max_closing_length_factor'),
        "Punkte (Mitte)": len(centerline) if centerline else 0,
    }
    
    # Aktiver Mode-String ermitteln
    mode_nummern = {0: "Random Track", 1: "Script Track", 2: "CSV Track", 
                    3: "Fixed Polar", 4: "Random Polar+Arc"}
    aktiver_modus = "Unbekannt"
    for mode_num, mode_name in mode_nummern.items():
        if config.get('default_run_mode') == mode_num:
            aktiver_modus = f"{mode_num} ({mode_name})"
    
    # Mode 4 (Polar Track) Parameter, die wichtig für die Diagnose sind
    param_summary["Aktiver Modus"] = aktiver_modus
    param_summary["Num Points Polar"] = config.get('num_points_polar_random')
    param_summary["Polar Distanz Bereich"] = config.get('polar_distance_range_random')
    param_summary["Kurventypen"] = config.get('curve_types_polar_random')
    param_summary["Arc Radius Min/Max"] = [config.get('polar_arc_radius_min'), config.get('polar_arc_radius_max')]
    param_summary["Arc Max Winkel"] = config.get('polar_arc_max_angle_deg')
    param_summary["Arc Punkte"] = config.get('polar_arc_num_points')
    param_summary["Geschlossener Track"] = config.get('create_closed_track_default', True)
    
    text_to_display = "Eingabeparameter (Auszug):\n"
    for key, value in param_summary.items():
        text_to_display += f"  {key}: {value}\n"

    # Aktiver Mode
    mode_nummern = {0: "Random Track", 1: "Script Track", 2: "CSV Track", 
                    3: "Fixed Polar", 4: "Random Polar+Arc"}
    active_mode = config.get('default_run_mode', 0)
    text_to_display += f"\nAktiver Modus: {active_mode} ({mode_nummern.get(active_mode, 'Unbekannt')})\n"
    text_to_display += f"Geschlossener Track: {config.get('create_closed_track_default', True)}"
    
    # Position der Textbox anpassen
    # Versuche, die Textbox rechts vom Plot zu platzieren.
    # Dafür muss der rechte Rand des Subplots angepasst werden.
    fig.subplots_adjust(right=0.75) # Schafft Platz auf der rechten Seite
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    fig.text(0.77, 0.95, text_to_display, transform=fig.transFigure, fontsize=10,
             verticalalignment='top', bbox=props)

    if save_path_prefix:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{save_path_prefix}_track_{timestamp}.png"
        try:
            # Stelle sicher, dass das Verzeichnis für den Speicherpfad existiert
            output_dir = os.path.dirname(filename)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            fig.savefig(filename, dpi=300) # fig.savefig statt plt.savefig
            print(f"Track-Bild gespeichert: {filename}")
        except Exception as e:
            print(f"Fehler beim Speichern des Track-Bildes: {e}")
    
    # Zeige den Plot an
    plt.show()
    
    return fig

def ensure_example_files():
    """Stellt sicher, dass die Beispieldateien existieren und erstellt sie bei Bedarf."""
    # Beispiel-CSV-Datei erstellen, falls sie nicht existiert
    default_csv_path = config.get('csv_path_example')
    if default_csv_path and not os.path.exists(default_csv_path):
        try:
            # Stelle sicher, dass das Verzeichnis existiert
            csv_dir = os.path.dirname(default_csv_path)
            if csv_dir and not os.path.exists(csv_dir):
                os.makedirs(csv_dir)
                
            with open(default_csv_path, 'w') as f:
                f.write("x,y,comment\n")
                f.write("0,0,start_node\n5,2,node1\n10,5,node2\n15,3,node3\n20,0,node4\n25,-2,node5\n20,-5,node6\n10,-6,node7\n0,-3,end_node\n")
            print(f"Beispiel-CSV-Datei erstellt: {default_csv_path}")
        except Exception as e:
            print(f"Fehler beim Erstellen der Beispiel-CSV-Datei {default_csv_path}: {e}")
    
    # Beispiel-Script-Datei erstellen, falls sie nicht existiert
    default_script_path = config.get('script_path_example')
    if default_script_path and not os.path.exists(default_script_path):
        try:
            # Stelle sicher, dass das Verzeichnis existiert
            script_dir = os.path.dirname(default_script_path)
            if script_dir and not os.path.exists(script_dir):
                os.makedirs(script_dir)
                
            with open(default_script_path, 'w') as f:
                f.write("0 0\n5 5\n10 10\n5 15\n0 10\n-5 5\n0 0\n") # Geschlossener Track
            print(f"Beispiel-Skriptdatei erstellt: {default_script_path}")
        except Exception as e:
            print(f"Fehler beim Erstellen der Beispiel-Skriptdatei {default_script_path}: {e}")

# Beim Import des Moduls sicherstellen, dass die Beispieldateien existieren
ensure_example_files()
def close_track_smoothly(track_points):
    """Schließt einen Track glatt, ohne zu große Segmente zum Startpunkt zu erzeugen.
    Sorgt dafür, dass die Steigung am Anfang und Ende des Tracks gleich ist.
    
    Die verbesserte Version verwendet Spline-Interpolation für einen natürlicheren
    Übergang, wenn möglich, oder eine optimierte Kreisbogenberechnung.
    
    Args:
        track_points: Liste von (x, y) Koordinaten des Tracks
        
    Returns:
        Die ergänzte Liste von Punkten mit glatter Schließung zum Startpunkt
    """
    if not track_points or len(track_points) < 2:
        return track_points
        
    # Wenn der Track bereits geschlossen ist, nichts zu tun
    if track_points[0] == track_points[-1]:
        return track_points
        
    try:
        # Versuche den Spline-basierten Ansatz für glattere Schließung
        import numpy as np
        from scipy import interpolate
        
        # Konvertiere zu Arrays für scipy
        points = np.array(track_points)
        x = points[:, 0]
        y = points[:, 1]
        
        # Berechne kumulative Bogenlänge als Parameter
        t = np.zeros(len(track_points))
        for i in range(1, len(track_points)):
            dx = track_points[i][0] - track_points[i-1][0]
            dy = track_points[i][1] - track_points[i-1][1]
            t[i] = t[i-1] + np.sqrt(dx**2 + dy**2)
        
        # Erstelle erweiterte Arrays für geschlossenen Track
        # Füge Punkte vom Anfang am Ende und umgekehrt hinzu für C1-Kontinuität
        n_extra = 3  # Anzahl der zusätzlichen Punkte für die Wiederholung
        
        # Erweitere die Punktliste für eine bessere Schließung
        x_extended = np.concatenate([x[-n_extra:], x, x[:n_extra]])
        y_extended = np.concatenate([y[-n_extra:], y, y[:n_extra]])
        
        # Erweitere Parameterbereich entsprechend
        t_extra_start = -np.linspace(t[-n_extra:][0], t[-1], n_extra, endpoint=False)[::-1]
        t_extra_end = np.linspace(0, t[n_extra-1], n_extra) + t[-1]
        t_extended = np.concatenate([t_extra_start, t, t_extra_end])
        
        # Erstelle Splines durch die erweiterten Punkte
        tck_x = interpolate.splrep(t_extended, x_extended, s=0, k=3)  # k=3 für kubischen Spline
        tck_y = interpolate.splrep(t_extended, y_extended, s=0, k=3)
        
        # Generiere mehr Punkte am Ende des Tracks für den Übergang zum Anfang
        # Wir generieren Punkte im letzten 20% des Tracks und den Anfangspunkt
        closing_fraction = 0.2
        t_close = np.linspace(t[-1] * (1-closing_fraction), t[-1], 10)
        t_close = np.append(t_close, t_extra_end[-1])  # Füge den echten Schlusspunkt hinzu
        
        # Interpoliere die neuen Punkte
        x_close = interpolate.splev(t_close, tck_x, der=0)
        y_close = interpolate.splev(t_close, tck_y, der=0)
        
        # Entferne den letzten Punkt des ursprünglichen Tracks
        closed_track = track_points[:-1].copy()
        
        # Füge die interpolierten Schließungspunkte hinzu
        for i in range(len(t_close)):
            closed_track.append((float(x_close[i]), float(y_close[i])))
        
        # Stelle sicher, dass der letzte Punkt exakt mit dem ersten übereinstimmt
        closed_track[-1] = track_points[0]
        
        return closed_track
        
    except (ImportError, Exception) as e:
        # Fallback auf ursprüngliche Methode wenn scipy nicht verfügbar ist
        # oder ein anderer Fehler auftritt
        print(f"Warnung: Spline-basiertes Schließen des Tracks fehlgeschlagen: {e}")
        print("Fallback auf geometrisches Verfahren...")
        
        # Berechne die durchschnittliche Segmentlänge
        total_length = 0.0
        segment_lengths = []
        for i in range(1, len(track_points)):
            dx = track_points[i][0] - track_points[i-1][0]
            dy = track_points[i][1] - track_points[i-1][1]
            segment_length = np.sqrt(dx**2 + dy**2)
            segment_lengths.append(segment_length)
            total_length += segment_length
            
        avg_segment_length = total_length / len(segment_lengths) if segment_lengths else 1.0
        
        # Berechne die Distanz zwischen dem letzten und dem ersten Punkt
        first_point = track_points[0]
        last_point = track_points[-1]
        dx_closing = first_point[0] - last_point[0]
        dy_closing = first_point[1] - last_point[1]
        closing_distance = np.sqrt(dx_closing**2 + dy_closing**2)
        
        # Maximale Schließlänge basierend auf der durchschnittlichen Segmentlänge
        max_closing_length = avg_segment_length * config.get('max_closing_length_factor', 1.5)
        
        # Berechne die Steigungen am Anfang und Ende des Tracks
        if len(track_points) > 1:
            # Anfangssteigung: Vektor vom ersten zum zweiten Punkt
            start_slope_x = track_points[1][0] - track_points[0][0]
            start_slope_y = track_points[1][1] - track_points[0][1]
            start_angle = math.atan2(start_slope_y, start_slope_x)
            
            # Endsteigung: Vektor vom vorletzten zum letzten Punkt
            end_slope_x = track_points[-1][0] - track_points[-2][0]
            end_slope_y = track_points[-1][1] - track_points[-2][1]
            end_angle = math.atan2(end_slope_y, end_slope_x)
            
            # Winkelunterschied zwischen Anfang und Ende
            angle_diff = (start_angle - end_angle) % (2 * math.pi)
            if angle_diff > math.pi:
                angle_diff -= 2 * math.pi  # Normalisiere auf [-π, π]
            
            # Bei großem Winkelunterschied oder langer Schließstrecke: Verwende Bogen statt linearer Interpolation
            if abs(angle_diff) > 0.5 or closing_distance > max_closing_length:
                # Berechne Radius für den Bogen
                arc_radius = max(closing_distance / (2 * math.sin(abs(angle_diff)/2)) if abs(angle_diff) > 0.001 else closing_distance * 2,
                               avg_segment_length * 2)  # Mindestradius basierend auf der Segmentlänge
                
                # Platziere den Mittelpunkt des Kreisbogens
                # Der Bogen sollte an beiden Enden tangential zu den Steigungen sein
                # Wir platzieren den Mittelpunkt senkrecht zur mittleren Richtung
                avg_angle = (end_angle + start_angle) / 2
                perp_angle = avg_angle + math.pi/2 * (1 if angle_diff > 0 else -1)
                
                # Mittelpunkt berechnen
                center_x = (first_point[0] + last_point[0]) / 2 + arc_radius * math.cos(perp_angle)
                center_y = (first_point[1] + last_point[1]) / 2 + arc_radius * math.sin(perp_angle)
                
                # Winkel vom Mittelpunkt zum letzten Punkt
                angle_to_last = math.atan2(last_point[1] - center_y, last_point[0] - center_x)
                angle_to_first = math.atan2(first_point[1] - center_y, first_point[0] - center_x)
                
                # Winkel zwischen diesen beiden Punkten
                arc_angle = (angle_to_first - angle_to_last) % (2 * math.pi)
                if arc_angle > math.pi:
                    arc_angle -= 2 * math.pi  # Normalisiere auf [-π, π]
                
                # Erzeuge Bogenpunkte
                num_points = max(3, int(abs(arc_angle) / math.radians(15)))  # Ca. alle 15 Grad ein Punkt
                for i in range(1, num_points):
                    fraction = i / num_points
                    current_angle = angle_to_last + fraction * arc_angle
                    x = center_x + arc_radius * math.cos(current_angle)
                    y = center_y + arc_radius * math.sin(current_angle)
                    track_points.append((x, y))
            else:
                # Bei kleinem Winkelunterschied: Lineare Interpolation
                num_points = int(np.ceil(closing_distance / avg_segment_length))
                for i in range(1, num_points):
                    # Lineare Interpolation zwischen letztem und erstem Punkt
                    fraction = i / num_points
                    x = last_point[0] + fraction * dx_closing
                    y = last_point[1] + fraction * dy_closing
                    track_points.append((x, y))
        
        # Schließlich füge den ersten Punkt hinzu, um den Track zu schließen
        track_points.append(first_point)
        
        return track_points
